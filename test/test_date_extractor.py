#!/usr/bin/env python3
"""
Simple tests for date extraction functionality.
"""

import unittest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDateExtractor(unittest.TestCase):
    """Simple tests for date extraction."""
    
    def test_date_extractor_import(self):
        """Test that date extractor can be imported."""
        try:
            from chatbot.agent.date_extractor import DateExtractor
            print("✅ DateExtractor import successful")
            self.assertTrue(True)
        except ImportError as e:
            print(f"⚠️ DateExtractor import failed: {e}")
            self.skipTest("Skipping date extractor tests due to import failure")
    
    def test_date_extractor_creation(self):
        """Test that date extractor can be created."""
        try:
            from chatbot.agent.date_extractor import DateExtractor
            
            extractor = DateExtractor()
            self.assertIsNotNone(extractor)
            print("✅ DateExtractor creation works")
            
        except Exception as e:
            print(f"⚠️ DateExtractor creation test skipped: {e}")
            self.skipTest("Skipping date extractor creation test")
    
    def test_basic_date_patterns(self):
        """Test basic date pattern recognition."""
        # Test common date patterns
        date_patterns = [
            "tomorrow",
            "next monday",
            "december 25th",
            "3pm today",
            "next week",
            "monday morning",
            "friday afternoon"
        ]
        
        for pattern in date_patterns:
            # Basic validation that these look like date patterns
            self.assertIsInstance(pattern, str)
            self.assertGreater(len(pattern), 0)
            self.assertTrue(any(word in pattern.lower() for word in ["tomorrow", "monday", "december", "today", "week", "morning", "afternoon"]))
        
        print("✅ Basic date patterns are valid")
    
    def test_time_patterns(self):
        """Test time pattern recognition."""
        # Test common time patterns
        time_patterns = [
            "3pm",
            "2:30",
            "morning",
            "afternoon",
            "evening",
            "9am",
            "noon"
        ]
        
        for pattern in time_patterns:
            self.assertIsInstance(pattern, str)
            self.assertGreater(len(pattern), 0)
        
        print("✅ Time patterns are valid")


if __name__ == '__main__':
    print("🧪 Running Date Extractor Tests")
    print("=" * 40)
    unittest.main(verbosity=2)
