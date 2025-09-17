#!/usr/bin/env python3
"""
Test script to verify the uninstall-all functionality fix.
This script simulates the API calls and verifies the behavior.
"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:3000/api/index"
TEST_CLIENT_ID = "test-client-123"

def test_api_endpoint(action, data=None):
    """Test an API endpoint"""
    payload = {"action": action}
    if data:
        payload.update(data)
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"\n--- Testing {action} ---")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', 'Unknown')}")
            if result.get('success'):
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

def main():
    """Run the tests"""
    print("Testing Uninstall-All Fix")
    print("=" * 50)
    
    # Test 1: Test connection
    test_api_endpoint("testConnection")
    
    # Test 2: Get active notifications (admin view - should exclude uninstall commands)
    print("\n--- Test 2: Admin view (should exclude uninstall commands) ---")
    test_api_endpoint("getNotifications")
    
    # Test 3: Get client notifications (client view - should include uninstall commands)
    print("\n--- Test 3: Client view (should include uninstall commands) ---")
    test_api_endpoint("getNotifications", {"clientId": TEST_CLIENT_ID})
    
    # Test 4: Trigger uninstall all clients (requires authentication)
    # This will likely fail without proper authentication, but we can see the endpoint response
    print("\n--- Test 4: Trigger uninstall all clients (expect auth error) ---")
    test_api_endpoint("uninstallAllClients", {"reason": "Test uninstall"})
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("1. API connection should work")
    print("2. Admin view should exclude uninstall commands")
    print("3. Client view should include uninstall commands (if any exist)")
    print("4. Uninstall endpoint should require authentication")
    print("\nIf these behave as expected, the fix is working!")

if __name__ == "__main__":
    main()
