#!/usr/bin/env python3
"""
Debug version of PushNotifications installer with admin check bypassed
"""

import os
import sys
import platform
import subprocess
import json
import time
import uuid
import secrets
import hashlib
import shutil
import ctypes
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Install core dependencies with minimal system impact
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests>=2.31.0'])
    import requests

# Global configuration
INSTALLER_VERSION = "3.0.0"
DEFAULT_API_URL = "https://push-notifications-phi.vercel.app"

class DebugInstaller:
    def __init__(self, api_url=None):
        self.system = platform.system()
        self.api_url = api_url or DEFAULT_API_URL
        self.installation_key = None
        self.mac_address = self._get_real_mac_address()
        
        print(f"Debug Installer v{INSTALLER_VERSION}")
        print(f"Platform: {self.system}")
        print(f"MAC Address: {self.mac_address}")
        print(f"API URL: {self.api_url}")
        print()

    def _get_real_mac_address(self):
        """Get the real primary network interface MAC address"""
        try:
            import uuid
            mac_num = uuid.getnode()
            if mac_num != 0x010203040506:
                mac_hex = ':'.join([f'{(mac_num >> i) & 0xff:02x}' for i in range(40, -8, -8)])
                mac_address = mac_hex.replace(':', '-').upper()
                return mac_address
        except Exception as e:
            print(f"MAC detection failed: {e}")
        
        # Fallback
        return "00-FF-FF-FF-FF-FF"

    def validate_installation_key(self):
        """Validate installation key with website API"""
        print("Installation Key Validation")
        print("=" * 50)
        print(f"API URL: {self.api_url}")
        
        # Test different keys
        test_keys = ["test123", "demo", "admin", "install123", ""]
        
        for key in test_keys:
            print(f"\nTesting key: '{key}'")
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/index",
                    json={
                        'action': 'validateInstallationKey',
                        'installationKey': key
                    },
                    timeout=30
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Parsed JSON: {json.dumps(result, indent=2)}")
                    if result.get('success'):
                        self.installation_key = key
                        print("✓ Key validation succeeded")
                        return True
                    else:
                        print(f"✗ Key validation failed: {result.get('message')}")
                else:
                    print(f"✗ Server error: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Validation error: {e}")
        
        print("\n\nAll test keys failed. Let me try manual input...")
        
        # Try with user input
        key = input("Enter installation key (or press Enter to skip): ").strip()
        if key:
            print(f"Testing manually entered key...")
            try:
                response = requests.post(
                    f"{self.api_url}/api/index",
                    json={
                        'action': 'validateInstallationKey',
                        'installationKey': key
                    },
                    timeout=30
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Parsed JSON: {json.dumps(result, indent=2)}")
                    if result.get('success'):
                        self.installation_key = key
                        print("✓ Manual key validation succeeded")
                        return True
                    else:
                        print(f"✗ Manual key validation failed: {result.get('message')}")
                        
            except Exception as e:
                print(f"✗ Manual validation error: {e}")
        
        return False

    def register_device(self):
        """Register device with website API"""
        print("\nDevice Registration")
        print("=" * 50)
        
        device_info = {
            'action': 'registerClient',
            'installationKey': self.installation_key,
            'macAddress': self.mac_address,
            'username': 'debug_user',
            'clientName': 'debug_client',
            'hostname': platform.node(),
            'platform': f"{platform.system()} {platform.release()}",
            'version': INSTALLER_VERSION,
            'installPath': 'debug_path',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Registration payload:")
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
        print(f"Response body (first 1000 chars): {response.text[:1000]}")
        if len(response.text) > 1000:
            print(f"Response body (last 200 chars): ...{response.text[-200:]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\nParsed response JSON: {json.dumps(result, indent=2)}")
                
                if result.get('success'):
                    print(f"\n✓ Device registered successfully!")
                    return True
                else:
                    error_msg = result.get('message', 'Unknown registration error')
                    print(f"\n✗ Registration failed: {error_msg}")
                    return False
            except json.JSONDecodeError:
                print(f"\nFailed to parse JSON response")
                return False
        else:
            print(f"\n✗ Server error: HTTP {response.status_code}")
            return False

    def run_debug(self):
        """Run debug installation"""
        print("Starting Debug Installation")
        print("=" * 60)
        
        # Skip admin check for debugging
        print("Skipping admin privilege check for debugging")
        
        # Validate installation key
        if not self.validate_installation_key():
            print("✗ Key validation failed")
            return False
        
        # Register device
        if not self.register_device():
            print("✗ Device registration failed")
            return False
        
        print("\n✓ Debug installation completed successfully!")
        return True

if __name__ == "__main__":
    installer = DebugInstaller()
    success = installer.run_debug()
    
    print(f"\nDebug result: {'SUCCESS' if success else 'FAILED'}")
    input("Press Enter to exit...")
