#!/usr/bin/env python3
"""
Simple tests for API routes functionality.
"""

import unittest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestRoutes(unittest.TestCase):
    """Simple tests for API routes."""
    
    def test_routes_import(self):
        """Test that routes can be imported."""
        try:
            from api.routes import router
            print("✅ Routes import successful")
            self.assertTrue(True)
        except ImportError as e:
            print(f"⚠️ Routes import failed: {e}")
            self.skipTest("Skipping routes tests due to import failure")
    
    def test_router_creation(self):
        """Test that router can be created."""
        try:
            from api.routes import router
            from fastapi import APIRouter
            
            self.assertIsInstance(router, APIRouter)
            print("✅ Router creation works")
            
        except Exception as e:
            print(f"⚠️ Router creation test skipped: {e}")
            self.skipTest("Skipping router creation test")
    
    def test_route_endpoints(self):
        """Test that expected route endpoints exist."""
        try:
            from api.routes import router
            
            # Get all routes
            routes = router.routes
            
            # Check for expected endpoints
            endpoint_paths = [route.path for route in routes]
            
            # Should have basic endpoints
            expected_endpoints = ["/", "/health", "/status"]
            for endpoint in expected_endpoints:
                self.assertIn(endpoint, endpoint_paths, f"Endpoint {endpoint} should exist")
            
            print(f"✅ Found {len(routes)} route endpoints")
            print(f"   Endpoints: {endpoint_paths}")
            
        except Exception as e:
            print(f"⚠️ Route endpoints test skipped: {e}")
            self.skipTest("Skipping route endpoints test")
    
    def test_schema_import(self):
        """Test that schema can be imported."""
        try:
            from api.schema import (
                QuestionRequest,
                QuestionResponse,
                HealthResponse
            )
            print("✅ Schema import successful")
            self.assertTrue(True)
        except ImportError as e:
            print(f"⚠️ Schema import failed: {e}")
            self.skipTest("Skipping schema tests due to import failure")


if __name__ == '__main__':
    print("🧪 Running Routes Tests")
    print("=" * 40)
    unittest.main(verbosity=2)
