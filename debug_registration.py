#!/usr/bin/env python3
"""
Debug script focused on device registration step
"""

import os
import sys
import platform
import subprocess
import json
import time
import uuid
import hashlib
from pathlib import Path
from datetime import datetime

# Install core dependencies
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests>=2.31.0'])
    import requests

# Global configuration
INSTALLER_VERSION = "3.0.0"
DEFAULT_API_URL = "https://push-notifications-phi.vercel.app"

class RegistrationDebugger:
    def __init__(self, api_url=None):
        self.system = platform.system()
        self.api_url = api_url or DEFAULT_API_URL
        self.mac_address = self._get_real_mac_address()
        self.username = self._get_username_with_number()
        self.client_name = f"{self.username}_{platform.node()}"
        
        print(f"Registration Debug Tool v{INSTALLER_VERSION}")
        print(f"Platform: {self.system}")
        print(f"MAC Address: {self.mac_address}")
        print(f"Username: {self.username}")
        print(f"Client Name: {self.client_name}")
        print(f"API URL: {self.api_url}")
        print()

    def _get_real_mac_address(self):
        """Get the real primary network interface MAC address using multiple methods"""
        mac_address = None
        detection_method = "unknown"
        
        try:
            if self.system == "Windows":
                # Try WMI first
                try:
                    import wmi
                    c = wmi.WMI()
                    for interface in c.Win32_NetworkAdapter():
                        if (interface.NetEnabled and 
                            interface.PhysicalAdapter and 
                            interface.MACAddress):
                            mac_address = interface.MACAddress.replace(':', '-').upper()
                            detection_method = "WMI"
                            break
                except:
                    pass
                
                # Fallback to uuid.getnode()
                if not mac_address:
                    try:
                        mac_num = uuid.getnode()
                        if mac_num != 0x010203040506:
                            mac_hex = ':'.join([f'{(mac_num >> i) & 0xff:02x}' for i in range(40, -8, -8)])
                            mac_address = mac_hex.replace(':', '-').upper()
                            detection_method = "uuid_getnode"
                    except:
                        pass
            
            # Final validation
            if mac_address and len(mac_address) == 17 and mac_address.count('-') == 5:
                print(f"MAC Address detected via {detection_method}: {mac_address}")
                return mac_address
                
        except Exception as e:
            print(f"MAC address detection error: {e}")
        
        # Emergency fallback
        print("Warning: Using emergency MAC fallback")
        system_id = f"{platform.node()}_{platform.machine()}_{os.environ.get('COMPUTERNAME', 'unknown')}"
        mac_hash = hashlib.sha256(system_id.encode()).hexdigest()[:12]
        mac_address = '-'.join([mac_hash[i:i+2].upper() for i in range(0, 12, 2)])
        return mac_address

    def _get_username_with_number(self):
        """Get username with number suffix for uniqueness"""
        import getpass
        import random
        base_username = getpass.getuser()
        number = random.randint(1000, 9999)
        return f"{base_username}_{number}"

    def test_registration_with_key(self, installation_key):
        """Test device registration with a specific installation key"""
        print(f"Testing Registration with Key: '{installation_key}'")
        print("=" * 60)
        
        # Use existing website API format for device registration
        device_info = {
            'action': 'registerClient',  # Using existing API action
            'installationKey': installation_key,
            'macAddress': self.mac_address,
            'username': self.username,
            'clientName': self.client_name,
            'hostname': platform.node(),
            'platform': f"{platform.system()} {platform.release()}",
            'version': INSTALLER_VERSION,
            'installPath': '', # Will be updated after directory creation
            'macDetectionMethod': 'debug',
            'installerMode': 'debug',
            'timestamp': datetime.now().isoformat(),
            # Additional security metadata
            'systemInfo': {
                'osVersion': f"{platform.system()} {platform.release()} {platform.version()}",
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'isAdmin': False,  # Debug mode, no admin check
                'timezone': str(datetime.now().astimezone().tzinfo)
            }
        }
        
        print("Registration payload:")
        # Debug: Show partial payload (without sensitive data)
        debug_info = {k: v for k, v in device_info.items() if k not in ['installationKey']}
        debug_info['installationKey'] = '***REDACTED***'
        print(json.dumps(debug_info, indent=2))
        
        print(f"\nMaking POST request to: {self.api_url}/api/index")
        print(f"Request timeout: 30 seconds")
        print(f"Request Content-Type: application/json")
        
        try:
            response = requests.post(
                f"{self.api_url}/api/index",
                json=device_info,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            print(f"✓ Request completed successfully")
        except requests.exceptions.ConnectTimeout as e:
            print(f"✗ Connection timeout: {e}")
            return False
        except requests.exceptions.ReadTimeout as e:
            print(f"✗ Read timeout: {e}")
            return False
        except Exception as e:
            print(f"✗ Request failed with exception: {type(e).__name__}: {e}")
            return False
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content length: {len(response.text)} characters")
        print(f"Response body (first 1500 chars): {response.text[:1500]}")
        if len(response.text) > 1500:
            print(f"Response body (last 300 chars): ...{response.text[-300:]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\nParsed response JSON:")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    print(f"\n✓ Device registered successfully!")
                    print(f"  Client ID: {result.get('clientId', 'Not provided')}")
                    print(f"  Key ID: {result.get('keyId', 'Not provided')}")
                    print(f"  New Installation: {result.get('isNewInstallation', 'Not specified')}")
                    print(f"  Server Message: {result.get('message', 'No message')}")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown registration error')
                    print(f"\n✗ Registration failed: {error_msg}")
                    
                    # Handle specific error cases
                    if 'duplicate' in error_msg.lower() or 'already registered' in error_msg.lower():
                        print("  → This MAC address is already registered.")
                        print("  → Previous installation may need to be uninstalled first.")
                    elif 'invalid key' in error_msg.lower():
                        print("  → Installation key is invalid or expired.")
                    elif 'database' in error_msg.lower() or 'server' in error_msg.lower():
                        print("  → Server-side database or configuration issue.")
                    
                    return False
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse JSON response: {e}")
                print("Raw response content:")
                print(repr(response.text))
                return False
        else:
            print(f"\n✗ Server error: HTTP {response.status_code}")
            try:
                error_detail = response.text[:500]
                print(f"  Server response: {error_detail}")
            except:
                pass
            return False

    def run_interactive_debug(self):
        """Run interactive debugging session"""
        print("Interactive Registration Debug Session")
        print("=" * 60)
        
        while True:
            print("\nOptions:")
            print("1. Test registration with manual key")
            print("2. Test registration with common keys") 
            print("3. Show current system info")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                key = input("Enter installation key: ").strip()
                if key:
                    success = self.test_registration_with_key(key)
                    if success:
                        print("\n🎉 Registration successful!")
                        break
                    else:
                        print("\n❌ Registration failed.")
                        retry = input("Try another key? (y/n): ").strip().lower()
                        if retry != 'y':
                            break
                else:
                    print("No key entered.")
                    
            elif choice == '2':
                test_keys = ["demo", "test", "admin", "install", "debug", "sample"]
                print("Testing common installation keys...")
                for key in test_keys:
                    print(f"\n--- Testing: {key} ---")
                    success = self.test_registration_with_key(key)
                    if success:
                        print(f"\n🎉 Registration successful with key: {key}")
                        break
                else:
                    print("\n❌ All test keys failed.")
                    
            elif choice == '3':
                print(f"\nCurrent System Information:")
                print(f"  Platform: {self.system}")
                print(f"  Hostname: {platform.node()}")
                print(f"  MAC Address: {self.mac_address}")
                print(f"  Username: {self.username}")
                print(f"  Client Name: {self.client_name}")
                print(f"  API URL: {self.api_url}")
                print(f"  Python: {sys.version}")
                
            elif choice == '4':
                print("Exiting debug session.")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    debugger = RegistrationDebugger()
    debugger.run_interactive_debug()
