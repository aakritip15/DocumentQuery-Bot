from typing import Dict, Optional, Tuple, List

from .validator import (
    validate_name,
    validate_email,
    validate_phone,
)
from ..agent.tool_agent import ToolAgent


class ConversationalForm:
    """Stateful conversational form for collecting booking/contact details.

    Fields collected in order:
    - name
    - phone
    - email
    - preferred_datetime (derived from user's phrasing; date/time optional)
    - notes (optional, free-form)

    Usage:
      form = ConversationalForm()
      prompt = form.start()
      reply, next_prompt = form.handle_input(user_text)
    """

    def __init__(self, tools: Optional[ToolAgent] = None) -> None:
        self.tools = tools or ToolAgent()
        self.required_fields_order: List[str] = [
            "name",
            "phone",
            "email",
            "preferred_datetime",
        ]
        self.optional_fields_order: List[str] = [
            "notes",
        ]
        self.collected: Dict[str, Optional[str]] = {
            "name": None,
            "phone": None,
            "email": None,
            "preferred_datetime": None,
            "notes": None,
        }
        self.current_field: Optional[str] = None

    def start(self) -> str:
        """Initialize the form and return the first prompt."""
        if self.current_field is None:
            self.current_field = self._next_incomplete_required_field()
        return self._prompt_for(self.current_field)

    def is_complete(self) -> bool:
        return self._next_incomplete_required_field() is None

    def get_data(self) -> Dict[str, Optional[str]]:
        return dict(self.collected)

    def reset(self) -> None:
        for key in self.collected.keys():
            self.collected[key] = None
        self.current_field = None

    def handle_input(self, user_text: str) -> Tuple[str, Optional[str]]:
        """Consume user's message and advance the form.

        Returns a tuple of (assistant_reply, next_prompt_or_None_if_done).
        """
        if self.current_field is None:
            self.current_field = self._next_incomplete_required_field()

        field = self.current_field
        if field is None:
            # Everything collected; optionally ask for notes
            if self.collected.get("notes") is None:
                self.current_field = "notes"
                return (
                    "Anything else you'd like us to note (optional)?",
                    None,
                )
            return (
                "Thanks! I have all the information needed.",
                None,
            )

        # Validate and store based on field
        valid, value_or_error = self._validate_and_normalize(field, user_text)
        if not valid:
            return (value_or_error, self._prompt_for(field))

        # Store the value
        self.collected[field] = value_or_error

        # Advance to next field
        self.current_field = self._next_incomplete_required_field()

        if self.current_field is None:
            # All required done; ask optional notes
            if self.collected.get("notes") is None:
                self.current_field = "notes"
                return (
                    "Great, I have your details. Any additional notes? (optional)",
                    None,
                )
            return (
                "All set!",
                None,
            )

        return (
            self._ack(field),
            self._prompt_for(self.current_field),
        )

    def _next_incomplete_required_field(self) -> Optional[str]:
        for field in self.required_fields_order:
            if not self.collected.get(field):
                return field
        return None

    def _prompt_for(self, field: Optional[str]) -> Optional[str]:
        if field is None:
            return None
        prompts = {
            "name": "Sure — what is your full name?",
            "phone": "What's the best phone number to reach you?",
            "email": "And your email address?",
            "preferred_datetime": (
                "When would you prefer the appointment?."
            ),
            "notes": "Any additional notes or preferences? (optional)",
        }
        return prompts.get(field, "Could you provide that information?")

    def _ack(self, field: str) -> str:
        messages = {
            "name": "Thanks!",
            "phone": "Got it.",
            "email": "Thanks.",
            "preferred_datetime": "Noted.",
            "notes": "Thanks for the details.",
        }
        return messages.get(field, "Thanks.")

    def _validate_and_normalize(self, field: str, user_text: str) -> Tuple[bool, str]:
        text = user_text.strip()

        if field == "name":
            ok, msg_or_value = self.tools.tool_validate_name(text)
            return (ok, msg_or_value)

        if field == "phone":
            ok, msg_or_value = self.tools.tool_validate_phone(text)
            return (ok, msg_or_value)

        if field == "email":
            ok, msg_or_value = self.tools.tool_validate_email(text)
            return (ok, msg_or_value)

        if field == "preferred_datetime":
            # Prefer normalized yyyy-mm-dd if user provided only a date; otherwise keep ISO datetime
            dt = self.tools.tool_extract_datetime_iso(text)
            if not dt:
                return (
                    False,
                    "I couldn't parse a date/time. Please try something like 'tomorrow 3pm' or 'next Monday 10:30'.",
                )
            ymd = self.tools.tool_extract_date_ymd(text)
            return (True, ymd or dt)

        if field == "notes":
            return (True, text)

        return (False, "Sorry, I didn't get that.")


