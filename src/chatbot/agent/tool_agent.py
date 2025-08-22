from __future__ import annotations

from typing import Optional, Tuple, List, Dict, Any

from ..form.validator import validate_name, validate_email, validate_phone
from .date_extractor import extract_datetime, extract_date_ymd
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
import os
import json
from datetime import datetime
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate


class ToolAgent:
    """Lightweight tool agent exposing validation and date parsing as callables.

    This is designed to be injectable into the conversational form. Later, this
    can be swapped with a full LangChain Agent and StructuredTool wrappers.
    """

    # Validation tools
    def tool_validate_name(self, text: str) -> Tuple[bool, str]:
        return validate_name(text)

    def tool_validate_email(self, text: str) -> Tuple[bool, str]:
        return validate_email(text)

    def tool_validate_phone(self, text: str) -> Tuple[bool, str]:
        return validate_phone(text)

    # Date/time tools
    def tool_extract_datetime_iso(self, text: str) -> Optional[str]:
        return extract_datetime(text)

    def tool_extract_date_ymd(self, text: str) -> Optional[str]:
        return extract_date_ymd(text)

    # Booking tool: persist appointment to a JSONL file; returns confirmation id
    class _BookingInput(BaseModel):
        name: str = Field(..., description="Person's full name")
        phone: str = Field(..., description="Validated phone number")
        email: str = Field(..., description="Validated email address")
        preferred_datetime: str = Field(..., description="Preferred date or datetime (ISO or YYYY-MM-DD)")
        notes: Optional[str] = Field(default=None, description="Optional additional notes")

    def tool_book_appointment(self, payload: Dict[str, Any]) -> str:
        # Ensure directory exists
        out_dir = os.path.join(os.getcwd(), "appointments")
        os.makedirs(out_dir, exist_ok=True)
        # Create confirmation id
        confirmation_id = datetime.utcnow().strftime("APPT-%Y%m%d-%H%M%S-%f")
        record = {
            "id": confirmation_id,
            "created_utc": datetime.utcnow().isoformat(),
            **payload,
        }
        # Append as JSONL
        out_path = os.path.join(out_dir, "bookings.jsonl")
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return confirmation_id

    # ---- LangChain StructuredTools wrappers ----
    class _TextInput(BaseModel):
        text: str = Field(..., description="User-provided text input to validate or parse")

    def get_langchain_tools(self) -> List[StructuredTool]:
        """Return LangChain StructuredTool list for use with an agent executor."""
        return [
            StructuredTool.from_function(
                name="validate_name",
                description="Validate and normalize a person's full name.",
                func=lambda text: self.tool_validate_name(text)[1] if self.tool_validate_name(text)[0] else "",
                args_schema=self._TextInput,
            ),
            StructuredTool.from_function(
                name="validate_email",
                description="Validate and normalize an email address.",
                func=lambda text: self.tool_validate_email(text)[1] if self.tool_validate_email(text)[0] else "",
                args_schema=self._TextInput,
            ),
            StructuredTool.from_function(
                name="validate_phone",
                description="Validate and normalize a phone number into international-like format.",
                func=lambda text: self.tool_validate_phone(text)[1] if self.tool_validate_phone(text)[0] else "",
                args_schema=self._TextInput,
            ),
            StructuredTool.from_function(
                name="extract_datetime_iso",
                description="Extract a date/time from natural language as ISO string.",
                func=lambda text: self.tool_extract_datetime_iso(text) or "",
                args_schema=self._TextInput,
            ),
            StructuredTool.from_function(
                name="extract_date_ymd",
                description="Extract a date from natural language in YYYY-MM-DD format.",
                func=lambda text: self.tool_extract_date_ymd(text) or "",
                args_schema=self._TextInput,
            ),
            StructuredTool.from_function(
                name="book_appointment",
                description=(
                    "Persist an appointment booking. Returns a confirmation id. "
                    "Input must include name, phone, email, preferred_datetime, and optional notes."
                ),
                func=lambda name, phone, email, preferred_datetime, notes=None: self.tool_book_appointment({
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "preferred_datetime": preferred_datetime,
                    "notes": notes,
                }),
                args_schema=self._BookingInput,
            ),
        ]

    def build_agent(self, llm) -> AgentExecutor:
        tools = self.get_langchain_tools()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an assistant that uses tools to validate inputs and book appointments."),
            ("human", "{input}"),
            ("placeholder", "agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)


