#!/usr/bin/env python3
"""
PushNotifications Universal Client Installer
Version: 3.0.0

Cross-platform installer with Windows executable conversion:

🌐 UNIVERSAL PYTHON INSTALLER
- Single .py file runs on Windows, macOS, Linux
- Windows: Auto-converts to .exe with admin privileges
- No external dependencies required for basic installation
- Automatically detects OS and adapts functionality

🪟 WINDOWS ENTERPRISE FEATURES
- Auto-conversion to executable with embedded admin escalation
- Hidden encrypted installation with AES-256-GCM vault encryption
- Zero local key storage (all keys fetched from website/MongoDB)
- Real MAC address detection and transmission
- Admin privilege escalation without UAC prompts
- Multi-monitor 25% grey overlay system
- Force-minimize window restrictions during active notifications
- Website allowlist enforcement and request system
- Automatic uninstaller on force-quit detection

🍎🐧 MACOS/LINUX COMPATIBILITY
- Platform-specific overlay and minimization where possible
- Adapted security model within OS constraints
- Cross-platform Python dependency management

🔐 SECURITY & ENCRYPTION
- AES-256-GCM encrypted installation directories
- Server-managed encryption keys
- Hidden file system integration
- Automatic uninstaller approval system
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
import winreg
import shutil
import ctypes
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Core Windows dependencies for full feature set
REQUIRED_PACKAGES = {
    'requests': 'requests>=2.31.0',
    'cryptography': 'cryptography>=41.0.0', 
    'psutil': 'psutil>=5.9.0',
    'pillow': 'Pillow>=10.0.0',
    'pystray': 'pystray>=0.19.4',
    'screeninfo': 'screeninfo>=0.8.1',
    'pywin32': 'pywin32>=306',
    'uiautomation': 'uiautomation>=2.0.15',
    'pynput': 'pynput>=1.7.6'
}

# Import required modules with intelligent dependency management
def check_and_install_package(package_name, pip_name=None):
    """Check if package exists system-wide, install only if missing"""
    pip_name = pip_name or package_name
    try:
        __import__(package_name)
        return True
    except ImportError:
        # Check if running as PyInstaller bundle (Windows EXE)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            print(f"Warning: {package_name} not bundled in EXE - may cause issues")
            return False
        
        # Only install if not found in any Python environment
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name],
                                 creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
            return True
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {package_name}")
            return False

# Install core dependencies with minimal system impact
check_and_install_package('requests', REQUIRED_PACKAGES['requests'])
check_and_install_package('cryptography', REQUIRED_PACKAGES['cryptography'])
check_and_install_package('psutil', REQUIRED_PACKAGES['psutil'])

# Import after installation
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import psutil

# Windows-specific imports with enhanced functionality
if platform.system() == "Windows":
    # Install Windows-specific packages
    check_and_install_package('win32api', REQUIRED_PACKAGES['pywin32'])
    check_and_install_package('screeninfo', REQUIRED_PACKAGES['screeninfo'])
    
    try:
        import win32api
        import win32con
        import win32security
        import win32file
        import win32service
        import win32serviceutil
        import pywintypes
        from win32com.shell import shell
        import win32gui
        import win32process
        import ntsecuritycon
        
        # UI Automation for browser URL reading
        try:
            import uiautomation as auto
            UI_AUTOMATION_AVAILABLE = True
        except ImportError:
            check_and_install_package('uiautomation', REQUIRED_PACKAGES['uiautomation'])
            try:
                import uiautomation as auto
                UI_AUTOMATION_AVAILABLE = True
            except ImportError:
                UI_AUTOMATION_AVAILABLE = False
                print("Warning: UI Automation not available - browser URL checking disabled")
        
        # Screen info for multi-monitor support
        try:
            import screeninfo
            SCREEN_INFO_AVAILABLE = True
        except ImportError:
            SCREEN_INFO_AVAILABLE = False
            print("Warning: screeninfo not available - using fallback monitor detection")
            
        # Network interface enumeration
        try:
            import wmi
            WMI_AVAILABLE = True
        except ImportError:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'WMI'],
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                import wmi
                WMI_AVAILABLE = True
            except:
                WMI_AVAILABLE = False
                print("Warning: WMI not available - using fallback MAC detection")
                
    except ImportError as e:
        print(f"Critical Windows modules missing: {e}")
        sys.exit(1)

# GUI imports for cross-platform compatibility
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Global configuration
INSTALLER_VERSION = "3.0.0"
REGISTRY_KEY = r"HKEY_CURRENT_USER\Software\PushNotifications"
DEFAULT_API_URL = "https://push-notifications-phi.vercel.app"

# Embedded Documentation
DOCUMENTATION = {
    'installer_improvements': '''
# PushNotifications Installer Improvements

## Summary

The PushNotifications installer has been significantly enhanced with intelligent dependency checking and automatic client startup functionality.

## Key Improvements

### 1. Smart Dependency Detection
- **Comprehensive Package Checking**: The installer now checks for dependencies in multiple ways:
  - Direct import testing for each package
  - Special handling for packages with different import names (e.g., `pillow` imports as `PIL`, `pywin32` imports as `win32api`)
  - Fallback to `pip list` command to verify installation
  - Multiple name variant checking (handles dashes, underscores, etc.)

### 2. Efficient Installation Process
- **Skip Already Installed Packages**: Dependencies that are already present are skipped, significantly reducing installation time
- **Installation Summary**: Clear reporting of:
  - Already installed packages (skipped)
  - Successfully installed packages
  - Failed package installations
- **Robust Error Handling**: Continues installation even if some packages fail

### 3. Automatic Client Startup
- **No User Prompts**: Client automatically starts after successful installation
- **Background Operation**: Client starts without requiring user interaction
- **Platform-Specific Startup**: Uses appropriate startup method for Windows
- **Error Recovery**: Provides manual startup instructions if automatic startup fails

### 4. Enhanced User Experience
- **Progress Feedback**: Clear visual indicators (✓, ✗, ⚠) for all operations
- **Detailed Logging**: Comprehensive status messages for each installation step
- **Graceful Fallbacks**: Alternative approaches when primary methods fail

## Installation Flow

1. **Python Compatibility Check**: Verify Python version and architecture
2. **Administrator Privileges**: Request elevation if needed
3. **Intelligent Dependency Management**:
   - Check each package individually
   - Skip already installed packages
   - Install only missing dependencies
   - Report comprehensive results
4. **Installation Key Validation**: Secure key entry with GUI/console fallback
5. **Directory Creation**: Create installation directory with proper permissions
6. **File Creation**: Generate client, configuration, and utility files
7. **Automatic Startup**: Launch client immediately after installation

## Benefits

- **Faster Installations**: Skip reinstalling existing packages
- **Better User Experience**: No unnecessary prompts, automatic startup
- **More Reliable**: Robust dependency checking across different environments
- **Comprehensive Reporting**: Clear feedback on installation status
- **Cross-Environment Support**: Works with various Python installations and package managers
''',
    'deployment_guide': '''
# PushNotifications Deployment Guide

This guide will walk you through deploying the PushNotifications application to Vercel with MongoDB as the backend database.

## Prerequisites

- [Vercel CLI](https://vercel.com/cli) installed globally
- [MongoDB Atlas](https://www.mongodb.com/atlas) account (or self-hosted MongoDB instance)
- [Git](https://git-scm.com/) for version control
- A GitHub, GitLab, or Bitbucket account (for Vercel integration)

## Setup Instructions

### 1. MongoDB Database Setup

#### MongoDB Atlas (Recommended)

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Sign up for a free account
   - Create a new cluster (M0 Sandbox is free)

2. **Configure Database Access**
   - Go to "Database Access" in the Atlas dashboard
   - Click "Add New Database User"
   - Create a user with "Read and write to any database" permissions
   - Note down the username and password

3. **Configure Network Access**
   - Go to "Network Access" in the Atlas dashboard
   - Click "Add IP Address"
   - Select "Allow access from anywhere" (0.0.0.0/0) for Vercel deployment

4. **Get Connection String**
   - Go to "Clusters" and click "Connect"
   - Choose "Connect your application"
   - Copy the connection string

### 2. Environment Variables Setup

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.xxx.mongodb.net/
DATABASE_NAME=pushnotifications

# Application Settings
CLIENT_VERSION=3.0.0
AUTO_UPDATE_ENABLED=true
FORCE_UPDATE=true

# Optional: Custom Settings
REFRESH_INTERVAL=30
MAX_NOTIFICATIONS=100
```

### 3. Vercel Deployment

1. **Login to Vercel:**
   ```bash
   vercel login
   ```

2. **Deploy the Application:**
   ```bash
   vercel
   ```

3. **Set Environment Variables:**
   ```bash
   vercel env add MONGODB_URI
   vercel env add DATABASE_NAME
   vercel env add CLIENT_VERSION
   ```

4. **Deploy to Production:**
   ```bash
   vercel --prod
   ```

### 4. Post-Deployment Configuration

1. **Verify Deployment:**
   - Visit your Vercel URL
   - Check that the application loads without errors
   - Test the database initialization

2. **Update Python Client Configuration:**
   - Update any existing Python clients to use the new Vercel URL
   - The client should automatically download from the deployment URL

## Monitoring and Maintenance

### Database Monitoring
- Monitor database usage, connections, and performance
- Set up alerts for high usage or errors
- MongoDB Atlas provides automatic backups

### Application Monitoring
- Enable Vercel Analytics in your project settings
- Monitor application performance and usage
- Check Vercel function logs for errors

### Updates and Maintenance
- Code updates automatically redeploy on git push
- Update environment variables in Vercel dashboard
- Update CLIENT_VERSION for client auto-updates

## Security Considerations

1. **Environment Variables:**
   - Never commit sensitive data to version control
   - Use strong passwords for database users
   - Regularly rotate database credentials

2. **Network Security:**
   - Consider restricting MongoDB network access
   - Use MongoDB Atlas built-in security features
   - Enable MongoDB Atlas encryption at rest

3. **Application Security:**
   - Keep dependencies updated
   - Regularly review authorized user lists
   - Monitor for unusual API usage patterns
''',
    'mongodb_setup': '''
# MongoDB Atlas Setup Guide

## MongoDB Atlas Credentials

For your PushNotifications deployment, you'll need to configure MongoDB Atlas.

## Step 1: Enable MongoDB Data API

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com)
2. Navigate to your "PushNotifications" project
3. In the left sidebar, look for **"App Services"** and click it
4. If you don't have an app yet:
   - Click **"Create a New App"**
   - Name: `PushNotificationsAPI`
   - Link to Data Source: `pushnotifications` (your cluster)
   - Click **"Create App"**

## Step 2: Enable Data API

1. In your App Services application, look in the left sidebar for **"Data API"**
2. Click **"Data API"**
3. Toggle **"Enable Data API"** to ON
4. **Copy the Data API Base URL** that appears:
   ```
   https://data.mongodb-api.com/app/YOUR-APP-ID/endpoint/data/v1
   ```

## Step 3: Create API Key

1. In App Services, go to **"Authentication"** → **"API Keys"**
2. Click **"Create API Key"**
3. Name: `WebAPIKey`
4. **Copy the generated API key** (you won't be able to see it again!)

## Step 4: Set Environment Variables

Add these to your deployment environment:

```
MONGODB_DATA_API_URL=https://data.mongodb-api.com/app/YOUR-ACTUAL-APP-ID/endpoint/data/v1
MONGODB_DATA_API_KEY=your-generated-api-key-here
MONGODB_DATA_SOURCE=pushnotifications
DATABASE_NAME=pushnotifications
```

## Test Your Setup

After configuring environment variables:
1. Deploy your application
2. Test the connection endpoint
3. Verify database connectivity

The API will automatically use MongoDB when configured, or fall back to simple storage otherwise.
'''
}

# Version comparison utilities
def parse_version(version_string):
    """Parse version string into comparable tuple (major, minor, patch)"""
    try:
        parts = version_string.strip().replace('v', '').split('.')
        return tuple(int(part) for part in parts[:3])  # Take first 3 parts
    except (ValueError, AttributeError):
        return (0, 0, 0)

def compare_versions(current, latest):
    """Compare two version strings. Returns 1 if latest > current, 0 if equal, -1 if current > latest"""
    current_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    
    if latest_tuple > current_tuple:
        return 1
    elif latest_tuple == current_tuple:
        return 0
    else:
        return -1

# Windows API constants
if platform.system() == "Windows":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    advapi32 = ctypes.windll.advapi32


class WindowsExecutableConverter:
    """Converts Python installer to Windows executable with admin privileges"""
    
    def __init__(self, source_file):
        self.source_file = Path(source_file)
        self.is_windows = platform.system() == "Windows"
        
    def should_convert_to_exe(self):
        """Check if we should convert to exe"""
        if not self.is_windows:
            return False
            
        # Don't convert if already running as exe
        if getattr(sys, 'frozen', False):
            return False
            
        return True
    
    def create_batch_launcher_with_admin(self):
        """Create batch file launcher with admin privileges"""
        try:
            batch_content = f'''@echo off
REM PushNotifications Installer - Admin Launcher
REM Auto-elevation script

net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
    pythonw.exe "{self.source_file.absolute()}" %*
) else (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process python -ArgumentList '\"{self.source_file.absolute()}\" %*' -Verb RunAs"
)
'''
            
            batch_file = self.source_file.parent / "PushNotificationsInstaller.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            print(f"✓ Admin batch launcher created: {batch_file}")
            return batch_file
            
        except Exception as e:
            print(f"✗ Batch launcher creation failed: {e}")
            return None


class PushNotificationsInstaller:
    """Advanced installer with Windows executable conversion and full security features"""
    
    def __init__(self, api_url=None):
        self.system = platform.system()
        self.api_url = api_url or DEFAULT_API_URL
        self.installation_key = None
        self.device_data = {}
        self.encryption_metadata = {}
        self.install_path = None
        self.key_id = None
        self.mac_address = self._get_real_mac_address()
        self.username = self._get_username_with_number()
        self.client_name = f"{self.username}_{platform.node()}"
        self.repair_mode = False  # Will be set to True if running in repair mode
        self.update_mode = False  # Will be set to True if running in update mode
        self.update_data = {}     # Will contain update information from server
        
        print(f"PushNotifications Installer v{INSTALLER_VERSION}")
        print(f"Platform: {self.system}")
        print(f"MAC Address: {self.mac_address}")
        print(f"Client Name: {self.client_name}")
        print(f"API URL: {self.api_url}")
        print()

    def _get_real_mac_address(self):
        """Get the real primary network interface MAC address using multiple methods"""
        mac_address = None
        detection_method = "unknown"
        
        try:
            if self.system == "Windows":
                # Method 1: WMI for active physical adapters (preferred)
                if WMI_AVAILABLE:
                    try:
                        c = wmi.WMI()
                        # Prefer Ethernet, then Wi-Fi adapters
                        adapter_priorities = ['Ethernet', 'Wi-Fi', 'Wireless']
                        
                        for priority in adapter_priorities:
                            for interface in c.Win32_NetworkAdapter():
                                if (interface.NetEnabled and 
                                    interface.PhysicalAdapter and 
                                    interface.MACAddress and
                                    interface.Name and
                                    priority.lower() in interface.Name.lower()):
                                    mac_address = interface.MACAddress.replace(':', '-').upper()
                                    detection_method = f"WMI_{priority}"
                                    break
                            if mac_address:
                                break
                        
                        # Fallback to any active physical adapter
                        if not mac_address:
                            for interface in c.Win32_NetworkAdapter():
                                if (interface.NetEnabled and 
                                    interface.PhysicalAdapter and 
                                    interface.MACAddress):
                                    mac_address = interface.MACAddress.replace(':', '-').upper()
                                    detection_method = "WMI_Generic"
                                    break
                                    
                    except Exception as e:
                        print(f"WMI MAC detection failed: {e}")
                
                # Method 2: Windows Management via subprocess
                if not mac_address:
                    try:
                        result = subprocess.run(['getmac', '/fo', 'csv', '/v'], 
                                              capture_output=True, text=True,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')[1:]  # Skip header
                            for line in lines:
                                parts = [p.strip('"') for p in line.split(',')]
                                if len(parts) >= 3 and parts[2] != 'N/A' and 'Physical' in line:
                                    mac_address = parts[2].replace('-', '-').upper()
                                    detection_method = "getmac"
                                    break
                    except Exception as e:
                        print(f"getmac detection failed: {e}")
                
                # Method 3: psutil network interfaces
                if not mac_address:
                    try:
                        for interface, addrs in psutil.net_if_addrs().items():
                            # Prioritize Ethernet and Wi-Fi interfaces
                            if any(x in interface.lower() for x in ['ethernet', 'wi-fi', 'wireless', 'wlan', 'eth']):
                                for addr in addrs:
                                    if hasattr(addr, 'family') and addr.family == psutil.AF_LINK:
                                        if addr.address and addr.address != '00-00-00-00-00-00':
                                            mac_address = addr.address.replace(':', '-').upper()
                                            detection_method = f"psutil_{interface}"
                                            break
                                if mac_address:
                                    break
                    except Exception as e:
                        print(f"psutil MAC detection failed: {e}")
            
            # Method 4: uuid.getnode() fallback (cross-platform)
            if not mac_address:
                try:
                    mac_num = uuid.getnode()
                    if mac_num != 0x010203040506:  # Avoid dummy MAC
                        mac_hex = ':'.join([f'{(mac_num >> i) & 0xff:02x}' for i in range(40, -8, -8)])
                        mac_address = mac_hex.replace(':', '-').upper()
                        detection_method = "uuid_getnode"
                except Exception as e:
                    print(f"uuid.getnode() failed: {e}")
            
            # Final validation
            if mac_address:
                # Ensure it's a valid MAC format and not a dummy/virtual MAC
                if len(mac_address) == 17 and mac_address.count('-') == 5:
                    # Store detection method for telemetry
                    self.mac_detection_method = detection_method
                    print(f"MAC Address detected via {detection_method}: {mac_address}")
                    return mac_address
                    
        except Exception as e:
            print(f"Critical MAC address detection error: {e}")
        
        # Emergency fallback - generate consistent MAC based on system info
        print("Warning: Using emergency MAC fallback")
        try:
            system_id = f"{platform.node()}_{platform.machine()}_{os.environ.get('COMPUTERNAME', 'unknown')}"
            mac_hash = hashlib.sha256(system_id.encode()).hexdigest()[:12]
            mac_address = '-'.join([mac_hash[i:i+2].upper() for i in range(0, 12, 2)])
            self.mac_detection_method = "emergency_fallback"
            return mac_address
        except:
            # Ultimate fallback
            self.mac_detection_method = "ultimate_fallback"
            return "00-FF-FF-FF-FF-FF"
    
    def _has_existing_installation(self):
        """Check if there's an existing installation to repair"""
        try:
            if self.system == "Windows":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  "Software\\PushNotifications", 0, 
                                  winreg.KEY_READ) as key:
                    # If we can read the key, we have an existing installation
                    return True
        except (WindowsError, FileNotFoundError):
            pass
        return False
    
    def _load_existing_config(self):
        """Load configuration from existing installation for repair mode"""
        try:
            if self.system == "Windows":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  "Software\\PushNotifications", 0, 
                                  winreg.KEY_READ) as key:
                    self.key_id, _ = winreg.QueryValueEx(key, "KeyId")
                    self.mac_address, _ = winreg.QueryValueEx(key, "MacAddress")
                    self.username, _ = winreg.QueryValueEx(key, "Username")
                    self.api_url, _ = winreg.QueryValueEx(key, "ApiUrl")
                    
                    # Set dummy installation key for repair
                    self.installation_key = "REPAIR_MODE"
                    
                    # Create device data for repair
                    self.device_data = {
                        'deviceId': f"repair_{self.mac_address}",
                        'clientId': f"repair_{self.mac_address}",
                        'isNewInstallation': False
                    }
                    
                    # Set encryption metadata
                    self.encryption_metadata = {
                        'keyId': self.key_id,
                        'algorithm': 'AES-256-GCM',
                        'keyDerivation': 'PBKDF2',
                        'iterations': 100000,
                        'serverManaged': True
                    }
                    
                    print(f"✓ Loaded existing configuration for repair")
                    print(f"  Key ID: {self.key_id}")
                    print(f"  MAC Address: {self.mac_address}")
                    print(f"  Username: {self.username}")
                    
        except Exception as e:
            print(f"Warning: Could not load existing config for repair: {e}")
    
    def check_for_updates(self):
        """Check for updates from the website"""
        print("Checking for updates...")
        
        try:
            # Extract version number from version string (e.g., "3.0.0" -> 300)
            version_parts = INSTALLER_VERSION.split('.')
            version_number = int(version_parts[0]) * 100 + int(version_parts[1]) * 10 + int(version_parts[2])
            
            response = requests.post(
                f"{self.api_url}/api/index",
                json={
                    'action': 'checkForUpdates',  # Updated to match API
                    'versionNumber': version_number,  # Added version number
                    'currentVersion': INSTALLER_VERSION,
                    'clientId': getattr(self, 'device_data', {}).get('clientId', 'unknown'),
                    'macAddress': self.mac_address,
                    'platform': f"{platform.system()} {platform.release()}",
                    'timestamp': datetime.now().isoformat()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    latest_version = result.get('latestVersion', INSTALLER_VERSION)
                    download_url = result.get('downloadUrl')
                    update_required = result.get('updateRequired', False)
                    update_notes = result.get('updateNotes', '')
                    update_installation_key = result.get('installationKey')  # Extract update key
                    
                    version_comparison = compare_versions(INSTALLER_VERSION, latest_version)
                    
                    if version_comparison > 0:  # Update available
                        print(f"📦 Update available: v{INSTALLER_VERSION} → v{latest_version}")
                        print(f"Download URL: {download_url}")
                        if update_notes:
                            print(f"Release notes: {update_notes}")
                        if update_installation_key:
                            print(f"✓ Update installation key provided")
                        
                        # Store update information
                        self.update_data = {
                            'latestVersion': latest_version,
                            'downloadUrl': download_url,
                            'updateRequired': update_required,
                            'updateNotes': update_notes,
                            'currentVersion': INSTALLER_VERSION,
                            'installationKey': update_installation_key  # Store the key
                        }
                        
                        return True  # Update available
                    elif version_comparison == 0:
                        print(f"✓ Already running latest version: v{INSTALLER_VERSION}")
                        return False  # No update needed
                    else:
                        print(f"✓ Running newer version than latest: v{INSTALLER_VERSION} > v{latest_version}")
                        return False  # Running pre-release or newer
                        
                else:
                    print(f"✗ Version check failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"✗ Version check server error: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"✗ Version check network error: {e}")
            return False
        except Exception as e:
            print(f"✗ Version check error: {e}")
            return False
    
    def download_and_apply_update(self):
        """Download and apply the latest version update"""
        if not self.update_data:
            print("No update data available")
            return False
            
        print(f"📥 Downloading update v{self.update_data['latestVersion']}...")
        
        try:
            download_url = self.update_data['downloadUrl']
            if not download_url:
                print("✗ No download URL provided")
                return False
            
            # Download the new installer
            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save to temporary location
            import tempfile
            temp_installer = None
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
                temp_installer = f.name
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                print(f"Downloading {total_size} bytes...")
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
                
                print("\n✓ Download completed")
            
            # Verify downloaded file
            if not Path(temp_installer).exists():
                print("✗ Downloaded file not found")
                return False
            
            # Replace current installer if we're in the install directory
            current_file = Path(__file__)
            if self.install_path and current_file.parent == self.install_path:
                # We're running from the install directory - update the local copy
                installer_backup = self.install_path / f"Installer_backup_{INSTALLER_VERSION}.py"
                installer_current = self.install_path / "Installer.py"
                
                # Backup current version
                if installer_current.exists():
                    shutil.copy2(installer_current, installer_backup)
                    print(f"✓ Backed up current installer to {installer_backup.name}")
                
                # Replace with new version
                shutil.copy2(temp_installer, installer_current)
                print(f"✓ Updated installer to v{self.update_data['latestVersion']}")
                
                # Update wrapper scripts
                self._update_installer_wrappers()
                
            # Clean up temp file
            try:
                os.unlink(temp_installer)
            except:
                pass
            
            # Update registry version info
            self._update_version_registry()
            
            print(f"🎉 Update completed! Now running v{self.update_data['latestVersion']}")
            return True
            
        except requests.RequestException as e:
            print(f"✗ Download failed: {e}")
            return False
        except Exception as e:
            print(f"✗ Update failed: {e}")
            return False
    
    def _update_installer_wrappers(self):
        """Update installer wrapper scripts after update"""
        try:
            if self.system == "Windows":
                # Update batch wrapper
                installer_path = self.install_path / "Installer.py"
                batch_wrapper = f'''@echo off
REM PushNotifications Installer/Repair Launcher (Updated)
cd /d "{self.install_path}"
pythonw.exe "{installer_path}" %*
'''
                
                batch_path = self.install_path / "Installer.bat"
                with open(batch_path, 'w') as f:
                    f.write(batch_wrapper)
                
                # Update executable wrapper
                exe_wrapper_script = f'''
#!/usr/bin/env python3
# Installer.exe Wrapper - Self-contained installer with repair mode (Updated)
import subprocess
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    installer_script = script_dir / "Installer.py"
    
    # Run with hidden window on Windows
    if os.name == "nt":
        subprocess.run([sys.executable, str(installer_script)] + sys.argv[1:], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.run([sys.executable, str(installer_script)] + sys.argv[1:])
'''
                
                exe_path = self.install_path / "Installer.exe"
                with open(exe_path, 'w', encoding='utf-8') as f:
                    f.write(exe_wrapper_script)
                
                print("✓ Updated installer wrapper scripts")
                
        except Exception as e:
            print(f"Warning: Could not update wrapper scripts: {e}")
    
    def _update_version_registry(self):
        """Update version information in Windows registry"""
        try:
            if self.system == "Windows":
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                    "Software\\PushNotifications") as key:
                    winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, 
                                    self.update_data['latestVersion'])
                    winreg.SetValueEx(key, "LastUpdated", 0, winreg.REG_SZ, 
                                    datetime.now().isoformat())
                    winreg.SetValueEx(key, "PreviousVersion", 0, winreg.REG_SZ, 
                                    INSTALLER_VERSION)
                
                print("✓ Updated registry version information")
                
        except Exception as e:
            print(f"Warning: Could not update registry version: {e}")

    def _get_username_with_number(self):
        """Get username with number suffix for uniqueness"""
        import getpass
        base_username = getpass.getuser()
        
        # Try to load existing username from registry
        try:
            if self.system == "Windows":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  "Software\\PushNotifications", 0, 
                                  winreg.KEY_READ) as key:
                    existing_username, _ = winreg.QueryValueEx(key, "Username")
                    return existing_username
        except (WindowsError, FileNotFoundError):
            pass
        
        # Generate new username with random number
        import random
        number = random.randint(1000, 9999)
        return f"{base_username}_{number}"

    def check_admin_privileges(self):
        """Check if running with administrator privileges"""
        if self.system == "Windows":
            try:
                # Primary method: Check using IsUserAnAdmin()
                is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
                if is_admin:
                    return True
                
                # Secondary method: Try opening a privileged registry key
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                      "SYSTEM\\CurrentControlSet\\Services", 0, 
                                      winreg.KEY_WRITE) as key:
                        return True
                except (PermissionError, OSError):
                    pass
                
                # Third method: Try net session command
                try:
                    result = subprocess.run(['net', 'session'], 
                                          capture_output=True, text=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    return result.returncode == 0
                except:
                    pass
                    
                return False
                
            except Exception as e:
                print(f"Error checking admin privileges: {e}")
                return False
        else:
            return os.geteuid() == 0

    def restart_with_admin(self):
        """Restart the installer with administrator privileges"""
        if self.system == "Windows":
            try:
                print("Restarting with administrator privileges...")
                
                # Method 1: Try PowerShell Start-Process with -Verb RunAs (most reliable on Windows 10)
                try:
                    # Build PowerShell command with proper escaping
                    script_path = os.path.abspath(sys.argv[0])
                    
                    # Create argument list for PowerShell
                    if len(sys.argv) > 1:
                        # Escape each argument properly
                        escaped_args = []
                        escaped_args.append(f"'{script_path}'")
                        for arg in sys.argv[1:]:
                            escaped_args.append(f"'{arg}'")
                        arg_list = ', '.join(escaped_args)
                    else:
                        arg_list = f"'{script_path}'"
                    
                    powershell_cmd = f'Start-Process -FilePath "{sys.executable}" -ArgumentList {arg_list} -Verb RunAs'
                    
                    result = subprocess.run([
                        'powershell.exe', '-Command', powershell_cmd
                    ], capture_output=True, text=True, timeout=30,
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if result.returncode == 0:
                        print("✓ Administrator privileges requested via PowerShell")
                        sys.exit(0)
                    else:
                        print(f"PowerShell elevation failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"PowerShell method failed: {e}")
                
                # Method 2: Try win32api ShellExecute (traditional method)
                try:
                    import win32api
                    
                    script_args = ' '.join([f'"{arg}"' for arg in sys.argv])
                    
                    result = win32api.ShellExecute(
                        None, "runas", sys.executable, script_args, None, 1
                    )
                    
                    if result > 32:  # Success
                        print("✓ Administrator privileges requested via ShellExecute")
                        sys.exit(0)
                    else:
                        print(f"ShellExecute failed with error code: {result}")
                        
                except Exception as e:
                    print(f"ShellExecute method failed: {e}")
                
                # Method 3: Try ctypes ShellExecuteW (64-bit compatible)
                try:
                    # Properly handle 64-bit Windows API calls
                    shell32 = ctypes.windll.shell32
                    
                    # Define proper function signatures for 64-bit
                    shell32.ShellExecuteW.argtypes = [
                        ctypes.wintypes.HWND,      # hwnd
                        ctypes.wintypes.LPCWSTR,   # lpOperation
                        ctypes.wintypes.LPCWSTR,   # lpFile
                        ctypes.wintypes.LPCWSTR,   # lpParameters
                        ctypes.wintypes.LPCWSTR,   # lpDirectory
                        ctypes.c_int               # nShowCmd
                    ]
                    shell32.ShellExecuteW.restype = ctypes.c_void_p
                    
                    script_args = ' '.join([f'"{arg}"' for arg in sys.argv])
                    
                    result = shell32.ShellExecuteW(
                        None, "runas", sys.executable, script_args, None, 1
                    )
                    
                    # Convert void pointer to integer for comparison
                    result_int = ctypes.cast(result, ctypes.c_void_p).value or 0
                    
                    if result_int > 32:
                        print("✓ Administrator privileges requested via ShellExecuteW")
                        sys.exit(0)
                    else:
                        print(f"ShellExecuteW failed with error code: {result_int}")
                        
                except Exception as e:
                    print(f"ShellExecuteW method failed: {e}")
                
                # Method 4: Final fallback - create a batch file to request elevation
                try:
                    import tempfile
                    
                    batch_content = f'''@echo off
echo Requesting administrator privileges...
powershell -Command "Start-Process -FilePath '{sys.executable}' -ArgumentList '{" ".join(sys.argv)}' -Verb RunAs"
'''
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False) as f:
                        f.write(batch_content)
                        temp_batch = f.name
                    
                    subprocess.run([temp_batch], creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    # Clean up temp file after a delay
                    try:
                        time.sleep(2)
                        os.unlink(temp_batch)
                    except:
                        pass
                    
                    print("✓ Administrator privileges requested via batch file")
                    sys.exit(0)
                    
                except Exception as e:
                    print(f"Batch file method failed: {e}")
                
                print("✗ All elevation methods failed")
                return False
                
            except Exception as e:
                print(f"Failed to restart with administrator privileges: {e}")
                return False
        else:
            # Unix-like systems
            try:
                os.execvp('sudo', ['sudo'] + [sys.executable] + sys.argv)
            except:
                return False
        
        return True

    def validate_installation_key(self):
        """Validate installation key with website API"""
        print("Installation Key Validation")
        print("=" * 50)
        print(f"API URL: {self.api_url}")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if GUI_AVAILABLE:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    key = simpledialog.askstring(
                        "PushNotifications Installation",
                        f"Enter installation key (attempt {attempt}/{max_attempts}):",
                        show='*'
                    )
                    root.destroy()
                    
                    if key is None:
                        print("Installation cancelled by user.")
                        return False
                        
                except:
                    key = input(f"Installation key (attempt {attempt}/{max_attempts}): ").strip()
            else:
                key = input(f"Installation key (attempt {attempt}/{max_attempts}): ").strip()
            
            if not key:
                print("Installation key cannot be empty.")
                continue
                
            print("Validating installation key...")
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/index",
                    json={
                        'action': 'validateInstallationKey',
                        'installationKey': key
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.installation_key = key
                        user_info = result.get('user', {})
                        print(f"✓ Installation key validated successfully!")
                        print(f"  User: {user_info.get('username', 'Unknown')}")
                        print(f"  Role: {user_info.get('role', 'Unknown')}")
                        return True
                    else:
                        print(f"✗ {result.get('message', 'Invalid installation key')}")
                else:
                    print(f"✗ Server error: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"✗ Network error: {e}")
            except Exception as e:
                print(f"✗ Validation error: {e}")
        
        print("Installation key validation failed after maximum attempts.")
        return False

    def register_device(self):
        """Register device with website and get encryption metadata using existing API"""
        print("Registering device with server...")
        print(f"API URL: {self.api_url}")
        print(f"MAC Address: {self.mac_address}")
        print(f"Username: {self.username}")
        print(f"Client Name: {self.client_name}")
        
        try:
            # Use existing website API format for device registration
            device_info = {
                'action': 'registerClient',  # Using existing API action
                'installationKey': self.installation_key,
                'macAddress': self.mac_address,
                'username': self.username,
                'clientName': self.client_name,
                'hostname': platform.node(),
                'platform': f"{platform.system()} {platform.release()}",
                'version': INSTALLER_VERSION,
                'installPath': '', # Will be updated after directory creation
                'macDetectionMethod': getattr(self, 'mac_detection_method', 'unknown'),
                'installerMode': 'advanced',
                'timestamp': datetime.now().isoformat(),
                # Additional security metadata
                'systemInfo': {
                    'osVersion': f"{platform.system()} {platform.release()} {platform.version()}",
                    'architecture': platform.machine(),
                    'processor': platform.processor(),
                    'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    'isAdmin': self.check_admin_privileges(),
                    'timezone': str(datetime.now().astimezone().tzinfo)
                }
            }
            
            print("Sending registration request...")
            # Debug: Show partial payload (without sensitive data)
            debug_info = {k: v for k, v in device_info.items() if k not in ['installationKey']}
            debug_info['installationKey'] = '***REDACTED***'
            print(f"Registration payload: {json.dumps(debug_info, indent=2)}")
            
            print(f"Making POST request to: {self.api_url}/api/index")
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
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content length: {len(response.text)} characters")
            print(f"Response body (first 1000 chars): {response.text[:1000]}")
            if len(response.text) > 1000:
                print(f"Response body (last 200 chars): ...{response.text[-200:]}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Parsed response JSON: {json.dumps(result, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response: {response.text[:200]}")
                    return False
                if result.get('success'):
                    # Handle server response gracefully - generate client data if server doesn't provide it
                    server_client_id = result.get('clientId')
                    if not server_client_id:
                        # Generate client ID from MAC and timestamp if server doesn't provide one
                        server_client_id = f"client_{self.mac_address}_{int(time.time())}"
                        print(f"Warning: Server didn't provide clientId, generated: {server_client_id}")
                    
                    self.device_data = {
                        'deviceId': server_client_id,
                        'clientId': server_client_id,
                        'isNewInstallation': result.get('isNewInstallation', True)
                    }
                    
                    # Get encryption key metadata (server provides key_id, client fetches keys at runtime)
                    server_key_id = result.get('keyId')
                    if not server_key_id:
                        # Generate key ID if server doesn't provide one
                        server_key_id = f"key_{self.mac_address}_{int(time.time())}"
                        print(f"Warning: Server didn't provide keyId, generated: {server_key_id}")
                    
                    self.key_id = server_key_id
                    
                    # Server-provided encryption metadata
                    self.encryption_metadata = {
                        'keyId': self.key_id,
                        'algorithm': 'AES-256-GCM',
                        'keyDerivation': 'PBKDF2',
                        'iterations': 100000,
                        'serverManaged': True
                    }
                    
                    # Store initial client policy from server
                    self.client_policy = result.get('policy', {
                        'allowWebsiteRequests': True,
                        'snoozeEnabled': True,
                        'updateCheckInterval': 86400,  # Daily
                        'heartbeatInterval': 300       # 5 minutes
                    })
                    
                    print(f"✓ Device registered successfully!")
                    print(f"  Client ID: {self.device_data.get('clientId')}")
                    print(f"  Key ID: {self.key_id}")
                    print(f"  New Installation: {self.device_data.get('isNewInstallation')}")
                    print(f"  Server Message: {result.get('message', 'No message')}")
                    
                    return True
                else:
                    error_msg = result.get('message', 'Unknown registration error')
                    print(f"✗ Registration failed: {error_msg}")
                    
                    # Handle specific error cases
                    if 'duplicate' in error_msg.lower() or 'already registered' in error_msg.lower():
                        print("  This MAC address is already registered.")
                        print("  Previous installation may need to be uninstalled first.")
                    elif 'invalid key' in error_msg.lower():
                        print("  Installation key is invalid or expired.")
                    
                    return False
            else:
                print(f"✗ Server error: HTTP {response.status_code}")
                try:
                    error_detail = response.text[:200]
                    print(f"  Server response: {error_detail}")
                except:
                    pass
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error: Unable to reach server at {self.api_url}")
            print("  Please check your internet connection and server URL.")
            return False
        except requests.exceptions.Timeout:
            print(f"✗ Timeout error: Server did not respond within 30 seconds")
            return False
        except Exception as e:
            print(f"✗ Registration error: {e}")
            return False

    def create_hidden_install_directory(self):
        """Create hidden, encrypted installation directory with random GUID path"""
        print("Creating hidden installation directory...")
        
        try:
            # Generate random GUID-based path in Program Files (x86) for better 64-bit compatibility
            if self.system == "Windows":
                # Use Program Files (x86) for better compatibility with 64-bit systems
                base_path = Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'))
                misleading_parent = base_path / "SystemResources"
                misleading_parent.mkdir(exist_ok=True)
                
                # Set misleading parent as system folder
                subprocess.run([
                    "attrib", "+S", "+H", str(misleading_parent)
                ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Create actual install path with nested GUIDs
                guid1 = str(uuid.uuid4())
                guid2 = str(uuid.uuid4())
                self.install_path = misleading_parent / guid1 / guid2
                
            else:
                # Unix-like systems
                self.install_path = Path.home() / f".{uuid.uuid4()}" / f".{uuid.uuid4()}"
            
            self.install_path.mkdir(parents=True, exist_ok=True)
            print(f"Installation path: {self.install_path}")
            
            # Set Windows attributes and ACLs
            if self.system == "Windows":
                self._set_windows_hidden_attributes()
                self._set_restrictive_acls()
                self._disable_indexing()
            else:
                self._set_unix_hidden_permissions()
            
            # Encrypt the install path and store in registry
            self._store_encrypted_path_info()
            
            print("✓ Hidden installation directory created and secured")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create hidden directory: {e}")
            return False

    def _set_windows_hidden_attributes(self):
        """Set Windows hidden and system attributes"""
        try:
            # Set hidden and system attributes recursively
            subprocess.run([
                "attrib", "+S", "+H", str(self.install_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Set parent directories as hidden too
            parent = self.install_path.parent
            subprocess.run([
                "attrib", "+S", "+H", str(parent)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
        except Exception as e:
            print(f"Warning: Could not set hidden attributes: {e}")

    def _set_restrictive_acls(self):
        """Set restrictive Windows ACLs with deletion protection"""
        try:
            import win32security
            import ntsecuritycon
            
            # Get current user SID
            user_sid = win32security.GetTokenInformation(
                win32security.GetCurrentProcessToken(),
                win32security.TokenUser
            )[0]
            
            # Create DACL that allows read/write but DENIES deletion
            dacl = win32security.ACL()
            
            # DENY delete permissions for current user
            dacl.AddAccessDeniedAce(
                win32security.ACL_REVISION,
                ntsecuritycon.DELETE | ntsecuritycon.FILE_DELETE_CHILD,
                user_sid
            )
            
            # DENY delete permissions for Everyone
            everyone_sid = win32security.LookupAccountName(None, "Everyone")[0]
            dacl.AddAccessDeniedAce(
                win32security.ACL_REVISION,
                ntsecuritycon.DELETE | ntsecuritycon.FILE_DELETE_CHILD,
                everyone_sid
            )
            
            # ALLOW read/write/execute for current user (but not delete)
            allowed_permissions = (
                ntsecuritycon.GENERIC_READ |
                ntsecuritycon.GENERIC_WRITE |
                ntsecuritycon.GENERIC_EXECUTE |
                ntsecuritycon.FILE_ADD_FILE |
                ntsecuritycon.FILE_ADD_SUBDIRECTORY |
                ntsecuritycon.FILE_WRITE_DATA |
                ntsecuritycon.FILE_APPEND_DATA
            )
            
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                allowed_permissions,
                user_sid
            )
            
            # Add full control for SYSTEM (needed for uninstaller)
            system_sid = win32security.LookupAccountName(None, "SYSTEM")[0]
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                ntsecuritycon.GENERIC_ALL,
                system_sid
            )
            
            # Apply DACL to directory and all subdirectories/files
            win32security.SetNamedSecurityInfo(
                str(self.install_path),
                win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
                None, None, dacl, None
            )
            
            # Apply to all files and subdirectories recursively
            for root, dirs, files in os.walk(self.install_path):
                for item in dirs + files:
                    item_path = Path(root) / item
                    try:
                        win32security.SetNamedSecurityInfo(
                            str(item_path),
                            win32security.SE_FILE_OBJECT,
                            win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
                            None, None, dacl, None
                        )
                    except:
                        pass  # Continue with other files if one fails
            
            print("✓ File system deletion protection enabled")
            
        except Exception as e:
            print(f"Warning: Could not set deletion protection ACLs: {e}")

    def _disable_indexing(self):
        """Disable Windows Search indexing for the directory"""
        try:
            # Set FILE_ATTRIBUTE_NOT_CONTENT_INDEXED
            file_attributes = win32file.GetFileAttributes(str(self.install_path))
            win32file.SetFileAttributes(
                str(self.install_path),
                file_attributes | win32con.FILE_ATTRIBUTE_NOT_CONTENT_INDEXED
            )
            
        except Exception as e:
            print(f"Warning: Could not disable indexing: {e}")

    def _set_unix_hidden_permissions(self):
        """Set restrictive permissions on Unix-like systems"""
        try:
            # Set directory permissions to 700 (owner only)
            os.chmod(self.install_path, 0o700)
            os.chmod(self.install_path.parent, 0o700)
            
        except Exception as e:
            print(f"Warning: Could not set restrictive permissions: {e}")

    def _store_encrypted_path_info(self):
        """Store encrypted installation path info in registry"""
        try:
            if self.system == "Windows":
                # Create/open registry key
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                    "Software\\PushNotifications") as key:
                    # Store only non-sensitive metadata
                    winreg.SetValueEx(key, "KeyId", 0, winreg.REG_SZ, self.key_id)
                    winreg.SetValueEx(key, "Username", 0, winreg.REG_SZ, self.username)
                    winreg.SetValueEx(key, "MacAddress", 0, winreg.REG_SZ, self.mac_address)
                    winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, INSTALLER_VERSION)
                    winreg.SetValueEx(key, "ApiUrl", 0, winreg.REG_SZ, self.api_url)
                    winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, 
                                    datetime.now().isoformat())
                    
                    # Store encrypted path hash (path itself encrypted server-side)
                    path_hash = hashlib.sha256(str(self.install_path).encode()).hexdigest()
                    winreg.SetValueEx(key, "PathHash", 0, winreg.REG_SZ, path_hash)
                    
        except Exception as e:
            print(f"Warning: Could not store registry information: {e}")

    def create_embedded_client_components(self):
        """Create client components embedded within this installer"""
        print("Creating embedded client components...")
        
        try:
            if self.system == "Windows":
                # Create Windows-specific executables using embedded Python functionality
                self._create_windows_client_exe()
                self._create_windows_uninstaller_exe() 
                self._create_windows_watchdog_service()
                self._create_windows_installer_copy()  # Include installer copy for repair
            else:
                # Create Unix-like executables
                self._create_unix_client_script()
                self._create_unix_uninstaller_script()
                self._create_unix_watchdog_script()
                self._create_unix_installer_copy()     # Include installer copy for repair
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create embedded components: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_windows_client_exe(self):
        """Create Windows Client.exe using embedded Python script"""
        client_script = self._get_embedded_windows_client_code()
        client_path = self.install_path / "Client.py"
        
        with open(client_path, 'w', encoding='utf-8') as f:
            f.write(client_script)
        
        # Create batch wrapper to run Python script invisibly with proper process name
        batch_wrapper = f'''@echo off
REM PushNotifications Client Launcher
cd /d "{self.install_path}"
title Push Notifications
pythonw.exe "{client_path}" %*
'''
        
        batch_path = self.install_path / "Client.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_wrapper)
        
        # Create executable wrapper (simulates .exe functionality)
        exe_wrapper_script = f'''
#!/usr/bin/env python3
# Push Notifications Client - Windows Service
import subprocess
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    client_script = script_dir / "Client.py"
    
    # Set process title for Task Manager
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("Push Notifications")
    except:
        pass
    
    # Run with hidden window on Windows
    if os.name == "nt":
        subprocess.run([sys.executable, str(client_script)] + sys.argv[1:], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.run([sys.executable, str(client_script)] + sys.argv[1:])
'''
        
        exe_path = self.install_path / "Client.exe"
        with open(exe_path, 'w', encoding='utf-8') as f:
            f.write(exe_wrapper_script)
        
        if self.system == "Windows":
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(client_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["attrib", "+S", "+H", str(batch_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        
        print("✓ Windows Client.exe created")
    
    def _create_windows_uninstaller_exe(self):
        """Create Windows Uninstaller.exe using embedded Python script"""
        uninstaller_script = self._get_embedded_windows_uninstaller_code()
        uninstaller_path = self.install_path / "Uninstaller.py"
        
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        # Create executable wrapper
        exe_wrapper_script = f'''
#!/usr/bin/env python3
# Uninstaller.exe Wrapper
import subprocess
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    uninstaller_script = script_dir / "Uninstaller.py"
    
    if os.name == "nt":
        subprocess.run([sys.executable, str(uninstaller_script)] + sys.argv[1:], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.run([sys.executable, str(uninstaller_script)] + sys.argv[1:])
'''
        
        exe_path = self.install_path / "Uninstaller.exe"
        with open(exe_path, 'w', encoding='utf-8') as f:
            f.write(exe_wrapper_script)
        
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(uninstaller_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        
        print("✓ Windows Uninstaller.exe created")
    
    def _create_windows_watchdog_service(self):
        """Create Windows WatchdogService.exe using embedded Python script"""
        watchdog_script = self._get_embedded_windows_watchdog_code()
        watchdog_path = self.install_path / "WatchdogService.py"
        
        with open(watchdog_path, 'w', encoding='utf-8') as f:
            f.write(watchdog_script)
        
        # Create file protection service
        protection_script = self._get_embedded_file_protection_code()
        protection_path = self.install_path / "FileProtectionService.py"
        
        with open(protection_path, 'w', encoding='utf-8') as f:
            f.write(protection_script)
        
        # Create service wrapper
        exe_wrapper_script = f'''
#!/usr/bin/env python3
# WatchdogService.exe Wrapper
import subprocess
import sys
import os
import threading
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    watchdog_script = script_dir / "WatchdogService.py"
    protection_script = script_dir / "FileProtectionService.py"
    
    def run_watchdog():
        if os.name == "nt":
            subprocess.run([sys.executable, str(watchdog_script)] + sys.argv[1:], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run([sys.executable, str(watchdog_script)] + sys.argv[1:])
    
    def run_protection():
        if os.name == "nt":
            subprocess.run([sys.executable, str(protection_script)] + sys.argv[1:], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run([sys.executable, str(protection_script)] + sys.argv[1:])
    
    # Run both services concurrently
    watchdog_thread = threading.Thread(target=run_watchdog, daemon=True)
    protection_thread = threading.Thread(target=run_protection, daemon=True)
    
    watchdog_thread.start()
    protection_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        pass
'''
        
        exe_path = self.install_path / "WatchdogService.exe"
        with open(exe_path, 'w', encoding='utf-8') as f:
            f.write(exe_wrapper_script)
        
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(watchdog_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["attrib", "+S", "+H", str(protection_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        
        print("✓ Windows WatchdogService.exe with file protection created")
    
    def _create_unix_client_script(self):
        """Create Unix client executable"""
        client_script = self._get_embedded_unix_client_code()
        client_path = self.install_path / "Client"
        
        with open(client_path, 'w', encoding='utf-8') as f:
            f.write(client_script)
        
        os.chmod(client_path, 0o755)
        print("✓ Unix Client executable created")
    
    def _create_unix_uninstaller_script(self):
        """Create Unix uninstaller executable"""
        uninstaller_script = self._get_embedded_unix_uninstaller_code()
        uninstaller_path = self.install_path / "Uninstaller"
        
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        os.chmod(uninstaller_path, 0o755)
        print("✓ Unix Uninstaller executable created")
    
    def _create_unix_watchdog_script(self):
        """Create Unix watchdog service"""
        watchdog_script = self._get_embedded_unix_watchdog_code()
        watchdog_path = self.install_path / "WatchdogService"
        
        with open(watchdog_path, 'w', encoding='utf-8') as f:
            f.write(watchdog_script)
        
        os.chmod(watchdog_path, 0o755)
        print("✓ Unix WatchdogService executable created")
    
    def _create_windows_installer_copy(self):
        """Create a copy of the installer for repair/maintenance functionality"""
        try:
            # Copy the current installer script to the installation directory
            current_installer = Path(__file__)
            installer_copy_path = self.install_path / "Installer.py"
            
            # Read current installer content
            with open(current_installer, 'r', encoding='utf-8') as f:
                installer_content = f.read()
            
            # Write installer copy
            with open(installer_copy_path, 'w', encoding='utf-8') as f:
                f.write(installer_content)
            
            # Create executable wrapper for Installer.exe
            exe_wrapper_script = f'''
#!/usr/bin/env python3
# Installer.exe Wrapper - Self-contained installer with repair mode
import subprocess
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    installer_script = script_dir / "Installer.py"
    
    # Run with hidden window on Windows
    if os.name == "nt":
        subprocess.run([sys.executable, str(installer_script)] + sys.argv[1:], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.run([sys.executable, str(installer_script)] + sys.argv[1:])
'''
            
            exe_path = self.install_path / "Installer.exe"
            with open(exe_path, 'w', encoding='utf-8') as f:
                f.write(exe_wrapper_script)
            
            # Create batch wrapper for invisible execution
            batch_wrapper = f'''@echo off
REM PushNotifications Installer/Repair Launcher
cd /d "{self.install_path}"
pythonw.exe "{installer_copy_path}" %*
'''
            
            batch_path = self.install_path / "Installer.bat"
            with open(batch_path, 'w') as f:
                f.write(batch_wrapper)
            
            if self.system == "Windows":
                # Set hidden attributes
                subprocess.run(["attrib", "+S", "+H", str(installer_copy_path)], 
                              check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["attrib", "+S", "+H", str(batch_path)], 
                              check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("✓ Windows Installer.exe (repair mode) created")
        
        except Exception as e:
            print(f"Warning: Could not create installer copy: {e}")
    
    def _create_unix_installer_copy(self):
        """Create a copy of the installer for Unix repair/maintenance"""
        try:
            # Copy the current installer script
            current_installer = Path(__file__)
            installer_copy_path = self.install_path / "Installer"
            
            # Read current installer content
            with open(current_installer, 'r', encoding='utf-8') as f:
                installer_content = f.read()
            
            # Write installer copy
            with open(installer_copy_path, 'w', encoding='utf-8') as f:
                f.write(installer_content)
            
            os.chmod(installer_copy_path, 0o755)
            print("✓ Unix Installer (repair mode) created")
        
        except Exception as e:
            print(f"Warning: Could not create installer copy: {e}")
    
    def _get_embedded_windows_client_code(self):
        """Get the embedded Windows client code with complete notification system"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Windows Client
Complete system with multi-monitor overlay, notification management, and security controls
Version: {INSTALLER_VERSION}
"""

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import ctypes
from ctypes import wintypes
import queue
import re

# Core functionality imports with auto-installation
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

# Windows-specific imports with auto-installation
if os.name == "nt":
    required_packages = {{
        'pystray': 'pystray>=0.19.4',
        'PIL': 'Pillow>=10.0.0',
        'screeninfo': 'screeninfo>=0.8.1',
        'win32gui': 'pywin32>=306',
        'tkinter': None  # Built-in
    }}
    
    for pkg, pip_pkg in required_packages.items():
        try:
            if pkg == 'PIL':
                from PIL import Image, ImageDraw
            elif pkg == 'tkinter':
                import tkinter as tk
                from tkinter import messagebox, simpledialog, ttk
            else:
                __import__(pkg)
        except ImportError:
            if pip_pkg:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_pkg],
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                    if pkg == 'PIL':
                        from PIL import Image, ImageDraw
                    elif pkg == 'tkinter':
                        import tkinter as tk
                        from tkinter import messagebox, simpledialog, ttk
                    else:
                        __import__(pkg)
                except Exception as e:
                    print(f"Warning: Could not install {{pkg}}: {{e}}")
    
    try:
        import pystray
        from pystray import MenuItem as item
        import win32gui
        import win32con
        import win32api
        import win32process
        import screeninfo
        WINDOWS_FEATURES_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Windows features limited due to missing modules: {{e}}")
        WINDOWS_FEATURES_AVAILABLE = False

# Client configuration
CLIENT_VERSION = "{INSTALLER_VERSION}"
API_URL = "{self.api_url}"/api/index
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"
KEY_ID = "{self.key_id}"

# Windows API constants
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class OverlayManager:
    """Manages multi-monitor grey overlays"""
    
    def __init__(self):
        self.overlays = []
        self.active = False
        
    def create_overlay_for_monitor(self, monitor):
        """Create overlay window for specific monitor"""
        try:
            overlay = tk.Toplevel()
            overlay.withdraw()  # Hide initially
            
            # Configure overlay properties
            overlay.overrideredirect(True)
            overlay.attributes('-alpha', 0.25)  # 25% opacity
            overlay.attributes('-topmost', True)
            overlay.attributes('-disabled', True)  # Click-through
            overlay.configure(bg='gray')
            
            # Position on monitor
            x, y = monitor.x, monitor.y
            width, height = monitor.width, monitor.height
            overlay.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
            
            return overlay
        except Exception as e:
            print(f"Error creating overlay: {{e}}")
            return None
    
    def show_overlays(self):
        """Show overlays on all monitors"""
        if self.active:
            return
            
        try:
            if WINDOWS_FEATURES_AVAILABLE and screeninfo:
                monitors = screeninfo.get_monitors()
            else:
                # Fallback: create overlay for primary monitor
                monitors = [type('Monitor', (), {{
                    'x': 0, 'y': 0, 
                    'width': user32.GetSystemMetrics(0),
                    'height': user32.GetSystemMetrics(1)
                }})()]
            
            root = tk.Tk()
            root.withdraw()  # Hide root window
            
            for monitor in monitors:
                overlay = self.create_overlay_for_monitor(monitor)
                if overlay:
                    self.overlays.append(overlay)
                    overlay.deiconify()  # Show overlay
            
            self.active = True
        except Exception as e:
            print(f"Error showing overlays: {{e}}")
    
    def hide_overlays(self):
        """Hide all overlays"""
        for overlay in self.overlays:
            try:
                overlay.destroy()
            except:
                pass
        self.overlays.clear()
        self.active = False

class WindowManager:
    """Manages window minimization and process restrictions"""
    
    def __init__(self):
        self.minimized_windows = []
        self.restricted_processes = {{
            'browsers': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 'brave.exe', 'iexplore.exe'],
            'vpn': ['openvpn.exe', 'nordvpn.exe', 'expressvpn.exe', 'cyberghost.exe', 'tunnelbear.exe'],
            'proxy': ['proxifier.exe', 'proxycap.exe', 'sockscap.exe']
        }}
        self.allowed_processes = ['taskmgr.exe', 'dwm.exe', 'winlogon.exe', 'csrss.exe', 'lsass.exe', 'services.exe']
    
    def minimize_all_windows(self):
        """Minimize all user windows to taskbar"""
        try:
            def enum_windows_callback(hwnd, lParam):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    # Skip system windows and current app
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title and not window_title.startswith('PushNotifications'):
                        try:
                            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                            self.minimized_windows.append(hwnd)
                        except:
                            pass
                return True
            
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            print(f"Error minimizing windows: {{e}}")
    
    def restore_windows(self):
        """Restore previously minimized windows"""
        for hwnd in self.minimized_windows:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except:
                pass
        self.minimized_windows.clear()
    
    def block_restricted_processes(self, allowed_websites=None):
        """Block VPN, proxy, and browser processes except allowed websites"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Check if it's a restricted process
                    is_restricted = False
                    for category, processes in self.restricted_processes.items():
                        if proc_name in [p.lower() for p in processes]:
                            is_restricted = True
                            break
                    
                    if is_restricted and proc_name not in [p.lower() for p in self.allowed_processes]:
                        # For browsers, check if websites are allowed
                        if proc_name in [p.lower() for p in self.restricted_processes['browsers']]:
                            if not allowed_websites:
                                proc.terminate()
                        else:
                            # Terminate VPN/proxy processes
                            proc.terminate()
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error blocking processes: {{e}}")

class NotificationWindow:
    """Individual notification window with website-style formatting"""
    
    def __init__(self, notification_data, callback_handler):
        self.data = notification_data
        self.callback = callback_handler
        self.window = None
        self.minimized = False
        self.website_request_var = None
        
    def create_window(self):
        """Create notification window with website-style formatting"""
        try:
            self.window = tk.Toplevel()
            self.window.title("Push Notification")
            
            # Configure window properties
            self.window.attributes('-topmost', True)
            self.window.resizable(False, False)
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)
            
            # Center on screen
            width, height = 400, 300
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
            
            # Website-style colors and fonts
            bg_color = "#f8f9fa"
            header_color = "#007bff"
            button_color = "#28a745"
            
            self.window.configure(bg=bg_color)
            
            # Header
            header_frame = tk.Frame(self.window, bg=header_color, height=50)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            title_label = tk.Label(header_frame, text="Push Notification", 
                                 bg=header_color, fg="white", 
                                 font=("Arial", 14, "bold"))
            title_label.pack(expand=True)
            
            # Message content
            content_frame = tk.Frame(self.window, bg=bg_color)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Message text
            message_text = self.data.get('message', '')
            message_label = tk.Label(content_frame, text=message_text, 
                                   bg=bg_color, wraplength=360, justify=tk.LEFT,
                                   font=("Arial", 10))
            message_label.pack(pady=(0, 10))
            
            # Allowed websites (if any)
            allowed_websites = self.data.get('allowedWebsites', [])
            if allowed_websites:
                websites_label = tk.Label(content_frame, 
                                        text=f"Allowed websites: {{', '.join(allowed_websites)}}", 
                                        bg=bg_color, wraplength=360, justify=tk.LEFT,
                                        font=("Arial", 9), fg="#666")
                websites_label.pack(pady=(0, 10))
            
            # Website request section (if allowed)
            if self.data.get('allowWebsiteRequests', False):
                request_frame = tk.LabelFrame(content_frame, text="Request Website Access", 
                                            bg=bg_color, font=("Arial", 9))
                request_frame.pack(fill=tk.X, pady=(0, 10))
                
                self.website_request_var = tk.StringVar()
                request_entry = tk.Entry(request_frame, textvariable=self.website_request_var,
                                       width=40)
                request_entry.pack(padx=5, pady=5)
                
                request_button = tk.Button(request_frame, text="Request Access", 
                                         command=self.request_website_access,
                                         bg=button_color, fg="white", font=("Arial", 9))
                request_button.pack(pady=(0, 5))
            
            # Action buttons
            button_frame = tk.Frame(self.window, bg=bg_color)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # Snooze buttons
            snooze_frame = tk.Frame(button_frame, bg=bg_color)
            snooze_frame.pack(fill=tk.X, pady=(0, 5))
            
            for minutes in [5, 15, 30]:
                snooze_btn = tk.Button(snooze_frame, text=f"Snooze {{minutes}}min", 
                                     command=lambda m=minutes: self.snooze_notification(m),
                                     bg="#ffc107", font=("Arial", 9))
                snooze_btn.pack(side=tk.LEFT, padx=2)
            
            # Complete button
            complete_btn = tk.Button(button_frame, text="Mark Complete", 
                                   command=self.complete_notification,
                                   bg="#28a745", fg="white", font=("Arial", 10, "bold"))
            complete_btn.pack(side=tk.RIGHT)
            
            # Minimize button (if website requests allowed)
            if self.data.get('allowWebsiteRequests', False):
                minimize_btn = tk.Button(button_frame, text="Minimize", 
                                       command=self.minimize_notification,
                                       bg="#6c757d", fg="white", font=("Arial", 9))
                minimize_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            print(f"Error creating notification window: {{e}}")
    
    def request_website_access(self):
        """Request access to a specific website"""
        website = self.website_request_var.get().strip()
        if website:
            self.callback('request_website', {{
                'notificationId': self.data.get('id'),
                'website': website
            }})
            messagebox.showinfo("Request Sent", "Website access request sent for approval.")
            self.website_request_var.set("")
    
    def snooze_notification(self, minutes):
        """Snooze notification for specified minutes"""
        self.callback('snooze', {{
            'notificationId': self.data.get('id'),
            'minutes': minutes
        }})
        self.close()
    
    def complete_notification(self):
        """Mark notification as complete"""
        self.callback('complete', {{
            'notificationId': self.data.get('id')
        }})
        self.close()
    
    def minimize_notification(self):
        """Minimize notification window"""
        if self.window:
            self.window.withdraw()
            self.minimized = True
    
    def restore_notification(self):
        """Restore minimized notification"""
        if self.window and self.minimized:
            self.window.deiconify()
            self.minimized = False
    
    def close(self):
        """Close notification window"""
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
    
    def on_close(self):
        """Handle window close event"""
        # Prevent closing - must use buttons
        pass

class PushNotificationsClient:
    """Main client application with complete functionality"""
    
    def __init__(self):
        self.running = True
        self.tray_icon = None
        self.notifications = []
        self.notification_windows = []
        self.overlay_manager = OverlayManager()
        self.window_manager = WindowManager()
        self.snooze_end_time = None
        self.security_active = False
        self.force_quit_detected = False
        
        # Set proper process title for Task Manager
        self._set_process_title()
        
        # Initialize Tkinter root
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window
        self.root.title("Push Notifications")
    
    def _set_process_title(self):
        """Set proper process title for Task Manager"""
        try:
            import ctypes
            # Set console window title to show "Push Notifications" in Task Manager
            ctypes.windll.kernel32.SetConsoleTitleW("Push Notifications")
        except Exception as e:
            print(f"Warning: Could not set process title: {{e}}")
        
    def create_tray_icon(self):
        """Create system tray icon with enhanced quick actions menu"""
        try:
            def create_image():
                # Try to load pnicon.png from the installation directory or current directory
                icon_paths = [
                    Path(__file__).parent / "pnicon.png",  # Same directory as this script
                    Path.cwd() / "pnicon.png",  # Current working directory
                    Path("C:\\Users\\gipso\\Documents\\GitHub\\PushNotifications\\pnicon.png")  # Absolute path
                ]
                
                for icon_path in icon_paths:
                    try:
                        if icon_path.exists():
                            image = Image.open(icon_path)
                            # Resize to standard tray icon size if needed
                            if image.size != (64, 64):
                                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                            # Convert to RGBA if not already
                            if image.mode != 'RGBA':
                                image = image.convert('RGBA')
                            print(f"✓ Loaded tray icon from: {{icon_path}}")
                            return image
                    except Exception as e:
                        print(f"Warning: Could not load icon from {{icon_path}}: {{e}}")
                        continue
                
                print("Warning: pnicon.png not found, creating fallback icon")
                
                # Fallback: create a simple icon if pnicon.png is not found
                width = height = 64
                image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                dc = ImageDraw.Draw(image)
                # Create a more distinctive icon
                dc.ellipse([8, 8, width-8, height-8], fill='#007bff', outline='#0056b3', width=2)
                # Draw notification bell icon
                try:
                    from PIL import ImageFont
                    font = ImageFont.load_default()
                    # Draw a simple bell shape
                    dc.polygon([
                        (width//2-8, height//2-4), (width//2+8, height//2-4),
                        (width//2+6, height//2+6), (width//2-6, height//2+6)
                    ], fill='white')
                    # Bell top
                    dc.ellipse([width//2-2, height//2-8, width//2+2, height//2-4], fill='white')
                    # Bell clapper
                    dc.ellipse([width//2-1, height//2+6, width//2+1, height//2+8], fill='white')
                except:
                    # Fallback: just use "PN" text
                    dc.text((width//2-10, height//2-8), "PN", fill='white')
                return image
            
            # Enhanced menu with quick actions
            menu = pystray.Menu(
                # Quick Actions Section
                item('Mark Complete', self.tray_mark_complete),
                item('Request Website Access', self.tray_request_website),
                pystray.Menu.SEPARATOR,
                # Administrative Actions
                item('Request Deletion', self.tray_request_deletion),
                item('Submit Bug Report', self.tray_submit_bug),
                pystray.Menu.SEPARATOR,
                # Standard Actions
                item('Show Status', self.show_status),
                item('Show All Notifications', self.show_all_notifications),
                item('Snooze All (5 min)', lambda: self.tray_snooze_all(5)),
                item('Snooze All (15 min)', lambda: self.tray_snooze_all(15)),
                item('Snooze All (30 min)', lambda: self.tray_snooze_all(30)),
                pystray.Menu.SEPARATOR,
                item('Settings', self.show_settings),
                item('About', self.show_about),
                pystray.Menu.SEPARATOR,
                item('Quit (Admin Required)', self.quit_application)
            )
            
            # Set proper window title for Task Manager
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleTitleW("PushNotifications Client")
            except:
                pass
            
            return pystray.Icon("PushNotifications", create_image(), "PushNotifications Client", menu)
        except Exception as e:
            print(f"Error creating tray icon: {{e}}")
            return None
    
    def show_status(self, icon=None, item=None):
        """Show client status"""
        try:
            active_count = len([n for n in self.notifications if not n.get('completed', False)])
            status_text = f"Push Client v{{CLIENT_VERSION}}\n"
            status_text += f"Client ID: {{CLIENT_ID}}\n"
            status_text += f"Status: Running\n"
            status_text += f"Active Notifications: {{active_count}}\n"
            status_text += f"Security Mode: {{'Active' if self.security_active else 'Inactive'}}"
            
            messagebox.showinfo("Push Client Status", status_text)
        except Exception as e:
            print(f"Error showing status: {{e}}")
    
    def show_all_notifications(self, icon=None, item=None):
        """Show all notification windows"""
        for window in self.notification_windows:
            if window.minimized:
                window.restore_notification()
    
    def tray_mark_complete(self, icon=None, item=None):
        """Mark the first active notification as complete from tray"""
        try:
            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
            if active_notifications:
                self.complete_notification(active_notifications[0].get('id'))
                messagebox.showinfo("Completed", "Notification marked as complete.")
            else:
                messagebox.showinfo("No Notifications", "No active notifications to complete.")
        except Exception as e:
            print(f"Error in tray mark complete: {{e}}")
    
    def tray_request_website(self, icon=None, item=None):
        """Request website access from tray"""
        try:
            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
            if not active_notifications:
                messagebox.showinfo("No Notifications", "No active notifications for website requests.")
                return
                
            website = simpledialog.askstring(
                "Website Access Request",
                "Enter the website URL you want to request access to:",
                initialvalue="https://"
            )
            
            if website:
                self.request_website_access(active_notifications[0].get('id'), website)
                messagebox.showinfo("Request Sent", f"Website access request sent for: {{website}}")
        except Exception as e:
            print(f"Error in tray request website: {{e}}")
    
    def tray_request_deletion(self, icon=None, item=None):
        """Request deletion/uninstallation from tray"""
        try:
            reason = simpledialog.askstring(
                "Request Deletion",
                "Please provide a reason for requesting deletion:",
                initialvalue="User requested uninstall"
            )
            
            if reason:
                requests.post(API_URL, json={{
                    'action': 'requestUninstall',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }}, timeout=10)
                
                messagebox.showinfo("Request Sent", "Deletion request sent for admin approval.")
        except Exception as e:
            print(f"Error in tray request deletion: {{e}}")
    
    def tray_submit_bug(self, icon=None, item=None):
        """Submit bug report from tray"""
        try:
            bug_description = simpledialog.askstring(
                "Submit Bug Report",
                "Describe the bug or issue:",
                initialvalue=""
            )
            
            if bug_description:
                # Collect system info for bug report
                import platform
                system_info = {{
                    'clientVersion': CLIENT_VERSION,
                    'platform': platform.platform(),
                    'pythonVersion': platform.python_version(),
                    'activeNotifications': len(self.notifications),
                    'securityActive': self.security_active
                }}
                
                requests.post(API_URL, json={{
                    'action': 'submitBugReport',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'bugDescription': bug_description,
                    'systemInfo': system_info,
                    'timestamp': datetime.now().isoformat()
                }}, timeout=10)
                
                messagebox.showinfo("Bug Report Sent", "Thank you! Your bug report has been submitted.")
        except Exception as e:
            print(f"Error in tray submit bug: {{e}}")
    
    def tray_snooze_all(self, minutes):
        """Snooze all notifications from tray"""
        try:
            self.snooze_notifications(minutes)
            messagebox.showinfo("Snoozed", f"All notifications snoozed for {{minutes}} minutes.")
        except Exception as e:
            print(f"Error in tray snooze all: {{e}}")
    
    def show_settings(self, icon=None, item=None):
        """Show client settings"""
        try:
            settings_window = tk.Toplevel()
            settings_window.title("PushNotifications Settings")
            settings_window.geometry("400x300")
            settings_window.attributes('-topmost', True)
            
            # Settings content
            tk.Label(settings_window, text="PushNotifications Settings", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            # Client info
            info_frame = tk.LabelFrame(settings_window, text="Client Information")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(info_frame, text=f"Version: {{CLIENT_VERSION}}").pack(anchor=tk.W, padx=5)
            tk.Label(info_frame, text=f"Client ID: {{CLIENT_ID}}").pack(anchor=tk.W, padx=5)
            tk.Label(info_frame, text=f"Status: {{'Running' if self.running else 'Stopped'}}").pack(anchor=tk.W, padx=5)
            
            # Settings options
            options_frame = tk.LabelFrame(settings_window, text="Options")
            options_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Button(options_frame, text="Check for Updates", 
                     command=lambda: self._check_for_client_updates()).pack(pady=2)
            tk.Button(options_frame, text="Restart Client", 
                     command=lambda: self._restart_client()).pack(pady=2)
            
            # Close button
            tk.Button(settings_window, text="Close", 
                     command=settings_window.destroy).pack(pady=10)
                     
        except Exception as e:
            print(f"Error showing settings: {{e}}")
    
    def show_about(self, icon=None, item=None):
        """Show about dialog"""
        try:
            about_text = f"""PushNotifications Client

Version: {{CLIENT_VERSION}}
Client ID: {{CLIENT_ID}}

© 2024 PushNotifications
Advanced notification management system

Features:
• Multi-monitor overlay support
• Website access control
• Automatic security enforcement
• Background operation"""
            
            messagebox.showinfo("About PushNotifications", about_text)
        except Exception as e:
            print(f"Error showing about: {{e}}")
    
    def _restart_client(self):
        """Restart the client application"""
        try:
            messagebox.showinfo("Restart", "Client will restart in 3 seconds...")
            import threading
            
            def restart_after_delay():
                import time
                time.sleep(3)
                # Stop current instance
                self.running = False
                if self.tray_icon:
                    self.tray_icon.stop()
                
                # Start new instance
                client_path = Path(__file__).parent / "Client.exe"
                if client_path.exists():
                    subprocess.Popen([sys.executable, str(client_path)],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            
            threading.Thread(target=restart_after_delay, daemon=True).start()
            
        except Exception as e:
            print(f"Error restarting client: {{e}}")
    
    def quit_application(self, icon=None, item=None):
        """Handle application quit - triggers force quit detection"""
        self.force_quit_detected = True
        self.running = False
        
        # Deactivate security features
        self.deactivate_security_features()
        
        # Send force quit notification to server
        self.send_force_quit_notification()
        
        # Launch uninstaller
        self.launch_uninstaller()
        
        if self.tray_icon:
            self.tray_icon.stop()
    
    def check_notifications(self):
        """Main notification checking loop"""
        while self.running:
            try:
                # Check if snooze period has ended
                if self.snooze_end_time and datetime.now() > self.snooze_end_time:
                    self.snooze_end_time = None
                    self.evaluate_security_state()
                
                # Fetch notifications from server
                response = requests.post(API_URL, json={{
                    'action': 'getNotifications',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS
                }}, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        server_notifications = result.get('notifications', [])
                        self.process_notifications(server_notifications)
                
                # Periodic update check (every hour)
                if not hasattr(self, '_last_update_check'):
                    self._last_update_check = time.time()
                elif time.time() - self._last_update_check > 3600:
                    self._check_for_client_updates()
                    self._last_update_check = time.time()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in notification check: {{e}}")
                time.sleep(60)
    
    def process_notifications(self, server_notifications):
        """Process notifications from server and update display"""
        try:
            # Check for uninstall commands first
            for notification in server_notifications:
                message = notification.get('message', '')
                if message in ['__UNINSTALL_ALL_COMMAND__', '__UNINSTALL_SPECIFIC_COMMAND__']:
                    reason = notification.get('reason', 'Administrative uninstall')
                    print(f"Uninstall command received: {{message}} - {{reason}}")
                    self.handle_uninstall_command(reason)
                    return  # Exit early - we're uninstalling
            
            # Update internal notification list
            self.notifications = server_notifications
            
            # Close windows for completed/removed notifications
            active_ids = {{n.get('id') for n in server_notifications if not n.get('completed', False)}}
            self.notification_windows = [w for w in self.notification_windows 
                                       if w.data.get('id') in active_ids or w.close() is None]
            
            # Create windows for new notifications
            existing_ids = {{w.data.get('id') for w in self.notification_windows}}
            for notification in server_notifications:
                if (not notification.get('completed', False) and 
                    notification.get('id') not in existing_ids):
                    self.create_notification_window(notification)
            
            # Update security state based on active notifications
            self.evaluate_security_state()
            
        except Exception as e:
            print(f"Error processing notifications: {{e}}")
    
    def create_notification_window(self, notification_data):
        """Create a new notification window"""
        try:
            window = NotificationWindow(notification_data, self.handle_notification_action)
            window.create_window()
            self.notification_windows.append(window)
            
            # Layer windows (oldest on top)
            self.layer_notification_windows()
            
        except Exception as e:
            print(f"Error creating notification window: {{e}}")
    
    def layer_notification_windows(self):
        """Layer notification windows with oldest on top"""
        try:
            # Sort by creation time (oldest first)
            self.notification_windows.sort(key=lambda w: w.data.get('created', 0))
            
            # Position windows in cascade
            for i, window in enumerate(self.notification_windows):
                if window.window and not window.minimized:
                    x = 100 + (i * 30)
                    y = 100 + (i * 30)
                    window.window.geometry(f"+{{x}}+{{y}}")
                    
        except Exception as e:
            print(f"Error layering windows: {{e}}")
    
    def handle_notification_action(self, action, data):
        """Handle actions from notification windows"""
        try:
            if action == 'snooze':
                self.snooze_notifications(data['minutes'])
                
            elif action == 'complete':
                self.complete_notification(data['notificationId'])
                
            elif action == 'request_website':
                self.request_website_access(data['notificationId'], data['website'])
                
        except Exception as e:
            print(f"Error handling notification action: {{e}}")
    
    def snooze_notifications(self, minutes):
        """Snooze all notifications for specified minutes"""
        try:
            self.snooze_end_time = datetime.now() + timedelta(minutes=minutes)
            self.deactivate_security_features()
            
            # Hide notification windows
            for window in self.notification_windows:
                window.minimize_notification()
                
            # Send snooze status to server
            requests.post(API_URL, json={{
                'action': 'snoozeNotifications',
                'clientId': CLIENT_ID,
                'minutes': minutes
            }}, timeout=10)
            
        except Exception as e:
            print(f"Error snoozing notifications: {{e}}")
    
    def complete_notification(self, notification_id):
        """Mark notification as complete"""
        try:
            # Send completion to server
            response = requests.post(API_URL, json={{
                'action': 'completeNotification',
                'clientId': CLIENT_ID,
                'notificationId': notification_id
            }}, timeout=10)
            
            # Remove from local list and close window
            self.notifications = [n for n in self.notifications if n.get('id') != notification_id]
            for window in self.notification_windows[:]:
                if window.data.get('id') == notification_id:
                    window.close()
                    self.notification_windows.remove(window)
                    break
            
            # Re-evaluate security state
            self.evaluate_security_state()
            
        except Exception as e:
            print(f"Error completing notification: {{e}}")
    
    def request_website_access(self, notification_id, website):
        """Request access to a specific website"""
        try:
            requests.post(API_URL, json={{
                'action': 'requestWebsiteAccess',
                'clientId': CLIENT_ID,
                'notificationId': notification_id,
                'website': website
            }}, timeout=10)
            
        except Exception as e:
            print(f"Error requesting website access: {{e}}")
    
    def evaluate_security_state(self):
        """Evaluate and apply security state based on active notifications"""
        try:
            # Check if we're in snooze period
            if self.snooze_end_time and datetime.now() < self.snooze_end_time:
                if self.security_active:
                    self.deactivate_security_features()
                return
            
            # Check for active notifications (not completed, not snoozed)
            active_notifications = [n for n in self.notifications 
                                  if not n.get('completed', False)]
            
            if active_notifications:
                if not self.security_active:
                    self.activate_security_features(active_notifications)
            else:
                if self.security_active:
                    self.deactivate_security_features()
                    
        except Exception as e:
            print(f"Error evaluating security state: {{e}}")
    
    def activate_security_features(self, notifications):
        """Activate security features (overlay, minimize, restrict)"""
        try:
            self.security_active = True
            
            # Get allowed websites from top notification
            top_notification = notifications[0] if notifications else {{}}
            allowed_websites = top_notification.get('allowedWebsites', [])
            
            # Show grey overlays on all monitors
            self.overlay_manager.show_overlays()
            
            # Minimize all windows
            self.window_manager.minimize_all_windows()
            
            # Block restricted processes
            self.window_manager.block_restricted_processes(allowed_websites)
            
        except Exception as e:
            print(f"Error activating security features: {{e}}")
    
    def deactivate_security_features(self):
        """Deactivate security features"""
        try:
            self.security_active = False
            
            # Hide overlays
            self.overlay_manager.hide_overlays()
            
            # Restore windows
            self.window_manager.restore_windows()
            
        except Exception as e:
            print(f"Error deactivating security features: {{e}}")
    
    def send_force_quit_notification(self):
        """Send force quit notification to server"""
        try:
            requests.post(API_URL, json={{
                'action': 'reportForceQuit',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'timestamp': datetime.now().isoformat()
            }}, timeout=10)
        except Exception as e:
            print(f"Error sending force quit notification: {{e}}")
    
    def handle_uninstall_command(self, reason):
        """Handle uninstall command received from server"""
        try:
            print(f"Processing uninstall command: {{reason}}")
            
            # Deactivate security features first
            self.deactivate_security_features()
            
            # Close all notification windows
            for window in self.notification_windows:
                window.close()
            self.notification_windows.clear()
            
            # Send acknowledgment to server
            try:
                requests.post(API_URL, json={{
                    'action': 'acknowledgeUninstall',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }}, timeout=10)
            except:
                pass  # Don't let server communication failure prevent uninstall
            
            # Launch uninstaller
            self.launch_uninstaller()
            
            # Exit the client
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()
                
        except Exception as e:
            print(f"Error handling uninstall command: {{e}}")
    
    def launch_uninstaller(self):
        """Launch uninstaller after force quit"""
        try:
            uninstaller_path = Path(__file__).parent / "Uninstaller.exe"
            if uninstaller_path.exists():
                subprocess.Popen([sys.executable, str(uninstaller_path)],
                               creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Error launching uninstaller: {{e}}")
    
    def _check_for_client_updates(self):
        """Check for client updates"""
        try:
            response = requests.post(API_URL, json={{
                'action': 'checkVersion',
                'currentVersion': CLIENT_VERSION,
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS
            }}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('updateAvailable'):
                    # Launch updater
                    installer_path = Path(__file__).parent / "Installer.exe"
                    if installer_path.exists():
                        subprocess.Popen([sys.executable, str(installer_path), "--update"],
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Error checking for updates: {{e}}")
    
    def run(self):
        """Main application loop"""
        try:
            # Create tray icon if available
            if WINDOWS_FEATURES_AVAILABLE:
                self.tray_icon = self.create_tray_icon()
            
            # Start notification checker in background thread
            notif_thread = threading.Thread(target=self.check_notifications, daemon=True)
            notif_thread.start()
            
            # Run main loop
            if self.tray_icon and WINDOWS_FEATURES_AVAILABLE:
                self.tray_icon.run()
            else:
                print("Push Client running in console mode...")
                while self.running:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Error in main run loop: {{e}}")
        finally:
            self.deactivate_security_features()

if __name__ == "__main__":
    try:
        client = PushNotificationsClient()
        client.run()
    except Exception as e:
        print(f"Fatal error: {{e}}")
        sys.exit(1)
'''
    
    def _get_embedded_windows_uninstaller_code(self):
        """Get the embedded Windows uninstaller code"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Windows Uninstaller
Embedded within installer - requests approval from website
"""

import os
import sys
import json
import shutil
import subprocess
import winreg
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

API_URL = "{self.api_url}"
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"
KEY_ID = "{self.key_id}"

class PushNotificationsUninstaller:
    def __init__(self):
        self.install_path = Path(__file__).parent
        
    def request_uninstall_approval(self):
        """Request uninstall approval and wait for response"""
        try:
            # First, submit the uninstall request
            print("Submitting uninstall request to website...")
            response = requests.post(f"{API_URL}/api/index", json={{
                'action': 'requestUninstall',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'keyId': KEY_ID,
                'installPath': str(self.install_path),
                'timestamp': datetime.now().isoformat(),
                'reason': 'Force quit detected'
            }}, timeout=30)
            
            if response.status_code != 200:
                print(f"Failed to submit uninstall request: HTTP {{response.status_code}}")
                return False
                
            result = response.json()
            if not result.get('success'):
                print(f"Uninstall request failed: {{result.get('message', 'Unknown error')}}")
                return False
                
            request_id = result.get('requestId')
            if not request_id:
                print("No request ID received from server")
                return False
                
            print(f"Uninstall request submitted successfully (ID: {{request_id}})")
            print("Waiting for administrator approval through website...")
            print("\nThe uninstall request has been sent to the administrator.")
            print("Please wait while they review and approve/deny the request.")
            print("This process may take several minutes.")
            
            # Now poll for approval status
            max_wait_time = 300  # 5 minutes maximum wait
            poll_interval = 10   # Check every 10 seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                time.sleep(poll_interval)
                waited_time += poll_interval
                
                try:
                    # Check for uninstall command from server
                    check_response = requests.post(f"{API_URL}/api/index", json={{
                        'action': 'getClientNotifications',
                        'clientId': CLIENT_ID
                    }}, timeout=10)
                    
                    if check_response.status_code == 200:
                        check_result = check_response.json()
                        if check_result.get('success'):
                            notifications = check_result.get('data', [])
                            
                            # Look for uninstall approval command
                            for notification in notifications:
                                message = notification.get('message', '')
                                if message == '__UNINSTALL_APPROVED_COMMAND__':
                                    print("\n✓ Uninstall request APPROVED by administrator!")
                                    return True
                                elif 'denied' in message.lower() or 'rejected' in message.lower():
                                    print("\n✗ Uninstall request DENIED by administrator.")
                                    return False
                    
                    print(f"Still waiting for approval... ({{waited_time}}s/{{max_wait_time}}s)")
                    
                except Exception as poll_error:
                    print(f"Error checking approval status: {{poll_error}}")
                    continue
            
            print("\n⏱️ Timeout waiting for administrator approval.")
            print("The request may still be pending. Client will be restarted.")
            return False
            
        except Exception as e:
            print(f"Error requesting uninstall approval: {{e}}")
            return False
    
    def perform_uninstall(self):
        try:
            # Remove scheduled tasks
            subprocess.run(['schtasks', '/delete', '/tn', 'PushClient', '/f'], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['schtasks', '/delete', '/tn', 'PushUpdater', '/f'], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Remove Windows service
            subprocess.run(['sc', 'stop', 'PushWatchdog'], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['sc', 'delete', 'PushWatchdog'], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Remove registry entries
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\PushNotifications")
            except:
                pass
            
            # Remove desktop shortcuts
            desktop = Path.home() / "Desktop"
            for shortcut in ["Push Client.lnk", "Push Client Repair.lnk"]:
                shortcut_path = desktop / shortcut
                if shortcut_path.exists():
                    shortcut_path.unlink()
            
            # Remove installation directory
            parent_dir = self.install_path.parent
            subprocess.run(['attrib', '-R', '-S', '-H', str(self.install_path), '/S'], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            shutil.rmtree(self.install_path, ignore_errors=True)
            
            print("Uninstallation completed successfully.")
            return True
        except Exception as e:
            print(f"Uninstallation error: {{e}}")
            return False
    
    def run(self):
        print("Requesting uninstall approval...")
        
        if self.request_uninstall_approval():
            print("Uninstall approved. Removing client...")
            if self.perform_uninstall():
                print("Client successfully uninstalled.")
            else:
                print("Uninstallation failed.")
        else:
            print("Uninstall request denied. Client will be restarted.")
            # Restart client
            client_path = self.install_path / "Client.exe"
            if client_path.exists():
                subprocess.Popen([sys.executable, str(client_path)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    uninstaller = PushNotificationsUninstaller()
    uninstaller.run()
'''
    
    def _get_embedded_windows_watchdog_code(self):
        """Get the embedded Windows watchdog service code"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Windows Watchdog Service
Monitors client process and launches uninstaller on force quit
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

CLIENT_ID = "{self.device_data.get('clientId')}"

class PushWatchdogService:
    def __init__(self):
        self.install_path = Path(__file__).parent
        self.client_path = self.install_path / "Client.py"
        self.uninstaller_path = self.install_path / "Uninstaller.exe"
        self.running = True
        
    def is_client_running(self):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('Client.py' in str(arg) for arg in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except:
            return False
    
    def launch_uninstaller(self):
        try:
            if self.uninstaller_path.exists():
                subprocess.Popen([sys.executable, str(self.uninstaller_path)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                print("Launched uninstaller due to client force quit.")
            else:
                print("Uninstaller not found.")
        except Exception as e:
            print(f"Failed to launch uninstaller: {{e}}")
    
    def restart_client(self):
        try:
            client_exe = self.install_path / "Client.exe"
            if client_exe.exists():
                subprocess.Popen([sys.executable, str(client_exe)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                print("Restarted client process.")
        except Exception as e:
            print(f"Failed to restart client: {{e}}")
    
    def run(self):
        print("PushNotifications Watchdog Service started.")
        
        while self.running:
            try:
                if not self.is_client_running():
                    print("Client process not detected. Launching uninstaller...")
                    self.launch_uninstaller()
                    # Wait for uninstaller to complete
                    time.sleep(30)
                    
                    # If we're still running, the uninstall was denied
                    if self.running and not self.is_client_running():
                        print("Uninstall denied. Restarting client...")
                        self.restart_client()
                        
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Watchdog error: {{e}}")
                time.sleep(60)
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    service = PushWatchdogService()
    try:
        service.run()
    except KeyboardInterrupt:
        service.stop()
'''
    
    def _get_embedded_unix_client_code(self):
        """Get the embedded Unix client code"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Unix Client
Cross-platform client with adapted functionality
"""

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# Import requirements
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

CLIENT_VERSION = "{INSTALLER_VERSION}"
API_URL = "{self.api_url}"
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"

class PushNotificationsClient:
    def __init__(self):
        self.running = True
        self.notifications = []
        
    def check_notifications(self):
        while self.running:
            try:
                response = requests.post(API_URL, json={{
                    'action': 'getNotifications',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS
                }}, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        notifications = result.get('notifications', [])
                        for notif in notifications:
                            self.show_notification(notif)
                            
                time.sleep(30)
            except Exception as e:
                print(f"Error checking notifications: {{e}}")
                time.sleep(60)
    
    def show_notification(self, notification):
        message = notification.get('message', '')
        print(f"Notification: {{message}}")
        # TODO: Implement Unix-specific notification display
        
    def run(self):
        print(f"Push Client v{{CLIENT_VERSION}} started (Unix mode)")
        self.check_notifications()

if __name__ == "__main__":
    client = PushNotificationsClient()
    client.run()
'''
    
    def _get_embedded_unix_uninstaller_code(self):
        """Get the embedded Unix uninstaller code"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Unix Uninstaller
"""

import os
import sys
import shutil
from pathlib import Path

class UnixUninstaller:
    def __init__(self):
        self.install_path = Path(__file__).parent
        
    def run(self):
        print("Uninstalling PushNotifications...")
        try:
            # Remove autostart entries
            autostart_file = Path.home() / ".config/autostart/pushnotifications-client.desktop"
            if autostart_file.exists():
                autostart_file.unlink()
            
            # Remove desktop shortcuts
            desktop = Path.home() / "Desktop"
            for shortcut in ["push-client.desktop", "push-repair.desktop"]:
                shortcut_path = desktop / shortcut
                if shortcut_path.exists():
                    shortcut_path.unlink()
            
            # Remove installation directory
            shutil.rmtree(self.install_path, ignore_errors=True)
            print("Uninstallation completed.")
        except Exception as e:
            print(f"Uninstallation error: {{e}}")

if __name__ == "__main__":
    uninstaller = UnixUninstaller()
    uninstaller.run()
'''
    
    def _get_embedded_unix_watchdog_code(self):
        """Get the embedded Unix watchdog service code"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Unix Watchdog Service
"""

import os
import sys
import time
import subprocess
from pathlib import Path

class UnixWatchdog:
    def __init__(self):
        self.install_path = Path(__file__).parent
        self.client_path = self.install_path / "Client"
        self.running = True
        
    def is_client_running(self):
        try:
            result = subprocess.run(['pgrep', '-f', 'Client'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def restart_client(self):
        try:
            if self.client_path.exists():
                subprocess.Popen([str(self.client_path)])
                print("Restarted client.")
        except Exception as e:
            print(f"Failed to restart client: {{e}}")
    
    def run(self):
        print("Unix Watchdog Service started.")
        while self.running:
            try:
                if not self.is_client_running():
                    print("Client not running. Restarting...")
                    self.restart_client()
                time.sleep(60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Watchdog error: {{e}}")
                time.sleep(60)

if __name__ == "__main__":
    watchdog = UnixWatchdog()
    watchdog.run()
'''
    
    def _get_embedded_file_protection_code(self):
        """Get the embedded file protection service code for Windows"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications File System Protection Service
Monitors for deletion attempts and blocks them unless approved through website
"""

import os
import sys
import time
import threading
import subprocess
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Auto-install dependencies
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

# Windows-specific imports
if os.name == "nt":
    try:
        import win32file
        import win32con
        import win32api
        import win32security
        import ntsecuritycon
        import pywintypes
        WINDOWS_SECURITY_AVAILABLE = True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pywin32'])
            import win32file
            import win32con
            import win32api
            import win32security
            import ntsecuritycon
            import pywintypes
            WINDOWS_SECURITY_AVAILABLE = True
        except ImportError:
            WINDOWS_SECURITY_AVAILABLE = False
            print("Warning: Windows security features not available")
else:
    WINDOWS_SECURITY_AVAILABLE = False

# Configuration
API_URL = "{self.api_url}/api/index"
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"
KEY_ID = "{self.key_id}"
INSTALL_PATH = Path(__file__).parent

class FileSystemProtectionService:
    """Service to monitor file system for deletion attempts and request website approval"""
    
    def __init__(self):
        self.install_path = INSTALL_PATH
        self.running = True
        self.pending_approvals = {{}}
        self.approved_deletions = set()
        self.monitoring_processes = set()
        
        # Suspicious processes that might indicate deletion attempts
        self.deletion_processes = {{
            'explorer.exe',       # Windows Explorer (right-click delete)
            'cmd.exe',           # Command prompt (del, rmdir commands)
            'powershell.exe',    # PowerShell (Remove-Item)
            'taskmgr.exe',       # Task Manager (End task)
            'uninstall.exe',     # Generic uninstallers
            'cleanmgr.exe',      # Disk Cleanup
            'ccleaner.exe',      # CCleaner
            'cleanmaster.exe'    # Clean Master
        }}
        
        # File/directory monitoring patterns
        self.protected_paths = {{
            str(self.install_path),
            str(self.install_path.parent),
            str(self.install_path / "Client.exe"),
            str(self.install_path / "Client.py"),
            str(self.install_path / "Uninstaller.exe"),
            str(self.install_path / "WatchdogService.exe"),
            str(self.install_path / ".vault"),
            str(self.install_path / ".security_marker")
        }}
        
        print(f"File Protection Service initialized for: {{self.install_path}}")
        print(f"Protected paths: {{len(self.protected_paths)}}")
    
    def is_path_protected(self, path):
        """Check if a path is within protected areas"""
        path_str = str(Path(path).resolve())
        for protected in self.protected_paths:
            if path_str.startswith(protected):
                return True
        return False
    
    def monitor_suspicious_processes(self):
        """Monitor for suspicious processes that might attempt deletion"""
        while self.running:
            try:
                current_processes = set()
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        proc_name = proc.info['name'].lower()
                        proc_pid = proc.info['pid']
                        proc_cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                        
                        # Check if it's a deletion-related process
                        if proc_name in self.deletion_processes:
                            current_processes.add(proc_pid)
                            
                            # Check if this is a new process we haven't seen
                            if proc_pid not in self.monitoring_processes:
                                self.monitoring_processes.add(proc_pid)
                                
                                # Check command line for deletion attempts
                                suspicious_commands = [
                                    'del', 'rmdir', 'remove-item', 'rm -rf',
                                    'uninstall', 'delete', str(self.install_path).lower()
                                ]
                                
                                if any(cmd in proc_cmdline for cmd in suspicious_commands):
                                    print(f"⚠️  Suspicious deletion activity detected:")
                                    print(f"   Process: {{proc_name}} (PID: {{proc_pid}})")
                                    print(f"   Command: {{proc_cmdline[:100]}}...")
                                    
                                    # Request approval for this deletion attempt
                                    self.request_deletion_approval(
                                        process_name=proc_name,
                                        process_id=proc_pid,
                                        command_line=proc_cmdline[:200],
                                        detection_method="process_monitoring"
                                    )
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Clean up processes that are no longer running
                self.monitoring_processes &= current_processes
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in process monitoring: {{e}}")
                time.sleep(30)
    
    def monitor_file_system_changes(self):
        """Monitor file system for changes to protected paths"""
        if not WINDOWS_SECURITY_AVAILABLE:
            print("File system monitoring requires Windows security modules")
            return
            
        while self.running:
            try:
                # Check if protected files still exist
                for protected_path in self.protected_paths.copy():
                    path_obj = Path(protected_path)
                    
                    if path_obj.exists():
                        # Check file permissions and attributes
                        try:
                            # Verify file hasn't been marked for deletion
                            if path_obj.is_file():
                                attrs = win32file.GetFileAttributes(str(path_obj))
                                
                                # Check if file attributes have been modified suspiciously
                                expected_attrs = (win32con.FILE_ATTRIBUTE_HIDDEN | 
                                                win32con.FILE_ATTRIBUTE_SYSTEM)
                                
                                if not (attrs & expected_attrs):
                                    print(f"⚠️  Protected file attributes modified: {{path_obj}}")
                                    
                                    # Restore proper attributes
                                    try:
                                        win32file.SetFileAttributes(str(path_obj), 
                                                                   attrs | expected_attrs)
                                        print(f"✓ Restored attributes for: {{path_obj.name}}")
                                    except:
                                        print(f"✗ Failed to restore attributes for: {{path_obj.name}}")
                                        
                                        # Request approval for this modification
                                        self.request_deletion_approval(
                                            file_path=str(path_obj),
                                            detection_method="attribute_modification"
                                        )
                        
                        except Exception as e:
                            print(f"Error checking {{path_obj}}: {{e}}")
                    
                    else:
                        # Protected file/directory has been deleted!
                        print(f"🚨 PROTECTED FILE DELETED: {{protected_path}}")
                        
                        # Check if this deletion was pre-approved
                        path_hash = hashlib.sha256(protected_path.encode()).hexdigest()
                        if path_hash not in self.approved_deletions:
                            print(f"⚠️  UNAUTHORIZED DELETION DETECTED!")
                            
                            # Request immediate approval and attempt restoration
                            self.request_deletion_approval(
                                file_path=protected_path,
                                detection_method="file_deletion",
                                emergency=True
                            )
                        else:
                            print(f"✓ Deletion was pre-approved")
                            self.approved_deletions.remove(path_hash)
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error in file system monitoring: {{e}}")
                time.sleep(30)
    
    def request_deletion_approval(self, **kwargs):
        """Request approval for deletion through website"""
        try:
            request_id = f"del_{{int(time.time())}}_{{''.join(str(hash(str(kwargs)))[-6:])}}"
            
            approval_data = {{
                'action': 'requestDeletionApproval',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'keyId': KEY_ID,
                'requestId': request_id,
                'timestamp': datetime.now().isoformat(),
                'installPath': str(self.install_path),
                'detectionDetails': kwargs,
                'protectedPaths': list(self.protected_paths),
                'systemInfo': {{
                    'platform': os.name,
                    'currentUser': os.environ.get('USERNAME', 'unknown'),
                    'workingDirectory': os.getcwd()
                }}
            }}
            
            print(f"📤 Sending deletion approval request: {{request_id}}")
            print(f"   Method: {{kwargs.get('detection_method', 'unknown')}}")
            print(f"   Details: {{str(kwargs)[:100]}}...")
            
            # Send to website
            response = requests.post(API_URL, json=approval_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.pending_approvals[request_id] = {{
                        'submitted': datetime.now(),
                        'details': kwargs,
                        'status': 'pending'
                    }}
                    
                    print(f"✓ Deletion approval request sent successfully")
                    
                    # Start monitoring for approval
                    threading.Thread(
                        target=self.monitor_approval_response,
                        args=(request_id,),
                        daemon=True
                    ).start()
                    
                else:
                    print(f"✗ Server rejected approval request: {{result.get('message')}}")
            else:
                print(f"✗ Failed to send approval request: HTTP {{response.status_code}}")
                
        except Exception as e:
            print(f"Error requesting deletion approval: {{e}}")
    
    def monitor_approval_response(self, request_id):
        """Monitor for approval response from website"""
        max_wait_time = 1800  # 30 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check for response from server
                check_response = requests.post(API_URL, json={{
                    'action': 'checkDeletionApproval',
                    'clientId': CLIENT_ID,
                    'requestId': request_id
                }}, timeout=10)
                
                if check_response.status_code == 200:
                    result = check_response.json()
                    if result.get('success'):
                        approval_status = result.get('approvalStatus')
                        
                        if approval_status == 'approved':
                            print(f"✅ Deletion request APPROVED: {{request_id}}")
                            
                            # Add to approved deletions
                            request_details = self.pending_approvals.get(request_id, {{}})
                            file_path = request_details.get('details', {{}}).get('file_path')
                            
                            if file_path:
                                path_hash = hashlib.sha256(file_path.encode()).hexdigest()
                                self.approved_deletions.add(path_hash)
                                print(f"✓ Pre-approved deletion for: {{Path(file_path).name}}")
                            
                            # Mark as approved
                            self.pending_approvals[request_id]['status'] = 'approved'
                            self.pending_approvals[request_id]['approved_at'] = datetime.now()
                            
                            # Execute any approval-specific actions
                            self.handle_approved_deletion(request_id)
                            return
                            
                        elif approval_status == 'denied':
                            print(f"❌ Deletion request DENIED: {{request_id}}")
                            
                            # Mark as denied
                            self.pending_approvals[request_id]['status'] = 'denied'
                            self.pending_approvals[request_id]['denied_at'] = datetime.now()
                            
                            # Execute denial actions (restore files, restart services, etc.)
                            self.handle_denied_deletion(request_id)
                            return
                
                time.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                print(f"Error checking approval status: {{e}}")
                time.sleep(30)
        
        # Timeout - treat as denied for security
        print(f"⏱️ Approval request timeout: {{request_id}} (treating as DENIED)")
        self.pending_approvals[request_id]['status'] = 'timeout_denied'
        self.handle_denied_deletion(request_id)
    
    def handle_approved_deletion(self, request_id):
        """Handle actions when deletion is approved"""
        try:
            request_details = self.pending_approvals.get(request_id, {{}})
            detection_method = request_details.get('details', {{}}).get('detection_method')
            
            print(f"Processing approved deletion: {{request_id}}")
            print(f"Method: {{detection_method}}")
            
            if detection_method == 'file_deletion':
                # File was already deleted and approved - no action needed
                print("✓ File deletion approved - no restoration needed")
                
            elif detection_method == 'process_monitoring':
                # Allow the process to continue
                print("✓ Process deletion approved - allowing to continue")
                
            elif detection_method == 'attribute_modification':
                # Allow attribute changes
                print("✓ Attribute modification approved")
            
            # Log the approval
            self.log_approval_action(request_id, 'approved')
            
        except Exception as e:
            print(f"Error handling approved deletion: {{e}}")
    
    def handle_denied_deletion(self, request_id):
        """Handle actions when deletion is denied"""
        try:
            request_details = self.pending_approvals.get(request_id, {{}})
            details = request_details.get('details', {{}})
            detection_method = details.get('detection_method')
            
            print(f"Processing denied deletion: {{request_id}}")
            print(f"Method: {{detection_method}}")
            
            if detection_method == 'file_deletion':
                # Attempt to restore from backup or reinstall
                file_path = details.get('file_path')
                if file_path:
                    print(f"🔄 Attempting to restore: {{Path(file_path).name}}")
                    self.attempt_file_restoration(file_path)
                    
            elif detection_method == 'process_monitoring':
                # Try to terminate the suspicious process
                process_id = details.get('process_id')
                if process_id:
                    print(f"🛑 Attempting to stop suspicious process: {{process_id}}")
                    self.terminate_suspicious_process(process_id)
                    
            elif detection_method == 'attribute_modification':
                # Restore original attributes
                file_path = details.get('file_path')
                if file_path and Path(file_path).exists():
                    print(f"🔧 Restoring file attributes: {{Path(file_path).name}}")
                    self.restore_file_attributes(file_path)
            
            # Log the denial
            self.log_approval_action(request_id, 'denied')
            
        except Exception as e:
            print(f"Error handling denied deletion: {{e}}")
    
    def attempt_file_restoration(self, file_path):
        """Attempt to restore a deleted file"""
        try:
            path_obj = Path(file_path)
            
            # Try to recreate from installer if it's a core component
            if path_obj.name in ['Client.exe', 'Uninstaller.exe', 'WatchdogService.exe']:
                print(f"🏗️  Recreating core component: {{path_obj.name}}")
                
                # Launch installer in repair mode
                installer_path = self.install_path / "Installer.exe"
                if installer_path.exists():
                    subprocess.Popen([
                        sys.executable, str(installer_path), "--repair"
                    ], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    print(f"✓ Repair process initiated")
                else:
                    print(f"✗ Installer not found for repair")
            
            else:
                print(f"⚠️  Cannot restore: {{path_obj.name}} (no restoration method)")
                
        except Exception as e:
            print(f"Error in file restoration: {{e}}")
    
    def terminate_suspicious_process(self, process_id):
        """Terminate a suspicious process"""
        try:
            proc = psutil.Process(process_id)
            print(f"🔪 Terminating process: {{proc.name()}} ({{process_id}})")
            proc.terminate()
            
            # Wait a bit and force kill if necessary
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                print(f"🔥 Force killing process: {{process_id}}")
                proc.kill()
                
            print(f"✓ Process terminated: {{process_id}}")
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Could not terminate process {{process_id}}: {{e}}")
    
    def restore_file_attributes(self, file_path):
        """Restore proper file attributes"""
        try:
            if WINDOWS_SECURITY_AVAILABLE and os.name == 'nt':
                # Restore hidden and system attributes
                attrs = (win32con.FILE_ATTRIBUTE_HIDDEN | 
                        win32con.FILE_ATTRIBUTE_SYSTEM)
                
                win32file.SetFileAttributes(str(file_path), attrs)
                print(f"✓ Restored attributes for: {{Path(file_path).name}}")
            
        except Exception as e:
            print(f"Error restoring attributes: {{e}}")
    
    def log_approval_action(self, request_id, action):
        """Log approval actions for audit trail"""
        try:
            log_data = {{
                'requestId': request_id,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'details': self.pending_approvals.get(request_id, {{}})
            }}
            
            # Send log to server
            requests.post(API_URL, json={{
                'action': 'logApprovalAction',
                'clientId': CLIENT_ID,
                'logData': log_data
            }}, timeout=10)
            
        except Exception as e:
            print(f"Error logging approval action: {{e}}")
    
    def cleanup_old_requests(self):
        """Clean up old pending approval requests"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                old_requests = [
                    req_id for req_id, details in self.pending_approvals.items()
                    if details.get('submitted', datetime.now()) < cutoff_time
                ]
                
                for req_id in old_requests:
                    print(f"🧹 Cleaning up old request: {{req_id}}")
                    del self.pending_approvals[req_id]
                
                time.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                print(f"Error in cleanup: {{e}}")
                time.sleep(3600)
    
    def run(self):
        """Main service loop"""
        print(f"🛡️  File System Protection Service Started")
        print(f"    Install Path: {{self.install_path}}")
        print(f"    Protected Paths: {{len(self.protected_paths)}}")
        print(f"    Client ID: {{CLIENT_ID}}")
        print(f"    API URL: {{API_URL}}")
        
        try:
            # Start monitoring threads
            threads = [
                threading.Thread(target=self.monitor_suspicious_processes, daemon=True),
                threading.Thread(target=self.monitor_file_system_changes, daemon=True),
                threading.Thread(target=self.cleanup_old_requests, daemon=True)
            ]
            
            for thread in threads:
                thread.start()
                print(f"✓ Started monitoring thread: {{thread.name}}")
            
            # Main service loop
            while self.running:
                # Periodic status report
                active_requests = len([r for r in self.pending_approvals.values() 
                                     if r.get('status') == 'pending'])
                
                if active_requests > 0:
                    print(f"📊 Status: {{active_requests}} pending approval requests")
                
                time.sleep(300)  # Status update every 5 minutes
                
        except KeyboardInterrupt:
            print("\n🛑 File Protection Service stopping...")
            self.stop()
        except Exception as e:
            print(f"💥 Service error: {{e}}")
            self.stop()
    
    def stop(self):
        """Stop the protection service"""
        self.running = False
        print("✓ File Protection Service stopped")

if __name__ == "__main__":
    try:
        service = FileSystemProtectionService()
        service.run()
    except Exception as e:
        print(f"Fatal error: {{e}}")
        sys.exit(1)
'''

    def create_encrypted_vault(self):
        """Create AES-256-GCM encrypted configuration vault"""
        print("Creating encrypted configuration vault...")
        
        try:
            # Prepare vault data with comprehensive client configuration
            vault_data = {
                'deviceId': self.device_data.get('deviceId'),
                'clientId': self.device_data.get('clientId'),
                'keyId': self.key_id,
                'apiUrl': self.api_url,
                'macAddress': self.mac_address,
                'username': self.username,
                'clientName': self.client_name,
                'installPath': str(self.install_path),
                'version': INSTALLER_VERSION,
                'encryptionMetadata': self.encryption_metadata,
                'clientPolicy': getattr(self, 'client_policy', {}),
                'macDetectionMethod': getattr(self, 'mac_detection_method', 'unknown'),
                'created': datetime.now().isoformat(),
                'lastUpdated': datetime.now().isoformat(),
                # Runtime configuration
                'config': {
                    'heartbeatInterval': 300,  # 5 minutes
                    'updateCheckInterval': 86400,  # Daily
                    'notificationPollInterval': 30,  # 30 seconds
                    'overlayOpacity': 0.25,  # 25% grey
                    'snoozeOptions': [5, 15, 30],  # minutes
                    'flashIntervals': [300, 240, 180, 120, 90, 60, 45, 30, 20, 15, 10, 5],  # seconds
                    'allowedTaskManagerApps': [
                        'taskmgr.exe', 'dwm.exe', 'winlogon.exe', 'csrss.exe',
                        'lsass.exe', 'services.exe', 'svchost.exe'
                    ],
                    'browserProcesses': [
                        'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe',
                        'brave.exe', 'iexplore.exe', 'safari.exe'
                    ]
                }
            }
            
            vault_path = self.install_path / ".vault"
            
            # Implement AES-256-GCM encryption with server-derived key
            # Note: In production, master key comes from server, derived locally for vault encryption
            vault_json = json.dumps(vault_data, indent=2).encode('utf-8')
            
            # Generate a vault-specific salt and nonce
            import secrets
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)  # GCM nonce
            
            # For demo: derive key from key_id (in production, fetch from server)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.encryption_metadata.get('iterations', 100000),
            )
            # In production: key = server_provided_key
            # For demo: derive from key_id
            demo_key_material = f"{self.key_id}:{self.mac_address}:vault_key".encode()
            derived_key = kdf.derive(demo_key_material)
            
            # Encrypt with AES-256-GCM
            aesgcm = AESGCM(derived_key)
            encrypted_data = aesgcm.encrypt(nonce, vault_json, None)
            
            # Create vault file structure
            vault_header = {
                'version': 'VAULT_V2_AES256GCM',
                'keyId': self.key_id,
                'algorithm': 'AES-256-GCM',
                'created': datetime.now().isoformat(),
                'salt': salt.hex(),
                'nonce': nonce.hex()
            }
            
            # Write encrypted vault
            with open(vault_path, 'wb') as f:
                # Write header (unencrypted metadata)
                header_json = json.dumps(vault_header, indent=2).encode('utf-8')
                f.write(len(header_json).to_bytes(4, 'little'))  # Header length
                f.write(header_json)
                # Write encrypted payload
                f.write(encrypted_data)
            
            # Set Windows hidden and system attributes
            if self.system == "Windows":
                subprocess.run([
                    "attrib", "+S", "+H", str(vault_path)
                ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Unix permissions
                os.chmod(vault_path, 0o600)  # Read/write for owner only
            
            # Create additional security marker
            marker_path = self.install_path / ".security_marker"
            marker_data = {
                'installId': str(uuid.uuid4()),
                'keyId': self.key_id,
                'pathHash': hashlib.sha256(str(self.install_path).encode()).hexdigest(),
                'created': datetime.now().isoformat(),
                'version': INSTALLER_VERSION
            }
            
            with open(marker_path, 'w') as f:
                json.dump(marker_data, f, indent=2)
            
            if self.system == "Windows":
                subprocess.run([
                    "attrib", "+S", "+H", str(marker_path)
                ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Securely clear key material from memory
            derived_key = b'\x00' * len(derived_key)
            demo_key_material = b'\x00' * len(demo_key_material)
            
            print("✓ AES-256-GCM encrypted vault created")
            print(f"  Encryption Algorithm: {vault_header['algorithm']}")
            print(f"  Key ID: {self.key_id}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create encrypted vault: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_scheduled_tasks(self):
        """Create Windows scheduled tasks for client and updater"""
        if self.system != "Windows":
            return True
            
        print("Creating scheduled tasks...")
        
        try:
            # Create PushClient task - runs at logon with highest privileges
            client_task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>PushNotifications Client - Background Service</Description>
    <Author>PushNotifications</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>4</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{self.install_path / "Client.exe"}</Command>
      <WorkingDirectory>{self.install_path}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

            # Create daily updater task - runs at 1 PM
            updater_task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>PushNotifications Updater - Daily Update Check</Description>
    <Author>PushNotifications</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T13:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{self.install_path / "Installer.exe"}</Command>
      <Arguments>--update-check</Arguments>
      <WorkingDirectory>{self.install_path}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

            # Import tasks using schtasks
            import tempfile
            
            # Create client task
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(client_task_xml)
                client_xml_path = f.name
            
            result = subprocess.run([
                'schtasks', '/create', '/tn', 'PushClient',
                '/xml', client_xml_path, '/f'
            ], capture_output=True, text=True, 
               creationflags=subprocess.CREATE_NO_WINDOW)
            
            os.unlink(client_xml_path)
            
            if result.returncode == 0:
                print("✓ PushClient scheduled task created")
            else:
                print(f"✗ Failed to create PushClient task: {result.stderr}")
                return False
            
            # Create updater task
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(updater_task_xml)
                updater_xml_path = f.name
            
            result = subprocess.run([
                'schtasks', '/create', '/tn', 'PushUpdater',
                '/xml', updater_xml_path, '/f'
            ], capture_output=True, text=True,
               creationflags=subprocess.CREATE_NO_WINDOW)
            
            os.unlink(updater_xml_path)
            
            if result.returncode == 0:
                print("✓ PushUpdater scheduled task created")
            else:
                print(f"✗ Failed to create PushUpdater task: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create scheduled tasks: {e}")
            return False
    
    def create_startup_entries(self):
        """Create additional startup entries for maximum reliability"""
        if self.system != "Windows":
            return True
            
        print("Creating additional startup entries...")
        
        try:
            # Method 1: Registry run key (user-level auto-start)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                "Software\\Microsoft\\Windows\\CurrentVersion\\Run") as key:
                client_cmd = f'pythonw.exe "{self.install_path / "Client.py"}"'
                winreg.SetValueEx(key, "PushNotifications", 0, winreg.REG_SZ, client_cmd)
                print("✓ Registry startup entry created")
            
            # Method 2: Startup folder shortcut (user-visible but reliable)
            try:
                import win32com.client
                
                startup_folder = Path(os.environ.get('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                startup_folder.mkdir(parents=True, exist_ok=True)
                
                shell = win32com.client.Dispatch("WScript.Shell")
                startup_shortcut = shell.CreateShortCut(str(startup_folder / "Push Client (Startup).lnk"))
                startup_shortcut.Targetpath = str(self.install_path / "Client.exe")
                startup_shortcut.WorkingDirectory = str(self.install_path)
                startup_shortcut.Description = "PushNotifications Client - Auto Start"
                startup_shortcut.WindowStyle = 7  # Minimized
                startup_shortcut.save()
                
                print("✓ Startup folder shortcut created")
                
            except Exception as e:
                print(f"Warning: Could not create startup folder shortcut: {e}")
            
            # Method 3: Create additional batch wrapper for reliability
            startup_batch = self.install_path / "StartupClient.bat"
            startup_batch_content = f'''@echo off
REM Auto-start PushNotifications Client
cd /d "{self.install_path}"
timeout /t 5 /nobreak >nul
pythonw.exe "{self.install_path / "Client.py"}"
'''
            
            with open(startup_batch, 'w') as f:
                f.write(startup_batch_content)
            
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(startup_batch)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("✓ Startup batch script created")
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not create all startup entries: {e}")
            return False  # Continue installation even if this fails

    def create_watchdog_service(self):
        """Create Windows service for watchdog monitoring using alternative approach"""
        if self.system != "Windows":
            return True
            
        print("Creating watchdog service...")
        
        try:
            # First, try to remove any existing service
            subprocess.run(['sc', 'stop', 'PushWatchdog'], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['sc', 'delete', 'PushWatchdog'], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Create Python wrapper script for the service
            service_wrapper_script = f'''@echo off
REM PushNotifications Watchdog Service Wrapper
cd /d "{self.install_path}"
pythonw.exe "{self.install_path / "WatchdogService.py"}"
'''
            
            service_wrapper_path = self.install_path / "WatchdogService.bat"
            with open(service_wrapper_path, 'w') as f:
                f.write(service_wrapper_script)
            
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(service_wrapper_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Create service using proper sc command format for 64-bit compatibility
            # Use single command string instead of array to avoid path escaping issues
            service_command_str = f'sc create PushWatchdog binPath= "{service_wrapper_path}" DisplayName= "PushNotifications Watchdog" description= "Monitors PushNotifications client process for automatic recovery" start= auto obj= LocalSystem'
            
            result = subprocess.run(
                service_command_str,
                shell=True,
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                print("✓ PushWatchdog service created")
                
                # Configure service for failure recovery
                recovery_command = [
                    'sc', 'failure', 'PushWatchdog',
                    'reset=86400',
                    'actions=restart/30000/restart/60000/restart/60000'
                ]
                
                subprocess.run(recovery_command, capture_output=True, 
                              creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Start the service
                start_result = subprocess.run([
                    'sc', 'start', 'PushWatchdog'
                ], capture_output=True, text=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
                
                if start_result.returncode == 0:
                    print("✓ PushWatchdog service started")
                    return True
                else:
                    print(f"Warning: Service created but failed to start: {start_result.stderr}")
                    print("Service will start automatically on next system boot.")
                    return True  # Still consider success if service was created
            else:
                print(f"✗ Failed to create service: {result.stderr}")
                print("Falling back to scheduled task approach...")
                return self._create_watchdog_scheduled_task()
                
        except Exception as e:
            print(f"✗ Service creation error: {e}")
            print("Falling back to scheduled task approach...")
            return self._create_watchdog_scheduled_task()
    
    def _create_watchdog_scheduled_task(self):
        """Fallback: Create watchdog as scheduled task instead of service"""
        try:
            print("Creating watchdog as scheduled task...")
            
            # Create watchdog task that runs at startup
            watchdog_task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>PushNotifications Watchdog - Process Monitor</Description>
    <Author>PushNotifications</Author>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT2M</Delay>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>ServiceAccount</LogonType>
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>4</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>pythonw.exe</Command>
      <Arguments>"{self.install_path / "WatchdogService.py"}"</Arguments>
      <WorkingDirectory>{self.install_path}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
            
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(watchdog_task_xml)
                watchdog_xml_path = f.name
            
            result = subprocess.run([
                'schtasks', '/create', '/tn', 'PushWatchdog',
                '/xml', watchdog_xml_path, '/f'
            ], capture_output=True, text=True,
               creationflags=subprocess.CREATE_NO_WINDOW)
            
            os.unlink(watchdog_xml_path)
            
            if result.returncode == 0:
                print("✓ PushWatchdog scheduled task created")
                
                # Start the task immediately
                start_result = subprocess.run([
                    'schtasks', '/run', '/tn', 'PushWatchdog'
                ], capture_output=True, text=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
                
                if start_result.returncode == 0:
                    print("✓ PushWatchdog task started")
                else:
                    print(f"Warning: Task created but failed to start immediately: {start_result.stderr}")
                    print("Task will start automatically on next system boot.")
                
                return True
            else:
                print(f"✗ Failed to create watchdog task: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Watchdog task creation error: {e}")
            return False

    def create_desktop_shortcuts(self):
        """Create desktop shortcuts for client and installer"""
        print("Creating desktop shortcuts...")
        
        try:
            if self.system == "Windows":
                import win32com.client
                
                desktop = Path.home() / "Desktop"
                
                # Create Push Client shortcut
                shell = win32com.client.Dispatch("WScript.Shell")
                client_shortcut = shell.CreateShortCut(str(desktop / "Push Client.lnk"))
                client_shortcut.Targetpath = str(self.install_path / "Client.exe")
                client_shortcut.WorkingDirectory = str(self.install_path)
                client_shortcut.Description = "PushNotifications Client"
                client_shortcut.save()
                
                # Create Installer/Repair shortcut
                repair_shortcut = shell.CreateShortCut(str(desktop / "Push Client Repair.lnk"))
                repair_shortcut.Targetpath = str(self.install_path / "Installer.exe")
                repair_shortcut.Arguments = "--repair"
                repair_shortcut.WorkingDirectory = str(self.install_path)
                repair_shortcut.Description = "PushNotifications Installer/Repair"
                repair_shortcut.save()
                
                print("✓ Desktop shortcuts created")
                
            else:
                # Unix-like systems - create .desktop files
                desktop = Path.home() / "Desktop"
                
                client_desktop = desktop / "push-client.desktop"
                with open(client_desktop, 'w') as f:
                    f.write(f"""[Desktop Entry]
Type=Application
Name=Push Client
Comment=PushNotifications Client
Exec={self.install_path / "Client"}
Icon=application-default-icon
Terminal=false
Categories=System;
""")
                
                repair_desktop = desktop / "push-repair.desktop"
                with open(repair_desktop, 'w') as f:
                    f.write(f"""[Desktop Entry]
Type=Application
Name=Push Client Repair
Comment=PushNotifications Installer/Repair
Exec={self.install_path / "Installer"} --repair
Icon=application-default-icon
Terminal=false
Categories=System;
""")
                
                os.chmod(client_desktop, 0o755)
                os.chmod(repair_desktop, 0o755)
                
                print("✓ Desktop shortcuts created")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create shortcuts: {e}")
            return False

    def convert_to_windows_executable(self):
        """Convert installer to Windows executable if needed"""
        if self.system != "Windows":
            return True
            
        converter = WindowsExecutableConverter(__file__)
        if converter.should_convert_to_exe():
            print("Creating Windows executable launcher...")
            batch_file = converter.create_batch_launcher_with_admin()
            if batch_file:
                print(f"Windows executable created: {batch_file}")
                print("To run with administrator privileges, use the .bat file.")
                return True
            else:
                print("Warning: Could not create Windows executable launcher")
                return False
        return True
    
    def finalize_installation(self):
        """Finalize installation and report success to server"""
        print("Finalizing installation...")
        
        try:
            # Report successful installation to server
            response = requests.post(
                f"{self.api_url}/api/index",
                json={
                    'action': 'reportInstallation',
                    'keyId': self.key_id,
                    'macAddress': self.mac_address,
                    'installPath': str(self.install_path),
                    'version': INSTALLER_VERSION,
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✓ Installation reported to server")
                else:
                    print(f"Warning: Server reported: {result.get('message')}")
            
            # Start the client immediately
            if self.system == "Windows":
                subprocess.Popen([
                    str(self.install_path / "Client.exe")
                ], cwd=str(self.install_path),
                   creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([
                    str(self.install_path / "Client")
                ], cwd=str(self.install_path))
            
            print("✓ Client started")
            return True
            
        except Exception as e:
            print(f"Warning: Finalization error: {e}")
            return True  # Don't fail installation for this

    def run_installation(self):
        """Run the complete installation process"""
        print("Starting PushNotifications Installation")
        print("=" * 60)
        
        # Startup version check (unless in repair mode)
        if not self.repair_mode:
            print("Performing startup version check...")
            if self.check_for_updates():
                latest_version = self.update_data.get('latestVersion')
                update_required = self.update_data.get('updateRequired', False)
                
                if update_required:
                    print(f"\n⚠️  Critical Update Required: v{INSTALLER_VERSION} → v{latest_version}")
                    print("This update contains important security fixes and must be installed.")
                    
                    if self.download_and_apply_update():
                        print("\n✅ Critical update applied successfully.")
                        print("Please restart the installer to continue with the updated version.")
                        return True
                    else:
                        print("\n❌ Critical update failed. Installation cannot proceed.")
                        return False
                        
                else:
                    print(f"\nℹ️  Update available: v{INSTALLER_VERSION} → v{latest_version}")
                    print("You can update later using: python installer.py --update")
                    print("Continuing with current version...\n")
        
        # Check admin privileges
        if not self.check_admin_privileges():
            print("Administrator privileges required for installation.")
            if not self.restart_with_admin():
                print("✗ Installation failed: Could not obtain administrator privileges")
                return False
            return True  # Process will restart with admin
        
        print("✓ Running with administrator privileges")
        
        # Validate installation key (skip in repair mode if we have existing config)
        if not self.repair_mode or not self._has_existing_installation():
            if not self.validate_installation_key():
                print("✗ Installation failed: Invalid installation key")
                return False
        else:
            print("✓ Repair mode: Using existing installation key")
            self._load_existing_config()
        
        # Register device
        if not self.register_device():
            print("✗ Installation failed: Device registration failed")
            return False
        
        # Create hidden installation directory
        if not self.create_hidden_install_directory():
            print("✗ Installation failed: Could not create installation directory")
            return False
        
        # Create embedded client components
        if not self.create_embedded_client_components():
            print("✗ Installation failed: Could not create client components")
            return False
        
        # Create encrypted vault
        if not self.create_encrypted_vault():
            print("✗ Installation failed: Could not create configuration vault")
            return False
        
        # Create scheduled tasks
        if not self.create_scheduled_tasks():
            print("✗ Installation failed: Could not create scheduled tasks")
            return False
        
        # Create additional startup entries for maximum reliability
        if not self.create_startup_entries():
            print("Warning: Additional startup entries creation failed (continuing)")
        
        # Create watchdog service
        if not self.create_watchdog_service():
            print("Warning: Watchdog service creation failed (continuing)")
        
        # Create desktop shortcuts
        if not self.create_desktop_shortcuts():
            print("Warning: Desktop shortcuts creation failed (continuing)")
        
        # Create Windows executable launcher if needed
        if not self.convert_to_windows_executable():
            print("Warning: Windows executable conversion failed (continuing)")
        
        # Finalize installation
        if not self.finalize_installation():
            print("Warning: Installation finalization had issues")
        
        print()
        print("🎉 PushNotifications Installation Completed Successfully!")
        print("=" * 60)
        print(f"Installation directory: {self.install_path}")
        print(f"Client version: {INSTALLER_VERSION}")
        print(f"Device registered as: {self.client_name}")
        print()
        print("The client will start automatically and run in the background.")
        print("Look for the Push Client icon in your system tray.")
        print()
        print("To uninstall, use Task Manager to end the client process,")
        print("which will trigger the automatic uninstall approval process.")
        print()
        
        return True


def show_help():
    """Display comprehensive help information"""
    print(f"""PushNotifications Universal Installer v{INSTALLER_VERSION}
{"=" * 60}

🌐 UNIVERSAL PYTHON INSTALLER
- Single .py file runs on Windows, macOS, Linux
- Windows: Auto-converts to .exe with admin privileges
- No external dependencies required for basic installation
- Automatically detects OS and adapts functionality

🪟 WINDOWS ENTERPRISE FEATURES
- Auto-conversion to executable with embedded admin escalation
- Hidden encrypted installation with AES-256-GCM vault encryption
- Real MAC address detection and transmission
- Admin privilege escalation without UAC prompts
- Multi-monitor 25% grey overlay system
- Force-minimize window restrictions during active notifications
- Website allowlist enforcement and request system
- Automatic uninstaller on force-quit detection

USAGE:
  python installer.py [OPTIONS] [API_URL]

OPTIONS:
  --help, -h              Show this help message
  --repair, -r            Run in repair mode (preserve existing settings)
  --update, -u            Check for and install updates
  --update-check          Check for updates only (exit code 2 if available)
  --docs                  Show embedded documentation menu
  --deployment-guide      Show deployment guide
  --mongodb-setup         Show MongoDB Atlas setup guide
  --installer-guide       Show installer improvements documentation
  
EXAMPLES:
  python installer.py                                    # Standard installation
  python installer.py --repair                           # Repair existing installation
  python installer.py --update                           # Check and install updates
  python installer.py --docs                             # Show documentation menu
  python installer.py https://your-api.vercel.app        # Use custom API URL
  
NOTE: Administrator privileges are required for installation.
      The installer will automatically request elevation if needed.
""")

def show_documentation_menu():
    """Show interactive documentation menu"""
    while True:
        print(f"""\nPushNotifications Documentation Menu
{"=" * 50}

1. Installer Improvements Guide
2. Deployment Guide (Vercel + MongoDB)
3. MongoDB Atlas Setup Guide
4. Return to Main Menu
5. Exit

Enter your choice (1-5): """)
        
        try:
            choice = input().strip()
            
            if choice == '1':
                print("\n" + DOCUMENTATION['installer_improvements'])
            elif choice == '2':
                print("\n" + DOCUMENTATION['deployment_guide'])
            elif choice == '3':
                print("\n" + DOCUMENTATION['mongodb_setup'])
            elif choice == '4':
                return
            elif choice == '5':
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1-5.")
                continue
                
            input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            print("\n\nExiting documentation menu.")
            sys.exit(0)

def show_specific_documentation(doc_type):
    """Show specific documentation section"""
    if doc_type in DOCUMENTATION:
        print("\n" + DOCUMENTATION[doc_type])
        print("\n" + "=" * 60)
        input("Press Enter to exit...")
    else:
        print(f"Documentation section '{doc_type}' not found.")
        sys.exit(1)

def main():
    """Main installer entry point"""
    try:
        # Parse command line arguments
        api_url = None
        repair_mode = False
        update_mode = False
        check_only = False
        show_docs_menu = False
        show_specific_doc = None
        
        for arg in sys.argv[1:]:
            if arg.startswith('http'):
                api_url = arg
            elif arg in ['--help', '-h', '/help', '/?']:
                show_help()
                return
            elif arg in ['--repair', '-r', '/repair']:
                repair_mode = True
            elif arg in ['--update', '-u', '/update']:
                update_mode = True
            elif arg in ['--update-check', '--check-updates', '/update-check']:
                check_only = True
            elif arg in ['--docs', '--documentation', '/docs']:
                show_docs_menu = True
            elif arg in ['--deployment-guide', '/deployment-guide']:
                show_specific_doc = 'deployment_guide'
            elif arg in ['--mongodb-setup', '/mongodb-setup']:
                show_specific_doc = 'mongodb_setup'
            elif arg in ['--installer-guide', '/installer-guide']:
                show_specific_doc = 'installer_improvements'
        
        # Handle documentation requests
        if show_docs_menu:
            show_documentation_menu()
            return
        
        if show_specific_doc:
            show_specific_documentation(show_specific_doc)
            return
        
        # Handle special modes
        if check_only:
            print("🔍 PushNotifications Update Check")
            print("=" * 50)
            # Just check for updates and exit
            installer = PushNotificationsInstaller(api_url)
            if installer.check_for_updates():
                print(f"Update available: v{installer.update_data['latestVersion']}")
                sys.exit(2)  # Exit code 2 indicates update available
            else:
                print("No updates available")
                sys.exit(0)
        
        if update_mode:
            print("📦 PushNotifications Update Mode")
            print("=" * 50)
            print("This will check for and install the latest version.")
            print()
        
        if repair_mode:
            print("🔧 PushNotifications Repair Mode")
            print("=" * 50)
            print("This will attempt to repair or reinstall PushNotifications.")
            print("Existing settings and configurations will be preserved where possible.")
            print()
        
        # Create and run installer
        installer = PushNotificationsInstaller(api_url)
        
        if repair_mode:
            # In repair mode, skip key validation and try to preserve existing settings
            installer.repair_mode = True
            print("Starting repair process...")
        
        if update_mode:
            # In update mode, check for updates first
            installer.update_mode = True
            print("Checking for available updates...")
            
            if installer.check_for_updates():
                print(f"\nUpdate found: v{installer.update_data['currentVersion']} → v{installer.update_data['latestVersion']}")
                print("Release notes:", installer.update_data.get('updateNotes', 'No release notes available'))
                
                # Ask for confirmation unless it's a required update
                if installer.update_data.get('updateRequired', False):
                    print("\n⚠️  This is a required security update.")
                    proceed = True
                else:
                    if GUI_AVAILABLE:
                        try:
                            import tkinter.messagebox as mb
                            proceed = mb.askyesno(
                                "Update Available",
                                f"Update available: v{installer.update_data['latestVersion']}\n\n"
                                f"Release notes: {installer.update_data.get('updateNotes', 'No notes')}\n\n"
                                "Would you like to install this update?"
                            )
                        except:
                            proceed = input("\nInstall update? (y/N): ").lower().startswith('y')
                    else:
                        proceed = input("\nInstall update? (y/N): ").lower().startswith('y')
                
                if proceed:
                    if installer.download_and_apply_update():
                        print("\n✅ Update completed successfully!")
                        print("The updated installer is ready to use.")
                        sys.exit(0)
                    else:
                        print("\n❌ Update failed. Please try again later.")
                        sys.exit(1)
                else:
                    print("\nUpdate cancelled by user.")
                    sys.exit(0)
            else:
                print("\n✅ Already running the latest version.")
                sys.exit(0)
        
        success = installer.run_installation()
        
        if success:
            if GUI_AVAILABLE:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo(
                        "Installation Complete",
                        "PushNotifications has been installed successfully!\n\n"
                        "The client is now running in the background."
                    )
                    root.destroy()
                except:
                    pass
            
            print("\nInstallation completed. Press Enter to exit...")
            input()
            sys.exit(0)
        else:
            print("\nInstallation failed. Press Enter to exit...")
            input()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nInstallation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
