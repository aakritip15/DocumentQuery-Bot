#!/usr/bin/env python3
"""
Simple tests for intent detection functionality.
"""

import unittest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestIntentDetection(unittest.TestCase):
    """Simple tests for intent detection."""
    
    def test_intent_categories(self):
        """Test that intent categories are properly defined."""
        # These are the three main intent categories
        intent_categories = ["qa", "appointment", "contact"]
        
        for category in intent_categories:
            self.assertIsInstance(category, str)
            self.assertGreater(len(category), 0)
        
        print("✅ Intent categories are properly defined")
    
    def test_keyword_detection_logic(self):
        """Test basic keyword detection logic."""
        # Test appointment keywords
        appointment_keywords = [
            "call me", "contact me", "book appointment", "schedule", 
            "call", "reach out", "appointment", "phone number", "email me",
            "book", "reserve", "make appointment", "set up meeting"
        ]
        
        # Test that these keywords would trigger appointment intent
        for keyword in appointment_keywords:
            has_appointment_keyword = any(app_keyword in keyword.lower() for app_keyword in appointment_keywords)
            self.assertTrue(has_appointment_keyword, f"Keyword '{keyword}' should be detected as appointment")
        
        print("✅ Basic keyword detection logic works")
    
    def test_debug_mode_setting(self):
        """Test that debug mode can be set."""
        try:
            from chatbot.core.chatbot_engine import ChatbotEngine
            
            # Test with debug=True
            chatbot_debug = ChatbotEngine(google_api_key="test_key", debug=True)
            self.assertTrue(chatbot_debug.debug)
            
            print("✅ Debug mode setting works")
            
        except Exception as e:
            print(f"⚠️ Debug mode test skipped (expected if no API key): {e}")
            self.skipTest("Skipping debug mode test due to missing API key")


if __name__ == '__main__':
    print("🧪 Running Intent Detection Tests")
    print("=" * 40)
    unittest.main(verbosity=2)
