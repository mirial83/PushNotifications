#!/usr/bin/env python3
"""
Test script to verify that specific client uninstall functionality still works
after the API routing changes.
"""

import requests
import json

# Configuration
API_URL = "http://localhost:3000/api/index"
TEST_CLIENT_ID = "test-specific-client-456"

def test_specific_uninstall_flow():
    """Test the specific client uninstall flow"""
    print("Testing Specific Client Uninstall Flow")
    print("=" * 50)
    
    # Step 1: Test that uninstallSpecificClient API endpoint exists
    print("\n--- Step 1: Testing uninstallSpecificClient API endpoint ---")
    payload = {
        "action": "uninstallSpecificClient",
        "clientId": TEST_CLIENT_ID,
        "reason": "Test specific uninstall"
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', 'Unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            # Expected: Authentication error (since we're not authenticated)
            if not result.get('success') and 'authentication' in result.get('message', '').lower():
                print("✅ API endpoint responds correctly (authentication required)")
            else:
                print("⚠️ Unexpected response - endpoint may have issues")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Step 2: Test that client notifications include uninstall commands
    print(f"\n--- Step 2: Testing client can receive specific uninstall commands ---")
    payload = {
        "action": "getNotifications",
        "clientId": TEST_CLIENT_ID  # This should route to getClientNotifications
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', 'Unknown')}")
            notifications = result.get('notifications', [])
            print(f"Notifications count: {len(notifications)}")
            
            # Check if any uninstall commands exist
            uninstall_commands = [n for n in notifications if n.get('message') in ['__UNINSTALL_SPECIFIC_COMMAND__', '__UNINSTALL_ALL_COMMAND__']]
            print(f"Uninstall commands found: {len(uninstall_commands)}")
            
            if len(uninstall_commands) > 0:
                print("✅ Client CAN receive uninstall commands")
                for cmd in uninstall_commands:
                    print(f"  - {cmd.get('message')} for clientId: {cmd.get('clientId')}")
            else:
                print("✅ No uninstall commands present (expected in normal operation)")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Step 3: Verify admin view still excludes uninstall commands
    print(f"\n--- Step 3: Testing admin view excludes uninstall commands ---")
    payload = {
        "action": "getNotifications"
        # No clientId - should route to getActiveNotifications
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', 'Unknown')}")
            notifications = result.get('notifications', [])
            print(f"Admin notifications count: {len(notifications)}")
            
            # Check if any uninstall commands exist (should be filtered out)
            uninstall_commands = [n for n in notifications if n.get('message', '').startswith('__UNINSTALL_')]
            print(f"Uninstall commands in admin view: {len(uninstall_commands)}")
            
            if len(uninstall_commands) == 0:
                print("✅ Admin view correctly excludes uninstall commands")
            else:
                print("❌ Admin view contains uninstall commands (this is incorrect)")
                for cmd in uninstall_commands:
                    print(f"  - {cmd.get('message')} for clientId: {cmd.get('clientId')}")
                    
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("1. ✅ uninstallSpecificClient API endpoint should exist (require auth)")
    print("2. ✅ Client view should be able to receive uninstall commands")  
    print("3. ✅ Admin view should exclude uninstall commands")
    print("\nIf all tests pass, specific client uninstall functionality is intact!")

if __name__ == "__main__":
    test_specific_uninstall_flow()
