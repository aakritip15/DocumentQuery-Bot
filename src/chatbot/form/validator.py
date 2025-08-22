import re
from typing import Tuple


def validate_name(text: str) -> Tuple[bool, str]:
    cleaned = " ".join(part.capitalize() for part in text.split())
    if len(cleaned) < 2:
        return False, "Please provide your full name."
    return True, cleaned


def validate_email(text: str) -> Tuple[bool, str]:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, text):
        return False, "That doesn't look like a valid email. Could you recheck it?"
    return True, text.lower()


def validate_phone(text: str) -> Tuple[bool, str]:
    digits = re.sub(r"\D", "", text)
    if len(digits) < 10:
        return False, "Please provide a valid phone number with at least 10 digits."
    # Basic formatting: +<country?> <area?> <rest>
    formatted = digits
    if len(digits) == 10:
        formatted = f"+1 {digits[0:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) > 10:
        formatted = f"+{digits[:-10]} {digits[-10:-7]}-{digits[-7:-4]}-{digits[-4:]}"
    return True, formatted


