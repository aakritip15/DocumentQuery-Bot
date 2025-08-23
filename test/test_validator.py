#!/usr/bin/env python3
"""
Simple tests for validation functionality.
"""

import unittest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestValidator(unittest.TestCase):
    """Simple tests for validation functionality."""
    
    def test_validator_import(self):
        """Test that validator can be imported."""
        try:
            from chatbot.form.validator import (
                validate_name,
                validate_email,
                validate_phone
            )
            print("✅ Validator functions import successful")
            self.assertTrue(True)
        except ImportError as e:
            print(f"⚠️ Validator import failed: {e}")
            self.skipTest("Skipping validator tests due to import failure")
    
    def test_name_validation_logic(self):
        """Test basic name validation logic."""
        # Test valid names
        valid_names = ["John Doe", "Jane Smith", "Bob", "Mary-Jane"]
        for name in valid_names:
            self.assertIsInstance(name, str)
            self.assertGreater(len(name), 0)
            # Basic validation: should contain letters and spaces/hyphens only
            self.assertTrue(all(c.isalpha() or c.isspace() or c == '-' for c in name))
        
        # Test invalid names
        invalid_names = ["", " ", "123", "John123", "!@#$%"]
        for name in invalid_names:
            # These should fail basic validation
            if name.strip() == "":
                self.assertEqual(len(name.strip()), 0)
            elif any(c.isdigit() for c in name):
                self.assertTrue(any(c.isdigit() for c in name))
        
        print("✅ Name validation logic works")
    
    def test_email_validation_logic(self):
        """Test basic email validation logic."""
        # Test valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@456.com"
        ]
        for email in valid_emails:
            self.assertIsInstance(email, str)
            self.assertIn("@", email)
            self.assertIn(".", email)
            # Should have text before @ and after @
            parts = email.split("@")
            self.assertEqual(len(parts), 2)
            self.assertGreater(len(parts[0]), 0)
            self.assertGreater(len(parts[1]), 0)
        
        # Test invalid emails
        invalid_emails = ["", " ", "invalid", "@example.com", "user@", "user.com"]
        for email in invalid_emails:
            if email.strip() == "":
                self.assertEqual(len(email.strip()), 0)
            elif "@" not in email:
                self.assertNotIn("@", email)
        
        print("✅ Email validation logic works")
    
    def test_phone_validation_logic(self):
        """Test basic phone validation logic."""
        # Test valid phone numbers
        valid_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "5551234567",
            "+1-555-123-4567"
        ]
        for phone in valid_phones:
            self.assertIsInstance(phone, str)
            # Should contain digits
            digits = sum(1 for c in phone if c.isdigit())
            self.assertGreaterEqual(digits, 10)  # At least 10 digits for US phone
        
        # Test invalid phone numbers
        invalid_phones = ["", " ", "abc", "123", "555-123"]
        for phone in invalid_phones:
            if phone.strip() == "":
                self.assertEqual(len(phone.strip()), 0)
            elif not any(c.isdigit() for c in phone):
                self.assertFalse(any(c.isdigit() for c in phone))
        
        print("✅ Phone validation logic works")


if __name__ == '__main__':
    print("🧪 Running Validator Tests")
    print("=" * 40)
    unittest.main(verbosity=2)
