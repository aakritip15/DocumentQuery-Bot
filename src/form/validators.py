import re
from typing import Tuple, Optional


class InputValidator:
    """Validates user input for forms."""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate name input."""
        if not name or not name.strip():
            return False, "Name cannot be empty"
        
        name = name.strip()
        
        # Check if name contains only letters, spaces, and common punctuation
        if not re.match(r"^[a-zA-Z\s\.\-']+$", name):
            return False, "Name can only contain letters, spaces, dots, hyphens, and apostrophes"
        
        # Check length
        if len(name) < 2:
            return False, "Name must be at least 2 characters long"
        
        if len(name) > 50:
            return False, "Name must be less than 50 characters"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email input."""
        if not email or not email.strip():
            return False, "Email cannot be empty"
        
        email = email.strip().lower()
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Please enter a valid email address"
        
        # Check length
        if len(email) > 254:
            return False, "Email address is too long"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number input."""
        if not phone or not phone.strip():
            return False, "Phone number cannot be empty"
        
        phone = phone.strip()
        
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        
        # Check if contains only digits after cleaning
        if not clean_phone.isdigit():
            return False, "Phone number can only contain digits and common separators (-, (), +, .)"
        
        # Check length (international format)
        if len(clean_phone) < 7:
            return False, "Phone number is too short"
        
        if len(clean_phone) > 15:
            return False, "Phone number is too long"
        
        # Check for valid patterns (basic validation)
        # Allow formats like: +1234567890, 123-456-7890, (123) 456-7890, etc.
        valid_patterns = [
            r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$',  # US format
            r'^\+?\d{7,15}$',  # International format
        ]
        
        # At least one pattern should match the clean phone
        if not any(re.match(pattern, clean_phone) for pattern in valid_patterns):
            return False, "Please enter a valid phone number"
        
        return True, None
    
    @staticmethod
    def validate_all_fields(name: str, email: str, phone: str) -> Tuple[bool, dict]:
        """Validate all fields and return results."""
        results = {
            "name": {"valid": True, "error": None},
            "email": {"valid": True, "error": None},
            "phone": {"valid": True, "error": None}
        }
        
        all_valid = True
        
        # Validate name
        name_valid, name_error = InputValidator.validate_name(name)
        results["name"] = {"valid": name_valid, "error": name_error}
        if not name_valid:
            all_valid = False
        
        # Validate email
        email_valid, email_error = InputValidator.validate_email(email)
        results["email"] = {"valid": email_valid, "error": email_error}
        if not email_valid:
            all_valid = False
        
        # Validate phone
        phone_valid, phone_error = InputValidator.validate_phone(phone)
        results["phone"] = {"valid": phone_valid, "error": phone_error}
        if not phone_valid:
            all_valid = False
        
        return all_valid, results
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number for display."""
        # Remove all non-digit characters
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Format based on length
        if len(clean_phone) == 10:
            return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
        elif len(clean_phone) == 11 and clean_phone[0] == '1':
            return f"+1 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:]}"
        else:
            return phone  # Return original if can't format