#!/usr/bin/env python3
"""
PushNotifications Registration Test Script
Tests the client registration API call with detailed error reporting
"""

import os
import sys
import json
import platform
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess

# Add requests if not available
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

# Configuration
DEFAULT_API_URL = "https://push-notifications-phi.vercel.app"
INSTALLER_VERSION = "3.0.0"

class RegistrationTester:
    def __init__(self, api_url=None):
        self.api_url = api_url or DEFAULT_API_URL
        self.mac_address = self._get_mac_address()
        self.username = self._get_username()
        self.client_name = f"{self.username}_{platform.node()}"
        
    def _get_mac_address(self):
        """Get MAC address for testing"""
        try:
            mac_num = uuid.getnode()
            mac_hex = ':'.join([f'{(mac_num >> i) & 0xff:02x}' for i in range(40, -8, -8)])
            return mac_hex.replace(':', '-').upper()
        except:
            return "00-FF-FF-FF-FF-FF"
    
    def _get_username(self):
        """Get username for testing"""
        import getpass
        import random
        base_username = getpass.getuser()
        number = random.randint(1000, 9999)
        return f"{base_username}_{number}"
    
    def test_api_connectivity(self):
        """Test basic API connectivity"""
        print("Testing API connectivity...")
        print(f"API URL: {self.api_url}")
        
        try:
            # Test basic connectivity
            response = requests.get(self.api_url, timeout=10)
            print(f"✓ API is reachable (HTTP {response.status_code})")
            return True
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Connection failed: {e}")
            return False
        except requests.exceptions.Timeout:
            print("✗ Connection timed out")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False
    
    def test_installation_key_validation(self):
        """Test installation key validation"""
        print("\nTesting installation key validation...")
        
        # Prompt for installation key
        installation_key = input("Enter installation key for testing: ").strip()
        if not installation_key:
            print("No installation key provided, skipping validation test")
            return None
        
        try:
            response = requests.post(
                f"{self.api_url}/api/index",
                json={
                    'action': 'validateInstallationKey',
                    'installationKey': installation_key
                },
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get('success'):
                        print("✓ Installation key is valid")
                        return installation_key
                    else:
                        print(f"✗ Installation key validation failed: {result.get('message')}")
                        return None
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response: {response.text[:200]}")
                    return None
            else:
                print(f"✗ HTTP error {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"✗ Validation error: {e}")
            return None
    
    def test_client_registration(self, installation_key):
        """Test client registration with detailed logging"""
        if not installation_key:
            print("\nSkipping registration test - no valid installation key")
            return False
            
        print("\nTesting client registration...")
        print(f"MAC Address: {self.mac_address}")
        print(f"Username: {self.username}")
        print(f"Client Name: {self.client_name}")
        
        # Prepare registration data
        device_info = {
            'action': 'registerClient',
            'installationKey': installation_key,
            'macAddress': self.mac_address,
            'username': self.username,
            'clientName': self.client_name,
            'hostname': platform.node(),
            'platform': f"{platform.system()} {platform.release()}",
            'version': INSTALLER_VERSION,
            'installPath': '',  # Empty for testing
            'macDetectionMethod': 'uuid_getnode',
            'installerMode': 'advanced',
            'timestamp': datetime.now().isoformat(),
            'systemInfo': {
                'osVersion': f"{platform.system()} {platform.release()} {platform.version()}",
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'isAdmin': False,  # For testing
                'timezone': str(datetime.now().astimezone().tzinfo)
            }
        }
        
        print(f"\nRegistration payload:")
        print(json.dumps(device_info, indent=2))
        
        try:
            response = requests.post(
                f"{self.api_url}/api/index",
                json=device_info,
                timeout=30
            )
            
            print(f"\nResponse status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get('success'):
                        print("✓ Client registered successfully!")
                        print(f"  Client ID: {result.get('clientId')}")
                        print(f"  Key ID: {result.get('keyId')}")
                        print(f"  Is New Installation: {result.get('isNewInstallation')}")
                        return True
                    else:
                        error_msg = result.get('message', 'Unknown registration error')
                        print(f"✗ Registration failed: {error_msg}")
                        
                        # Additional error analysis
                        if 'duplicate' in error_msg.lower():
                            print("  → This MAC address might already be registered")
                        elif 'invalid key' in error_msg.lower():
                            print("  → Installation key might be invalid or expired")
                        elif 'missing' in error_msg.lower():
                            print("  → Some required fields might be missing")
                        
                        return False
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response: {response.text[:500]}")
                    return False
            else:
                print(f"✗ HTTP error {response.status_code}")
                print(f"Response body: {response.text[:500]}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Connection error: {e}")
            return False
        except requests.exceptions.Timeout:
            print("✗ Request timed out")
            return False
        except Exception as e:
            print(f"✗ Registration error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_report_installation(self, installation_key):
        """Test installation reporting"""
        if not installation_key:
            print("\nSkipping installation report test - no valid installation key")
            return False
            
        print("\nTesting installation report...")
        
        # Generate dummy data for testing
        dummy_key_id = f"key_{self.mac_address}_{int(datetime.now().timestamp())}"
        dummy_install_path = "C:\\ProgramData\\SystemResources\\test\\test"
        
        try:
            response = requests.post(
                f"{self.api_url}/api/index",
                json={
                    'action': 'reportInstallation',
                    'keyId': dummy_key_id,
                    'macAddress': self.mac_address,
                    'installPath': dummy_install_path,
                    'version': INSTALLER_VERSION,
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                },
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get('success'):
                        print("✓ Installation reported successfully")
                        return True
                    else:
                        print(f"✗ Installation report failed: {result.get('message')}")
                        return False
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response: {response.text[:200]}")
                    return False
            else:
                print(f"✗ HTTP error {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"✗ Report error: {e}")
            return False
    
    def run_full_test(self):
        """Run complete registration test suite"""
        print("PushNotifications Registration Test Suite")
        print("=" * 50)
        
        # Test 1: API Connectivity
        if not self.test_api_connectivity():
            print("⚠️  API connectivity failed - cannot proceed with other tests")
            return False
        
        # Test 2: Installation Key Validation
        installation_key = self.test_installation_key_validation()
        
        # Test 3: Client Registration
        registration_success = self.test_client_registration(installation_key)
        
        # Test 4: Installation Reporting
        report_success = self.test_report_installation(installation_key)
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        print(f"✓ API Connectivity: {'PASS' if True else 'FAIL'}")
        print(f"{'✓' if installation_key else '✗'} Installation Key: {'VALID' if installation_key else 'INVALID/SKIPPED'}")
        print(f"{'✓' if registration_success else '✗'} Client Registration: {'PASS' if registration_success else 'FAIL'}")
        print(f"{'✓' if report_success else '✗'} Installation Report: {'PASS' if report_success else 'FAIL'}")
        
        overall_success = installation_key and registration_success and report_success
        print(f"\nOverall Result: {'SUCCESS' if overall_success else 'FAILURE'}")
        
        if not overall_success:
            print("\n⚠️  TROUBLESHOOTING SUGGESTIONS:")
            if not installation_key:
                print("- Verify you have a valid installation key")
                print("- Check if the installation key has expired")
            if not registration_success:
                print("- Check if the MAC address is already registered")
                print("- Verify the API endpoint is working correctly")
                print("- Check server logs for detailed error information")
            if not report_success:
                print("- Verify the reportInstallation API endpoint is implemented")
        
        return overall_success

def main():
    """Main entry point"""
    try:
        # Allow custom API URL
        api_url = None
        if len(sys.argv) > 1:
            api_url = sys.argv[1]
        
        tester = RegistrationTester(api_url)
        success = tester.run_full_test()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests passed! Registration should work in the installer.")
        else:
            print("❌ Some tests failed. Please check the issues above.")
        
        input("\nPress Enter to exit...")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
