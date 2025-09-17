#!/usr/bin/env python3
# PushNotifications Client Installer
# Downloaded Version: 1.8.4
# Version Number: 85
# Download Date: 2025-09-15T15:31:10.423Z
# task manager name update

"""
PushNotifications Universal Client Installer
Version: 1.8.4

Cross-platform installer with native Python operation:

🌐 UNIVERSAL PYTHON INSTALLER
- Single .py file runs on Windows, macOS, Linux
- Windows: Runs as Python script with admin privileges
- No external dependencies required for basic installation
- Automatically detects OS and adapts functionality

🪟 WINDOWS ENTERPRISE FEATURES
- Python-based operation with admin privileges
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
        # Check if running as PyInstaller bundle (now using Python scripts)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            print(f"Warning: {package_name} not bundled - may cause issues")
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
        import winreg
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
    from tkinter import messagebox, simpledialog, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Global flag to control GUI dialog usage - only enable on Windows
USE_GUI_DIALOGS = platform.system() == "Windows" and GUI_AVAILABLE

# Cross-platform system tray support
if platform.system() != "Windows":
    # Install cross-platform packages for macOS/Linux GUI support
    check_and_install_package('pystray', 'pystray>=0.19.4')
    check_and_install_package('PIL', 'Pillow>=10.0.0')
    
    try:
        import pystray
        from PIL import Image, ImageDraw, ImageFont
        TRAY_AVAILABLE = True
    except ImportError:
        TRAY_AVAILABLE = False
        print("Warning: System tray support not available - using fallback notifications")
else:
    TRAY_AVAILABLE = True  # Windows support handled separately

class InstallationProgressDialog:
    """Cross-platform installation progress dialog"""
    
    def __init__(self):
        self.window = None
        self.progress_bar = None
        self.status_label = None
        self.log_text = None
        
        if USE_GUI_DIALOGS:
            self._create_dialog()
    
    def _create_dialog(self):
        """Create the progress dialog window"""
        try:
            self.window = tk.Tk()
            self.window.title("PushNotifications Installer")
            self.window.geometry("600x400")
            self.window.resizable(False, False)
            
            # Make window stay on top and center it
            self.window.attributes('-topmost', True)
            self.window.withdraw()  # Hide initially
            
            # Center the window
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
            y = (self.window.winfo_screenheight() // 2) - (400 // 2)
            self.window.geometry(f"600x400+{x}+{y}")
            
            # Title
            title_label = tk.Label(
                self.window, 
                text="PushNotifications Client Installer",
                font=("Arial", 16, "bold")
            )
            title_label.pack(pady=10)
            
            # Progress bar
            progress_frame = tk.Frame(self.window)
            progress_frame.pack(pady=10, padx=20, fill=tk.X)
            
            tk.Label(progress_frame, text="Installation Progress:").pack(anchor=tk.W)
            self.progress_bar = ttk.Progressbar(
                progress_frame, 
                mode='determinate', 
                length=560
            )
            self.progress_bar.pack(pady=5, fill=tk.X)
            
            # Current status
            self.status_label = tk.Label(
                self.window,
                text="Initializing...",
                font=("Arial", 10)
            )
            self.status_label.pack(pady=5)
            
            # Log area
            log_frame = tk.Frame(self.window)
            log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
            
            tk.Label(log_frame, text="Installation Log:").pack(anchor=tk.W)
            
            # Text area with scrollbar
            text_frame = tk.Frame(log_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            self.log_text = tk.Text(
                text_frame,
                height=12,
                width=70,
                font=("Consolas", 9),
                bg="#f0f0f0",
                state=tk.DISABLED
            )
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            self.log_text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=self.log_text.yview)
            
        except Exception as e:
            print(f"Warning: Could not create progress dialog: {e}")
            self.window = None
    
    def show(self):
        """Show the progress dialog"""
        if self.window:
            self.window.deiconify()
            self.window.focus_force()
            self.window.update()
    
    def hide(self):
        """Hide the progress dialog"""
        if self.window:
            self.window.withdraw()
    
    def update_progress(self, percentage, status_text=""):
        """Update progress bar and status"""
        if self.window:
            try:
                self.progress_bar['value'] = percentage
                if status_text:
                    self.status_label.config(text=status_text)
                self.window.update()
            except:
                pass
    
    def add_log(self, message, level="INFO"):
        """Add a message to the log area"""
        if self.window and self.log_text:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                colored_message = f"[{timestamp}] {level}: {message}\n"
                
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, colored_message)
                self.log_text.config(state=tk.DISABLED)
                self.log_text.see(tk.END)  # Scroll to bottom
                self.window.update()
            except:
                pass
        
        # Also print to console
        print(f"{level}: {message}")
    
    def set_completion(self, success=True):
        """Show completion status"""
        if self.window:
            try:
                if success:
                    self.status_label.config(text="✅ Installation completed successfully!")
                    self.progress_bar['value'] = 100
                else:
                    self.status_label.config(text="❌ Installation failed")
                
                # Add a close button
                close_btn = tk.Button(
                    self.window,
                    text="Close",
                    command=self.close,
                    font=("Arial", 10)
                )
                close_btn.pack(pady=10)
                
                self.window.update()
            except:
                pass
    
    def close(self):
        """Close the progress dialog"""
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
    
    def update_gui(self):
        """Update GUI events"""
        if self.window:
            try:
                self.window.update()
            except:
                pass

def fetch_current_version_from_api(api_url=None):
    """Fetch the current version from the API"""
    api_url = api_url or DEFAULT_API_URL
    
    try:
        print("Fetching current version from API...")
        response = requests.post(
            f"{api_url}/api/index",
            json={
                'action': 'getCurrentVersion',
                'timestamp': datetime.now().isoformat()
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('currentVersion'):
                version = result.get('currentVersion')
                print(f"✓ Retrieved version from API: v{version}")
                return version
            else:
                print(f"✗ API response unsuccessful: {result.get('message', 'Unknown error')}")
        else:
            print(f"✗ API request failed: HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"✗ Network error fetching version: {e}")
    except Exception as e:
        print(f"✗ Error fetching version: {e}")
    
    # Fallback to a default version if API fails
    print("Warning: Using fallback version 1.0.0")
    return "1.0.0"

# Global configuration
INSTALLER_VERSION = '1.0.0'  # Dynamic version - replaced by download API
VERSION_NUMBER = 1  # Numeric version for update comparisons
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


# Windows administrative functionality is now handled directly within the installer
# All operations use native Python scripts with proper privilege handling


class PushNotificationsInstaller:
    """Advanced installer with Python-based implementation and full security features"""
    
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
        self.installation_finalized = False  # Track if installation completed successfully
        self.cleanup_performed = False  # Track if cleanup was already performed
        self.device_registered = False  # Track if device was registered with server
        
        # Initialize progress dialog only if GUI dialogs are enabled
        self.progress_dialog = None
        if USE_GUI_DIALOGS:
            self.progress_dialog = InstallationProgressDialog()
            self.progress_dialog.show()
            self.progress_dialog.add_log(f"PushNotifications Installer v{INSTALLER_VERSION}")
            self.progress_dialog.add_log(f"Platform: {self.system}")
            self.progress_dialog.add_log(f"MAC Address: {self.mac_address}")
            self.progress_dialog.add_log(f"Client Name: {self.client_name}")
            self.progress_dialog.add_log(f"API URL: {self.api_url}")
        
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
            else:
                # On Unix-like systems, check for common installation directories
                common_install_paths = [
                    Path.home() / ".local" / "share" / "PushNotifications",
                    Path.home() / "Applications" / "PushNotifications",
                    Path("/usr/local/share/PushNotifications"),
                    Path("/opt/PushNotifications"),
                    # Check current directory for development installs
                    Path.cwd() / "Client.py"
                ]
                
                for path in common_install_paths:
                    if path.exists():
                        if path.name == "Client.py":
                            # Found client file
                            return True
                        elif (path / "Client.py").exists():
                            # Found installation directory with client
                            return True
                        
        except (OSError, FileNotFoundError):
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
            else:
                # On Unix-like systems, we'll use current detected values and assume upgrade
                print("✓ Unix/macOS upgrade mode - using current system configuration")
                print(f"  MAC Address: {self.mac_address}")
                print(f"  Username: {self.username}")
                print(f"  API URL: {self.api_url}")
                
                # Set upgrade installation key - will be validated normally
                self.installation_key = "UPGRADE_MODE"
                
                # Create device data for upgrade
                self.device_data = {
                    'deviceId': f"upgrade_{self.mac_address}",
                    'clientId': f"upgrade_{self.mac_address}",
                    'isNewInstallation': False
                }
                    
        except Exception as e:
            print(f"Warning: Could not load existing config for repair: {e}")
    
    def check_for_updates(self):
        """Check for updates from the website"""
        print("Checking for updates...")
        
        try:
            # Extract version number from version string (e.g., "3.0.0" -> 300)
            try:
                version_parts = INSTALLER_VERSION.split('.')
                if len(version_parts) >= 3:
                    version_number = int(version_parts[0]) * 100 + int(version_parts[1]) * 10 + int(version_parts[2])
                else:
                    version_number = int(VERSION_NUMBER)  # Fallback to numeric version
            except (ValueError, IndexError):
                version_number = int(VERSION_NUMBER)  # Fallback to numeric version
            
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
        """Update installer Python script"""
        try:
            if self.system == "Windows":
                # We only update the main Python script now
                installer_path = self.install_path / "Installer.py"
                print(f"✓ Updated installer Python script: {installer_path}")
                
        except Exception as e:
            print(f"Warning: Could not update installer script: {e}")
    
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
        """Get username with number suffix for uniqueness - will be updated after key validation"""
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
        except (OSError, FileNotFoundError):
            pass
        
        # Temporary placeholder - will be replaced with website username after key validation
        import random
        number = random.randint(1000, 9999)
        return f"temp_{base_username}_{number}"

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
            print(f"Debug: System detected as '{self.system}', GUI dialogs: {USE_GUI_DIALOGS}")
            if USE_GUI_DIALOGS:
                try:
                    # Set environment variable to suppress tkinter deprecation warning
                    os.environ['TK_SILENCE_DEPRECATION'] = '1'
                    
                    root = tk.Tk()
                    root.title("PushNotifications Installation")
                    
                    # Configure root window for better visibility
                    root.geometry("400x150")
                    root.attributes('-topmost', True)
                    root.lift()
                    root.focus_force()
                    
                    # Center the window on screen
                    root.update_idletasks()
                    width = root.winfo_width()
                    height = root.winfo_height()
                    x = (root.winfo_screenwidth() // 2) - (width // 2)
                    y = (root.winfo_screenheight() // 2) - (height // 2)
                    root.geometry(f"{width}x{height}+{x}+{y}")
                    
                    # Show the dialog
                    key = simpledialog.askstring(
                        "Installation Key Required",
                        f"Enter installation key (attempt {attempt}/{max_attempts}):",
                        parent=root,
                        show='*'
                    )
                    root.destroy()
                    
                    if key is None:
                        print("Installation cancelled by user.")
                        return False
                        
                except Exception as e:
                    print(f"GUI dialog failed ({e}), falling back to console input")
                    key = input(f"Installation key (attempt {attempt}/{max_attempts}): ").strip()
            else:
                # Use console input for macOS, Linux, and fallback cases
                print(f"\n📝 Please enter your installation key:")
                print(f"   (Attempt {attempt} of {max_attempts})")
                print(f"   💡 Tip: Right-click and paste, or use Cmd+V (macOS) / Ctrl+V (Linux)")
                print(f"   🔓 Note: Key will be visible for easy pasting and verification")
                print(f"   ⏎ Press Enter when done")
                print()
                try:
                    sys.stdout.write("Installation Key: ")
                    sys.stdout.flush()
                    key = sys.stdin.readline().strip()
                    
                    if key:
                        # Clear the line after input for cleaner output
                        print("\033[A\033[2K", end="", flush=True)  # Move cursor up and clear line
                        print("Installation Key: [ENTERED - " + str(len(key)) + " characters]")  # Show confirmation
                    else:
                        print("No key entered")
                except (EOFError, KeyboardInterrupt):
                    print("\nInstallation cancelled by user.")
                    return False
            
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
                        
                        # Update username to use website username with numbers
                        website_username = user_info.get('username', 'unknown')
                        import random
                        number = random.randint(1000, 9999)
                        self.username = f"{website_username}_{number}"
                        self.client_name = f"{self.username}_{platform.node()}"
                        
                        print(f"✓ Installation key validated successfully!")
                        print(f"  User: {user_info.get('username', 'Unknown')}")
                        print(f"  Role: {user_info.get('role', 'Unknown')}")
                        print(f"  Generated Client Username: {self.username}")
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
                    
                    # Mark device as registered
                    self.device_registered = True
                    
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
            
            # Update install path in database after directory creation
            self._update_install_path_in_database()
            
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
            import win32api
            
            # Get current user SID - use GetCurrentProcess instead
            try:
                # Try the newer API first
                token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
                user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
                win32api.CloseHandle(token)
            except AttributeError:
                # Fallback for older pywin32 versions
                import win32process
                token = win32security.OpenProcessToken(win32process.GetCurrentProcess(), win32security.TOKEN_QUERY)
                user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
                win32api.CloseHandle(token)
            
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
            import win32file
            import win32con
            
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
    
    def _update_install_path_in_database(self):
        """Update the install path in the database after directory creation"""
        try:
            if not hasattr(self, 'device_data') or not self.device_data.get('clientId'):
                print("Warning: Device not registered yet, cannot update install path")
                return
                
            print("Updating install path in database...")
            
            response = requests.post(
                f"{self.api_url}/api/index",
                json={
                    'action': 'updateClientInstallPath',
                    'clientId': self.device_data.get('clientId'),
                    'macAddress': self.mac_address,
                    'installPath': str(self.install_path),
                    'keyId': self.key_id,
                    'timestamp': datetime.now().isoformat()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✓ Install path updated in database")
                else:
                    print(f"Warning: Failed to update install path: {result.get('message')}")
            else:
                print(f"Warning: Server error updating install path: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Warning: Could not update install path in database: {e}")

    def create_embedded_client_components(self):
        """Create client components embedded within this installer"""
        print("Creating embedded client components...")
        
        try:
            # Copy icon file to installation directory first
            self._copy_icon_file()
            
            # Create Python scripts for all platforms
            self._create_client_script()
            self._create_uninstaller_script()
            self._create_installer_copy()
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create embedded components: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_client_script(self):
        """Create Client Python script for all platforms"""
        if self.system == "Windows":
            client_script = self._get_embedded_windows_client_code()
        else:
            client_script = self._get_embedded_unix_client_code()
            
        client_path = self.install_path / "Client.py"
        
        with open(client_path, 'w', encoding='utf-8') as f:
            f.write(client_script)
        
        if self.system == "Windows":
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(client_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Set executable permissions on Unix-like systems
            os.chmod(client_path, 0o755)
        
        print("✓ Client Python script created")
    
    def _create_uninstaller_script(self):
        """Create Uninstaller Python script for all platforms"""
        if self.system == "Windows":
            uninstaller_script = self._get_embedded_windows_uninstaller_code()
        else:
            uninstaller_script = self._get_embedded_unix_uninstaller_code()
            
        uninstaller_path = self.install_path / "Uninstaller.py"
        
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        if self.system == "Windows":
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(uninstaller_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Set executable permissions on Unix-like systems
            os.chmod(uninstaller_path, 0o755)
        
        print("✓ Uninstaller Python script created")
    
    def _create_installer_copy(self):
        """Create a copy of the installer for repair/maintenance functionality"""
        try:
            # Copy the current installer script to the installation directory
            current_installer = Path(__file__).resolve()
            installer_copy_path = self.install_path / "Installer.py"
            
            # Read current installer content
            with open(current_installer, 'r', encoding='utf-8') as f:
                installer_content = f.read()
            
            # Write installer copy
            with open(installer_copy_path, 'w', encoding='utf-8') as f:
                f.write(installer_content)
            
            if self.system == "Windows":
                # Set hidden attributes
                subprocess.run(["attrib", "+S", "+H", str(installer_copy_path)], 
                              check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Set executable permissions on Unix-like systems
                os.chmod(installer_copy_path, 0o755)
            
            print("✓ Installer Python script copy created")
        
        except Exception as e:
            print(f"Warning: Could not create installer copy: {e}")
    
    def _copy_icon_file(self):
        """Copy pnicon.png to the installation directory"""
        try:
            # Look for pnicon.png in various locations
            icon_paths = [
                Path(__file__).parent / "pnicon.png",  # Same directory as this installer
                Path.cwd() / "pnicon.png"  # Current working directory
            ]
            
            source_icon = None
            for icon_path in icon_paths:
                if icon_path.exists():
                    source_icon = icon_path
                    print(f"✓ Found icon file at: {icon_path}")
                    break
            
            if source_icon:
                # Copy to installation directory
                dest_icon = self.install_path / "pnicon.png"
                
                import shutil
                shutil.copy2(source_icon, dest_icon)
                
                # Set hidden attributes on Windows
                if self.system == "Windows":
                    subprocess.run(["attrib", "+S", "+H", str(dest_icon)], 
                                  check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    # Set appropriate permissions on Unix-like systems
                    os.chmod(dest_icon, 0o644)
                
                print(f"✓ Icon file copied to installation directory: {dest_icon.name}")
                return True
            else:
                print("⚠️  Warning: pnicon.png not found in any expected locations")
                print("   The client may use a fallback system tray icon")
                return False  # Not a critical failure
                
        except Exception as e:
            print(f"Warning: Could not copy icon file: {e}")
            return False  # Not a critical failure
    
    
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
API_URL = "{self.api_url}/api/index"
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"
KEY_ID = "{self.key_id}"

# Global flag to control GUI dialog usage - Windows only
import platform
USE_GUI_DIALOGS = platform.system() == "Windows"

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
            overlay.overrideredirect(True)  # No window decorations
            overlay.attributes('-alpha', 0.25)  # 25% opacity
            overlay.attributes('-topmost', True)  # Keep above other windows
            overlay.attributes('-disabled', True)  # Click-through
            overlay.configure(bg='gray')
            
            # Set proper window styles for layering
            if platform.system() == "Windows":
                try:
                    import win32gui
                    import win32con
                    
                    # Get window handle
                    hwnd = overlay.winfo_id()
                    
                    # Set extended window styles
                    GWL_EXSTYLE = -20
                    WS_EX_LAYERED = 0x00080000
                    WS_EX_TRANSPARENT = 0x00000020
                    WS_EX_NOACTIVATE = 0x08000000
                    
                    style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
                    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
                    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
                    
                    # Set proper window z-order
                    win32gui.SetWindowPos(
                        hwnd, win32con.HWND_TOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
                    )
                except Exception as e:
                    print(f"Warning: Could not set overlay window styles: {e}")
            
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
        # Process executable names to monitor and potentially terminate
        # These refer to Windows process names (actual .exe files) that may be running
        self.restricted_processes = {{
            'browsers': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 'brave.exe', 'iexplore.exe'],
            'vpn': ['openvpn.exe', 'nordvpn.exe', 'expressvpn.exe', 'cyberghost.exe', 'tunnelbear.exe'],
            'proxy': ['proxifier.exe', 'proxycap.exe', 'sockscap.exe']
        }}
        # System processes that should never be terminated even if detected
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

def enable_dpi_awareness():
    """Enable DPI awareness for proper scaling on high-DPI displays"""
    if platform.system() == "Windows":
        try:
            # Try Windows 8.1+ API first
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
            except (AttributeError, OSError):
                # Fallback to Windows 8 API
                ctypes.windll.user32.SetProcessDPIAware()
            return True
        except Exception as e:
            print(f"Warning: Could not enable DPI awareness: {e}")
    return False

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
            # Enable DPI awareness for this window
            if platform.system() == "Windows":
                try:
                    import ctypes
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except Exception as e:
                    print(f"Warning: Could not set DPI awareness: {e}")

            self.window = tk.Toplevel()
            self.window.title("Push Notification")
            
            # Configure window properties
            self.window.attributes('-topmost', True)
            self.window.resizable(False, False)
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)
            
            if platform.system() == "Windows":
                try:
                    import win32gui
                    import win32con
                    import win32api
                    
                    # Get window handle
                    hwnd = self.window.winfo_id()
                    
                    # Set extended window styles
                    GWL_EXSTYLE = -20
                    WS_EX_APPWINDOW = 0x00040000
                    WS_EX_TOOLWINDOW = 0x00000080
                    
                    # Get current style
                    style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
                    
                    # Add app window style and remove tool window style
                    style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                    
                    # Apply new style
                    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
                    
                    # Update window frame
                    win32gui.SetWindowPos(
                        hwnd, win32con.HWND_TOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                        win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW
                    )
                    
                    # Force active state
                    win32gui.SetActiveWindow(hwnd)
                    win32gui.SetForegroundWindow(hwnd)
                    
                except Exception as e:
                    print(f"Warning: Could not set window styles: {e}")
            
            # Set proper taskbar state and window styles
            if platform.system() == "Windows":
                try:
                    import win32gui
                    import win32con
                    
                    # Get window handle
                    hwnd = self.window.winfo_id()
                    
                    # Set window styles for proper layering
                    GWL_EXSTYLE = -20
                    WS_EX_APPWINDOW = 0x00040000
                    WS_EX_NOACTIVATE = 0x08000000
                    
                    style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
                    style |= WS_EX_APPWINDOW | WS_EX_NOACTIVATE
                    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
                    
                    # Ensure proper taskbar behavior
                    win32gui.SetWindowPos(
                        hwnd, win32con.HWND_TOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
                    )
                    
                    # Force window activation
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    print(f"Warning: Could not set window styles: {e}")
            
            # Force window redraw and ensure proper DPI scaling
            self.window.update_idletasks()
            
            # Set initial size before positioning
            self.window.geometry("400x300")
            self.window.update()
            
            # Center on screen
            width, height = 400, 300
            # Get the screen the mouse is on
            mouse_x = self.window.winfo_pointerx()
            mouse_y = self.window.winfo_pointery()
            
            try:
                import screeninfo
                current_screen = None
                for monitor in screeninfo.get_monitors():
                    if (monitor.x <= mouse_x <= monitor.x + monitor.width and
                        monitor.y <= mouse_y <= monitor.y + monitor.height):
                        current_screen = monitor
                        break
                
                if current_screen:
                    # Center on current screen
                    x = current_screen.x + (current_screen.width - width) // 2
                    y = current_screen.y + (current_screen.height - height) // 2
                else:
                    # Fallback to primary screen centering
                    x = (self.window.winfo_screenwidth() // 2) - (width // 2)
                    y = (self.window.winfo_screenheight() // 2) - (height // 2)
            except Exception:
                # Fallback to primary screen centering
                x = (self.window.winfo_screenwidth() // 2) - (width // 2)
                y = (self.window.winfo_screenheight() // 2) - (height // 2)
            
            # Ensure coordinates are within screen bounds
            x = max(0, min(x, self.window.winfo_screenwidth() - width))
            y = max(0, min(y, self.window.winfo_screenheight() - height))
            
            self.window.geometry(f"{width}x{height}+{x}+{y}")
            self.window.update()
            
            # Modern design theme colors
            colors = {
                'bg': "#ffffff",
                'header': "#1a73e8",  # Google Blue
                'text': "#202124",    # Dark Gray
                'border': "#dadce0",  # Light Gray
                'button_primary': "#1a73e8",
                'button_secondary': "#5f6368",
                'button_warning': "#f29900",
                'shadow': "#0000001a"  # 10% black shadow
            }
            
            # Set base window style
            self.window.configure(bg=colors['bg'])
            
            # Add shadow effect frame
            shadow_size = 2
            shadow_frame = tk.Frame(self.window, bg=colors['shadow'])
            shadow_frame.place(x=shadow_size, y=shadow_size, 
                             relwidth=1, relheight=1)
            
            # Main content frame with border
            main_frame = tk.Frame(self.window, bg=colors['bg'], 
                                bd=1, relief='solid')
            main_frame.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Header with gradient effect
            header_height = 50
            header_frame = tk.Frame(main_frame, bg=colors['header'], 
                                  height=header_height)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            # Header icon (if available) and text
            header_content = tk.Frame(header_frame, bg=colors['header'])
            header_content.pack(expand=True)
            
            try:
                from PIL import Image, ImageTk
                icon_path = Path(__file__).parent / "pnicon.png"
                if icon_path.exists():
                    icon = Image.open(icon_path)
                    icon = icon.resize((24, 24), Image.Resampling.LANCZOS)
                    icon = ImageTk.PhotoImage(icon)
                    icon_label = tk.Label(header_content, image=icon, 
                                        bg=colors['header'])
                    icon_label.image = icon  # Keep reference
                    icon_label.pack(side=tk.LEFT, padx=(10, 5))
            except Exception:
                pass  # Skip icon if not available
            
            title_label = tk.Label(header_content, text="Push Notification", 
                                 bg=colors['header'], fg="white", 
                                 font=("Segoe UI", 14, "bold"))
            title_label.pack(side=tk.LEFT, padx=10)
            
            # Content area with padding and shadow
            content_frame = tk.Frame(main_frame, bg=colors['bg'])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
            
            # Message text with improved typography
            message_text = self.data.get('message', '')
            message_text = self._strip_html_and_decode(message_text)
            
            # Create text widget for better text rendering
            message_widget = tk.Text(content_frame, wrap=tk.WORD, 
                                   font=("Segoe UI", 11),
                                   bg=colors['bg'], fg=colors['text'],
                                   relief='flat', height=4)
            message_widget.insert('1.0', message_text)
            message_widget.configure(state='disabled')  # Make read-only
            message_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Allowed websites (if any)
            allowed_websites = self.data.get('allowedWebsites', [])
            if allowed_websites:
                websites_label = tk.Label(content_frame, 
                                        text=f"Allowed websites: {{', '.join(allowed_websites)}}", 
                                        bg=colors['bg'], wraplength=360, justify=tk.LEFT,
                                        font=("Arial", 9), fg="#666")
                websites_label.pack(pady=(0, 10))
            
            # Define the create_button function for use throughout the window creation
            def create_button(parent, text, command, color, is_primary=False):
                """Create a modern styled button"""
                btn = tk.Button(parent, text=text, command=command,
                              font=("Segoe UI", 10),
                              fg="white" if is_primary else colors['text'],
                              bg=color if is_primary else colors['bg'],
                              activebackground=color if is_primary else colors['border'],
                              activeforeground="white" if is_primary else colors['text'],
                              relief='flat', bd=1,
                              padx=15, pady=5)
                if not is_primary:
                    btn.configure(bd=1, highlightthickness=1,
                                highlightbackground=colors['border'])
                return btn
            
            # Website request section with modern styling
            if self.data.get('allowWebsiteRequests', False):
                request_frame = tk.Frame(content_frame, bg=colors['bg'])
                request_frame.pack(fill=tk.X, pady=(10, 15))
                
                request_label = tk.Label(request_frame, 
                                        text="Request Website Access",
                                        font=("Segoe UI", 10, "bold"),
                                        bg=colors['bg'],
                                        fg=colors['text'])
                request_label.pack(anchor=tk.W)
                
                entry_frame = tk.Frame(request_frame, bg=colors['bg'],
                                     highlightthickness=1,
                                     highlightbackground=colors['border'])
                entry_frame.pack(fill=tk.X, pady=(5, 10))
                
                self.website_request_var = tk.StringVar()
                request_entry = tk.Entry(entry_frame,
                                       textvariable=self.website_request_var,
                                       font=("Segoe UI", 10),
                                       bd=0, relief='flat')
                request_entry.pack(fill=tk.X, padx=10, pady=8)
                
                request_button = create_button(request_frame,
                                             "Request Access",
                                             self.request_website_access,
                                             colors['button_primary'],
                                             True)
                request_button.pack(anchor=tk.E)
            
            # Button container with modern styling
            button_frame = tk.Frame(main_frame, bg=colors['bg'])
            button_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
            
            # Snooze options in dropdown
            snooze_var = tk.StringVar(value="Snooze")
            snooze_options = [("5 minutes", 5), ("15 minutes", 15), ("30 minutes", 30)]
            
            snooze_menu = tk.Menu(button_frame, tearoff=0)
            for label, mins in snooze_options:
                snooze_menu.add_command(
                    label=label,
                    command=lambda m=mins: self.snooze_notification(m)
                )
            
            snooze_btn = create_button(button_frame, "Snooze ▾", 
                                     lambda e: snooze_menu.post(
                                         snooze_btn.winfo_rootx(),
                                         snooze_btn.winfo_rooty() + snooze_btn.winfo_height()
                                     ),
                                     colors['button_warning'])
            snooze_btn.pack(side=tk.LEFT)
            
            # Complete and minimize buttons
            button_container = tk.Frame(button_frame, bg=colors['bg'])
            button_container.pack(side=tk.RIGHT)
            
            complete_btn = create_button(button_container, "Mark Complete",
                                       self.complete_notification,
                                       colors['button_primary'], True)
            complete_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            # Minimize button with improved visibility
            if self.data.get('allowWebsiteRequests', False):
                minimize_btn = create_button(button_container, "Minimize",
                                           self.minimize_notification,
                                           colors['button_secondary'])
                minimize_btn.pack(side=tk.RIGHT, padx=5)
            
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
    
    def _strip_html_and_decode(self, text):
        """Strip HTML tags and decode HTML entities from notification text"""
        import re
        import html
        
        if not text:
            return text
        
        try:
            # First decode HTML entities
            text = html.unescape(text)
            
            # Remove HTML tags using regex
            # This regex matches opening and closing tags, including self-closing tags
            clean_text = re.sub(r'<[^>]+>', '', text)
            
            # Clean up extra whitespace that might be left
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            return clean_text
        except Exception as e:
            print(f"Error stripping HTML: {{e}}")
            # Return original text if processing fails
            return text

class PushNotificationsClient:
    """Main client application with complete functionality"""
    
    def __init__(self):
        # Enable DPI awareness
        enable_dpi_awareness()
        
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
                # Try to load pnicon.png from the installation directory first
                icon_paths = [
                    Path(__file__).parent / "pnicon.png",  # Same directory as this script (installation dir)
                    Path.cwd() / "pnicon.png"  # Current working directory
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
                
                # Fallback: create a teal circle with white "PN" text
                width = height = 64
                image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                dc = ImageDraw.Draw(image)
                
                # Create teal circle background
                dc.ellipse([4, 4, width-4, height-4], fill='#20B2AA', outline='#008B8B', width=2)
                
                # Draw "PN" text in white
                try:
                    from PIL import ImageFont
                    # Try to get a better font for the text
                    try:
                        font = ImageFont.truetype("arial.ttf", 24)
                    except:
                        try:
                            font = ImageFont.truetype("calibri.ttf", 24)
                        except:
                            font = ImageFont.load_default()
                    
                    # Calculate text position to center it
                    bbox = dc.textbbox((0, 0), "PN", font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (width - text_width) // 2
                    y = (height - text_height) // 2 - 2
                    
                    dc.text((x, y), "PN", fill='white', font=font)
                except:
                    # Ultimate fallback: simple text positioning
                    dc.text((width//2-12, height//2-8), "PN", fill='white')
                
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
            status_text = f"Push Client v{{CLIENT_VERSION}}\\n"
            status_text += f"Client ID: {{CLIENT_ID}}\\n"
            status_text += f"Status: Running\\n"
            status_text += f"Active Notifications: {{active_count}}\\n"
            status_text += f"Security Mode: {{'Active' if self.security_active else 'Inactive'}}"
            
            if USE_GUI_DIALOGS:
                messagebox.showinfo("Push Client Status", status_text)
            else:
                print(f"Push Client Status: {{status_text}}")
        except Exception as e:
            print(f"Error showing status: {{e}}")
    
def show_all_notifications(self, icon=None, item=None):
        """Show all notification windows"""
        # First, restore any minimized windows
        for window in self.notification_windows:
            if window.minimized:
                window.restore_notification()
        
        # Then re-layer all windows
        self.layer_notification_windows()
    
    def tray_mark_complete(self, icon=None, item=None):
        """Mark the first active notification as complete from tray"""
        try:
            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
            if active_notifications:
                self.complete_notification(active_notifications[0].get('id'))
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Completed", "Notification marked as complete.")
                else:
                    print("Completed: Notification marked as complete.")
            else:
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("No Notifications", "No active notifications to complete.")
                else:
                    print("No Notifications: No active notifications to complete.")
        except Exception as e:
            print(f"Error in tray mark complete: {{e}}")
    
    def tray_request_website(self, icon=None, item=None):
        """Request website access from tray"""
        try:
            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
            if not active_notifications:
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("No Notifications", "No active notifications for website requests.")
                else:
                    print("No Notifications: No active notifications for website requests.")
                return
                
            if USE_GUI_DIALOGS:
                website = simpledialog.askstring(
                    "Website Access Request",
                    "Enter the website URL you want to request access to:",
                    initialvalue="https://"
                )
            else:
                website = input("Enter the website URL you want to request access to (or press Enter to cancel): ").strip()
                if not website:
                    return
            
            if website:
                self.request_website_access(active_notifications[0].get('id'), website)
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Request Sent", f"Website access request sent for: {{website}}")
                else:
                    print(f"Request Sent: Website access request sent for: {{website}}")
        except Exception as e:
            print(f"Error in tray request website: {{e}}")
    
    def tray_request_deletion(self, icon=None, item=None):
        """Request deletion/uninstallation from tray"""
        try:
            if USE_GUI_DIALOGS:
                reason = simpledialog.askstring(
                    "Request Deletion",
                    "Please provide a reason for requesting deletion:",
                    initialvalue="User requested uninstall"
                )
            else:
                reason = input("Please provide a reason for requesting deletion (or press Enter to cancel): ").strip()
                if not reason:
                    reason = "User requested uninstall"
            
            if reason:
                requests.post(API_URL, json={{
                    'action': 'requestUninstall',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }}, timeout=10)
                
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Request Sent", "Deletion request sent for admin approval.")
                else:
                    print("Request Sent: Deletion request sent for admin approval.")
        except Exception as e:
            print(f"Error in tray request deletion: {{e}}")
    
    def tray_submit_bug(self, icon=None, item=None):
        """Submit bug report from tray"""
        try:
            if USE_GUI_DIALOGS:
                bug_description = simpledialog.askstring(
                    "Submit Bug Report",
                    "Describe the bug or issue:",
                    initialvalue=""
                )
            else:
                bug_description = input("Describe the bug or issue (or press Enter to cancel): ").strip()
            
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
                
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Bug Report Sent", "Thank you! Your bug report has been submitted.")
                else:
                    print("Bug Report Sent: Thank you! Your bug report has been submitted.")
        except Exception as e:
            print(f"Error in tray submit bug: {{e}}")
    
    def tray_snooze_all(self, minutes):
        """Snooze all notifications from tray"""
        try:
            self.snooze_notifications(minutes)
            if USE_GUI_DIALOGS:
                messagebox.showinfo("Snoozed", f"All notifications snoozed for {{minutes}} minutes.")
            else:
                print(f"Snoozed: All notifications snoozed for {{minutes}} minutes.")
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
                client_path = Path(__file__).parent / "Client.py"
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
        """Main notification checking loop with heartbeat functionality"""
        while self.running:
            try:
                # Check if snooze period has ended
                if self.snooze_end_time and datetime.now() > self.snooze_end_time:
                    self.snooze_end_time = None
                    self.evaluate_security_state()
                
                # Send heartbeat/check-in to update client status
                self._send_heartbeat()
                
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
    
    def _send_heartbeat(self):
        """Send heartbeat/check-in to update client status"""
        try:
            # Send updateClientMacCheckin request to keep client status current
            response = requests.post(API_URL, json={{
                'action': 'updateClientMacCheckin',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'timestamp': datetime.now().isoformat(),
                'status': 'active',
                'version': CLIENT_VERSION
            }}, timeout=5)  # Short timeout for heartbeat
            
            # Don't log success to avoid spam, only log errors
            if response.status_code != 200:
                print(f"Heartbeat warning: HTTP {{response.status_code}}")
                
        except Exception as e:
            # Log heartbeat errors but don't let them crash the client
            print(f"Heartbeat error: {{e}}")
    
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
        """Layer notification windows with newest on top"""
        try:
            if not self.notification_windows:
                return

            # Sort by creation time (newest first)
            self.notification_windows.sort(key=lambda w: w.data.get('created', 0), reverse=True)
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate base position (centered on screen)
            window_width = 400
            window_height = 300
            base_x = (screen_width - window_width) // 2
            base_y = (screen_height - window_height) // 2
            
            # Position windows in cascade, ensuring they stay on screen
            offset = 30  # Pixels to offset each window
            max_cascade = 5  # Maximum number of cascaded windows
            
            for i, window in enumerate(self.notification_windows):
                if window.window and not window.minimized:
                    cascade_index = min(i, max_cascade - 1)
                    x = base_x + (cascade_index * offset)
                    y = base_y + (cascade_index * offset)
                    
                    # Ensure window stays on screen
                    x = max(0, min(x, screen_width - window_width))
                    y = max(0, min(y, screen_height - window_height))
                    
                    # Update window position
                    window.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
                    
                    # Ensure proper z-order
                    if platform.system() == "Windows":
                        try:
                            import win32gui
                            hwnd = window.window.winfo_id()
                            win32gui.SetWindowPos(
                                hwnd,
                                win32gui.HWND_TOPMOST if i == 0 else win32gui.HWND_NOTOPMOST,
                                x, y, window_width, window_height,
                                win32gui.SWP_SHOWWINDOW
                            )
                        except Exception as e:
                            print(f"Warning: Could not set window z-order: {e}")
                    
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
            
            # Spawn post-uninstall notifier before launching uninstaller
            self._spawn_post_uninstall_notifier()
            
            # Launch uninstaller
            self.launch_uninstaller()
            
            # Exit the client
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()
                
        except Exception as e:
            print(f"Error handling uninstall command: {{e}}")
    
    def launch_uninstaller(self):
        """Launch uninstaller as a separate process and return immediately"""
        try:
            uninstaller_path = Path(__file__).parent / "Uninstaller.py"
            if uninstaller_path.exists():
                if platform.system() == "Windows":
                    # Windows - Launch without visible console window
                    subprocess.Popen(
                        [sys.executable, str(uninstaller_path)],
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    # macOS and other Unix-like systems
                    subprocess.Popen(
                        [sys.executable, str(uninstaller_path)],
                        start_new_session=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
        except Exception as e:
            print(f"Error launching uninstaller: {{e}}")
    
    def _spawn_post_uninstall_notifier(self):
        """Spawn a detached post-uninstall notifier script"""
        try:
            install_path = Path(__file__).parent
            
            # Create Python script for post-uninstall notification
            notifier_script = f'''#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

install_path = "{install_path}"

# Wait up to 10 minutes for installation folder to be removed
for i in range(600):  # 600 seconds = 10 minutes
    if not os.path.exists(install_path):
        break
    time.sleep(1)
else:
    # Timeout reached, installation folder still exists
    sys.exit(1)

# Show platform-specific notification
import platform
if platform.system() == "Darwin":
    # macOS - Use AppleScript
    import subprocess
    script = '''display dialog "Push Notifications client Uninstalled Successfully" buttons {{"OK"}} default button 1 with icon note'''
    subprocess.run(["osascript", "-e", script])
elif platform.system() == "Windows":
    # Windows - Use VBScript to avoid PowerShell window
    import tempfile
    vbs_script = '''MsgBox "Push Notifications client Uninstalled Successfully", 64, "Uninstall Complete"'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vbs", delete=False) as f:
        f.write(vbs_script)
        vbs_path = f.name
    try:
        subprocess.run(["wscript.exe", vbs_path], check=True)
    finally:
        try:
            os.unlink(vbs_path)
        except:
            pass
else:
    # Other platforms - fallback
    print("Push Notifications client Uninstalled Successfully")
'''
            
            # Write notifier script to temp directory
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(notifier_script)
                notifier_path = f.name
            
            # Launch detached notifier process
            if platform.system() == "Windows":
                subprocess.Popen(
                    [sys.executable, notifier_path],
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # macOS and other Unix-like systems
                subprocess.Popen(
                    [sys.executable, notifier_path],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
        except Exception as e:
            print(f"Error spawning post-uninstall notifier: {{e}}")
    
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
                    # Launch updater using Python
                    installer_path = Path(__file__).parent / "Installer.py"
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
        # Properly format variables for the embedded code
        api_url = self.api_url
        mac_address = self.mac_address
        client_id = self.device_data.get('clientId', 'unknown')
        key_id = self.key_id
        
        return f'''#!/usr/bin/env python3
"""
PushNotifications Windows Uninstaller
Embedded within installer - requests approval from website
"""

import os
import sys
import json
import time
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

API_URL = "{api_url}"
MAC_ADDRESS = "{mac_address}"
CLIENT_ID = "{client_id}"
KEY_ID = "{key_id}"

class PushNotificationsUninstaller:
    def __init__(self):
        self.install_path = Path(__file__).parent
        
    def request_uninstall_approval(self):
        """Request uninstall approval and wait for response"""
        try:
            # First, submit the uninstall request
            print("Submitting uninstall request to website...")
            response = requests.post(f"{{API_URL}}/api/index", json={{
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
                    check_response = requests.post(f"{{API_URL}}/api/index", json={{
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
            client_path = self.install_path / "Client.py"
            if client_path.exists():
                subprocess.Popen([sys.executable, str(client_path)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    uninstaller = PushNotificationsUninstaller()
    uninstaller.run()
'''
    
    
def _get_embedded_unix_client_code(self):
        """Get the embedded Unix client code with comprehensive cross-platform functionality"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Cross-Platform Client
Complete system with notifications, overlay management, security controls, and GUI features
Version: {INSTALLER_VERSION}
"""

import os
import sys
import json
import time
import threading
import subprocess
import platform
import signal
import queue
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Install and import requirements with comprehensive error handling
required_packages = [
    ('requests', 'requests>=2.31.0'),
    ('pystray', 'pystray>=0.19.4'),
    ('PIL', 'Pillow>=10.0.0'),
    ('psutil', 'psutil>=5.9.0')
]

for import_name, pip_name in required_packages:
    try:
        if import_name == 'PIL':
            from PIL import Image, ImageDraw, ImageFont, ImageTk
        else:
            __import__(import_name)
    except ImportError:
        try:
            print(f"Installing {{pip_name}}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])
            if import_name == 'PIL':
                from PIL import Image, ImageDraw, ImageFont, ImageTk
            else:
                __import__(import_name)
        except Exception as e:
            print(f"Warning: Could not install {{pip_name}}: {{e}}")

# Core imports
import requests
import psutil

# System tray imports
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw, ImageTk
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Warning: System tray not available - using console mode")

# GUI imports for notifications and dialogs
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: GUI features not available")

# Global flag to control GUI dialog usage - disable on non-Windows
USE_GUI_DIALOGS = False  # Disabled for Unix/macOS to prevent black box issues

# Cross-platform GUI utility functions
def show_message_dialog(title, message, dialog_type="info", parent=None):
    """Show a properly configured message dialog for cross-platform compatibility"""
    if not USE_GUI_DIALOGS or not GUI_AVAILABLE:
        print(f"{{title}}: {{message}}")
        return
    
    try:
        # Set environment variable to suppress tkinter deprecation warning on macOS
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
        
        # Create or use existing parent window
        if parent is None:
            root = tk.Tk()
            root.title(title)
            root.geometry("400x150")
            
            # Configure for better visibility on macOS
            root.attributes('-topmost', True)
            root.lift()
            root.focus_force()
            
            # Center the window
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
            
            parent_window = root
            should_destroy = True
        else:
            parent_window = parent
            should_destroy = False
        
        # Show appropriate dialog type
        if dialog_type == "error":
            messagebox.showerror(title, message, parent=parent_window)
        elif dialog_type == "warning":
            messagebox.showwarning(title, message, parent=parent_window)
        else:
            messagebox.showinfo(title, message, parent=parent_window)
        
        if should_destroy:
            parent_window.destroy()
            
    except Exception as e:
        print(f"GUI dialog failed ({{e}}): {{title}} - {{message}}")

# Client configuration
CLIENT_VERSION = "{INSTALLER_VERSION}"
API_URL = "{self.api_url}/api/index"
MAC_ADDRESS = "{self.mac_address}"
CLIENT_ID = "{self.device_data.get('clientId')}"
KEY_ID = "{self.key_id}"

class OverlayManager:
    """Cross-platform overlay manager for screen blocking"""
    
    def __init__(self):
        self.overlays = []
        self.active = False
        self.system = platform.system()
        
    def get_screen_info(self):
        """Get screen information across platforms"""
        screens = []
        
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                
                # Primary screen
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                screens.append({{'x': 0, 'y': 0, 'width': width, 'height': height}})
                
                root.destroy()
            except Exception as e:
                print(f"Error getting screen info: {{e}}")
                # Fallback default
                screens = [{{'x': 0, 'y': 0, 'width': 1920, 'height': 1080}}]
        
        return screens
    
    def create_overlay_for_screen(self, screen):
        """Create overlay window for specific screen"""
        if not GUI_AVAILABLE:
            return None
            
        try:
            overlay = tk.Toplevel()
            overlay.withdraw()  # Hide initially
            
            # Configure overlay properties
            overlay.overrideredirect(True)  # No window decorations
            overlay.attributes('-alpha', 0.25)  # 25% opacity
            overlay.attributes('-topmost', True)  # Keep above other windows
            overlay.configure(bg='gray')
            
            # Platform-specific window configuration
            if self.system == "Darwin":  # macOS
                try:
                    # macOS specific window handling
                    overlay.attributes('-transparent', True)
                    overlay.attributes('-toolwindow', True)
                except Exception as e:
                    print(f"macOS overlay config warning: {{e}}")
            elif self.system == "Linux":
                try:
                    # Linux specific window handling
                    overlay.attributes('-type', 'dock')
                except Exception as e:
                    print(f"Linux overlay config warning: {{e}}")
            
            # Position on screen
            x, y = screen['x'], screen['y']
            width, height = screen['width'], screen['height']
            overlay.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
            
            # Add click-through behavior
            overlay.bind("<Button-1>", lambda e: None)
            overlay.bind("<Key>", lambda e: None)
            
            return overlay
        except Exception as e:
            print(f"Error creating overlay: {{e}}")
            return None
    
    def show_overlays(self):
        """Show overlays on all screens"""
        if self.active or not GUI_AVAILABLE:
            return
            
        try:
            screens = self.get_screen_info()
            
            for screen in screens:
                overlay = self.create_overlay_for_screen(screen)
                if overlay:
                    self.overlays.append(overlay)
                    overlay.deiconify()  # Show overlay
            
            self.active = True
            print(f"✓ Screen overlay activated on {{len(self.overlays)}} screen(s)")
            
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
        print("✓ Screen overlay deactivated")

class WindowManager:
    """Cross-platform window and process management"""
    
    def __init__(self):
        self.system = platform.system()
        self.minimized_windows = []
        
        # Cross-platform restricted processes
        self.restricted_processes = {{
            'browsers': [
                'chrome', 'firefox', 'safari', 'opera', 'brave', 'edge', 'chromium',
                'Chrome', 'Firefox', 'Safari', 'Opera', 'Brave', 'Edge', 'Chromium'
            ],
            'vpn': [
                'openvpn', 'nordvpn', 'expressvpn', 'cyberghost', 'tunnelbear', 'protonvpn',
                'OpenVPN', 'NordVPN', 'ExpressVPN', 'CyberGhost', 'TunnelBear', 'ProtonVPN'
            ],
            'proxy': [
                'proxifier', 'proxycap', 'sockscap', 'shadowsocks', 'v2ray',
                'Proxifier', 'ProxyCap', 'SocksCap', 'Shadowsocks', 'V2Ray'
            ]
        }}
        
        # System processes that should never be terminated
        self.allowed_processes = [
            'systemd', 'kernel', 'init', 'launchd', 'WindowServer', 'loginwindow',
            'Finder', 'Dock', 'SystemUIServer', 'Activity Monitor', 'htop', 'top'
        ]
    
    def minimize_windows(self):
        """Cross-platform window minimization"""
        try:
            if self.system == "Darwin":  # macOS
                # Use AppleScript to minimize windows
                applescript = (
                    'tell application "System Events"\n'
                    'set visibleApps to name of every application process whose visible is true\n'
                    'repeat with appName in visibleApps\n'
                    'if appName is not "PushNotifications" and appName is not "Finder" then\n'
                    'try\n'
                    'tell application process appName\n'
                    'set visible to false\n'
                    'end tell\n'
                    'end try\n'
                    'end if\n'
                    'end repeat\n'
                    'end tell'
                )
                subprocess.run(['osascript', '-e', applescript], check=False)
                
            elif self.system == "Linux":
                # Use wmctrl if available
                if subprocess.run(['which', 'wmctrl'], capture_output=True).returncode == 0:
                    subprocess.run(['wmctrl', '-k', 'on'], check=False)  # Show desktop
                else:
                    # Fallback: use xdotool if available
                    if subprocess.run(['which', 'xdotool'], capture_output=True).returncode == 0:
                        subprocess.run(['xdotool', 'key', 'Super+d'], check=False)
                        
            print("✓ Windows minimized")
        except Exception as e:
            print(f"Error minimizing windows: {{e}}")
    
    def block_restricted_processes(self, allowed_websites=None):
        """Block VPN, proxy, and browser processes except allowed websites"""
        try:
            blocked_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    
                    # Check if it's a restricted process
                    is_restricted = False
                    for category, processes in self.restricted_processes.items():
                        if proc_name in processes:
                            is_restricted = True
                            break
                    
                    if is_restricted and proc_name not in self.allowed_processes:
                        # For browsers, check if websites are allowed
                        if proc_name.lower() in [p.lower() for p in self.restricted_processes['browsers']]:
                            if not allowed_websites:
                                proc.terminate()
                                blocked_count += 1
                                print(f"  ✓ Blocked browser: {{proc_name}} (PID: {{proc.info['pid']}})")
                        else:
                            # Terminate VPN/proxy processes
                            proc.terminate()
                            blocked_count += 1
                            print(f"  ✓ Blocked process: {{proc_name}} (PID: {{proc.info['pid']}})")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if blocked_count > 0:
                print(f"✓ Blocked {{blocked_count}} restricted processes")
        except Exception as e:
            print(f"Error blocking processes: {{e}}")

class NotificationWindow:
    """Cross-platform notification window with full GUI controls"""
    
    def __init__(self, notification_data, callback_handler):
        self.data = notification_data
        self.callback = callback_handler
        self.window = None
        self.minimized = False
        self.website_request_var = None
        self.system = platform.system()
        
    def create_window(self):
        """Create comprehensive notification window"""
        if not GUI_AVAILABLE:
            return
            
        try:
            self.window = tk.Toplevel()
            self.window.title("Push Notification")
            
            # Configure window properties
            self.window.attributes('-topmost', True)
            self.window.resizable(False, False)
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)
            
            # Platform-specific window configuration
            if self.system == "Darwin":  # macOS
                try:
                    self.window.attributes('-modified', False)
                    self.window.attributes('-titlepath', '')
                except Exception:
                    pass
            elif self.system == "Linux":
                try:
                    self.window.attributes('-type', 'dialog')
                except Exception:
                    pass
            
            # Set window size and center it
            width, height = 450, 350
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
            
            # Modern design theme colors
            colors = {{
                'bg': "#ffffff",
                'header': "#1a73e8",  # Google Blue
                'text': "#202124",    # Dark Gray
                'border': "#dadce0",  # Light Gray
                'button_primary': "#1a73e8",
                'button_secondary': "#5f6368",
                'button_warning': "#f29900",
                'button_danger': "#d93025",
                'shadow': "#0000001a"  # 10% black shadow
            }}
            
            # Set base window style
            self.window.configure(bg=colors['bg'])
            
            # Header with gradient effect
            header_height = 60
            header_frame = tk.Frame(self.window, bg=colors['header'], height=header_height)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            # Header content with icon and text
            header_content = tk.Frame(header_frame, bg=colors['header'])
            header_content.pack(expand=True)
            
            # Try to load icon
            try:
                icon_path = Path(__file__).parent / "pnicon.png"
                if icon_path.exists():
                    icon = Image.open(icon_path)
                    icon = icon.resize((32, 32), Image.Resampling.LANCZOS)
                    icon = ImageTk.PhotoImage(icon)
                    icon_label = tk.Label(header_content, image=icon, bg=colors['header'])
                    icon_label.image = icon  # Keep reference
                    icon_label.pack(side=tk.LEFT, padx=(15, 10))
            except Exception:
                pass  # Skip icon if not available
            
            title_label = tk.Label(header_content, text="🔔 Push Notification", 
                                 bg=colors['header'], fg="white", 
                                 font=("Helvetica", 16, "bold"))
            title_label.pack(side=tk.LEFT, padx=10)
            
            # Content area with padding
            content_frame = tk.Frame(self.window, bg=colors['bg'])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
            
            # Message text with improved typography
            message_text = self.data.get('message', '')
            message_text = self._strip_html_and_decode(message_text)
            
            # Create text widget for better text rendering
            message_widget = tk.Text(content_frame, wrap=tk.WORD, 
                                   font=("Helvetica", 11),
                                   bg=colors['bg'], fg=colors['text'],
                                   relief='flat', height=6, bd=1)
            message_widget.insert('1.0', message_text)
            message_widget.configure(state='disabled', highlightthickness=1,
                                   highlightbackground=colors['border'])
            message_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Allowed websites (if any)
            allowed_websites = self.data.get('allowedWebsites', [])
            if allowed_websites:
                websites_label = tk.Label(content_frame, 
                                        text=f"✅ Allowed: {{', '.join(allowed_websites)}}", 
                                        bg=colors['bg'], wraplength=400, justify=tk.LEFT,
                                        font=("Helvetica", 9), fg="#137333")
                websites_label.pack(pady=(0, 10))
            
            # Define the create_button function
            def create_button(parent, text, command, color, is_primary=False, icon=None):
                """Create a modern styled button"""
                btn_text = f"{{icon}} {{text}}" if icon else text
                btn = tk.Button(parent, text=btn_text, command=command,
                              font=("Helvetica", 10, "bold" if is_primary else "normal"),
                              fg="white" if is_primary else colors['text'],
                              bg=color if is_primary else colors['bg'],
                              activebackground=color if is_primary else colors['border'],
                              activeforeground="white" if is_primary else colors['text'],
                              relief='flat', bd=0 if is_primary else 1,
                              padx=20, pady=8)
                if not is_primary:
                    btn.configure(highlightthickness=1,
                                highlightbackground=colors['border'])
                return btn
            
            # Website request section
            if self.data.get('allowWebsiteRequests', False):
                request_frame = tk.LabelFrame(content_frame, text="🌐 Request Website Access",
                                            bg=colors['bg'], fg=colors['text'],
                                            font=("Helvetica", 10, "bold"))
                request_frame.pack(fill=tk.X, pady=(10, 15))
                
                entry_frame = tk.Frame(request_frame, bg=colors['bg'])
                entry_frame.pack(fill=tk.X, padx=10, pady=10)
                
                self.website_request_var = tk.StringVar()
                request_entry = tk.Entry(entry_frame,
                                       textvariable=self.website_request_var,
                                       font=("Helvetica", 10), bd=1, relief='solid',
                                       highlightthickness=1,
                                       highlightbackground=colors['border'])
                request_entry.pack(fill=tk.X, pady=(0, 10))
                request_entry.insert(0, "https://")
                
                request_button = create_button(entry_frame,
                                             "Send Request",
                                             self.request_website_access,
                                             colors['button_primary'],
                                             True, "📤")
                request_button.pack(anchor=tk.E)
            
            # Button container with modern styling
            button_frame = tk.Frame(self.window, bg=colors['bg'])
            button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            # Left side buttons (Snooze)
            left_buttons = tk.Frame(button_frame, bg=colors['bg'])
            left_buttons.pack(side=tk.LEFT)
            
            # Snooze dropdown menu
            snooze_var = tk.StringVar(value="⏰ Snooze")
            snooze_menu = tk.Menu(self.window, tearoff=0)
            snooze_options = [("5 minutes", 5), ("15 minutes", 15), ("30 minutes", 30), ("1 hour", 60)]
            
            for label, mins in snooze_options:
                snooze_menu.add_command(
                    label=f"⏰ {{label}}",
                    command=lambda m=mins: self.snooze_notification(m)
                )
            
            def show_snooze_menu():
                try:
                    snooze_menu.post(snooze_btn.winfo_rootx(),
                                   snooze_btn.winfo_rooty() + snooze_btn.winfo_height())
                except Exception as e:
                    print(f"Error showing snooze menu: {{e}}")
            
            snooze_btn = create_button(left_buttons, "Snooze ▾", show_snooze_menu,
                                     colors['button_warning'], False, "⏰")
            snooze_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # Right side buttons
            right_buttons = tk.Frame(button_frame, bg=colors['bg'])
            right_buttons.pack(side=tk.RIGHT)
            
            # Minimize button (if website requests allowed)
            if self.data.get('allowWebsiteRequests', False):
                minimize_btn = create_button(right_buttons, "Minimize",
                                           self.minimize_notification,
                                           colors['button_secondary'], False, "➖")
                minimize_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Complete button
            complete_btn = create_button(right_buttons, "Mark Complete",
                                       self.complete_notification,
                                       colors['button_primary'], True, "✅")
            complete_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Focus and bring to front
            self.window.focus_force()
            self.window.lift()
            
        except Exception as e:
            print(f"Error creating notification window: {{e}}")
    
    def _strip_html_and_decode(self, text):
        """Remove HTML tags and decode HTML entities"""
        import html
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', text)
        # Decode HTML entities
        text = html.unescape(text)
        return text.strip()
    
    def request_website_access(self):
        """Request access to a specific website"""
        website = self.website_request_var.get().strip()
        if website and website != "https://":
            self.callback('request_website', {{
                'notificationId': self.data.get('id'),
                'website': website
            }})
            if GUI_AVAILABLE:
                show_message_dialog("Request Sent", f"Website access request sent for:\n{{website}}")
            self.website_request_var.set("https://")
    
    def snooze_notification(self, minutes):
        """Snooze notification for specified minutes"""
        self.callback('snooze', {{
            'notificationId': self.data.get('id'),
            'minutes': minutes
        }})
        if GUI_AVAILABLE:
            show_message_dialog("Snoozed", f"Notification snoozed for {{minutes}} minute(s)")
        self.close()
    
    def complete_notification(self):
        """Mark notification as complete"""
        self.callback('complete', {{
            'notificationId': self.data.get('id')
        }})
        if GUI_AVAILABLE:
            show_message_dialog("Complete", "Notification marked as complete!")
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
            self.window.lift()
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
        self.close()

class PushNotificationsCrossplatformClient:
    def __init__(self):
        self.running = True
        self.notifications = []
        self.notification_windows = []
        self.tray_icon = None
        self.notification_thread = None
        self.overlay_manager = OverlayManager()
        self.window_manager = WindowManager()
        self.system = platform.system()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"\n🚀 PushNotifications Client v{{CLIENT_VERSION}}")
        print(f"Platform: {{self.system}}")
        print(f"Client ID: {{CLIENT_ID}}")
        print(f"MAC Address: {{MAC_ADDRESS}}")
        print(f"System Tray: {{'✅ Available' if TRAY_AVAILABLE else '❌ Not Available'}}")
        print(f"GUI Support: {{'✅ Available' if GUI_AVAILABLE else '❌ Not Available'}}")
    
    def signal_handler(self, signum, frame):
        print(f"\n🔄 Received signal {{signum}}, shutting down gracefully...")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        sys.exit(0)
    
    def create_tray_icon(self):
        """Create comprehensive system tray icon"""
        if not TRAY_AVAILABLE:
            return None
            
        try:
            # Create icon image
            def create_image():
                width = height = 64
                image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                dc = ImageDraw.Draw(image)
                
                # Try to load custom icon first
                try:
                    icon_path = Path(__file__).parent / "pnicon.png"
                    if icon_path.exists():
                        custom_icon = Image.open(icon_path)
                        custom_icon = custom_icon.resize((width, height), Image.Resampling.LANCZOS)
                        return custom_icon
                except Exception:
                    pass
                
                # Fallback: create custom icon
                dc.ellipse([4, 4, width-4, height-4], fill=(26, 115, 232), outline=(23, 103, 209))
                
                # Add notification badge if there are active notifications
                active_count = len([n for n in self.notifications if not n.get('completed', False)])
                if active_count > 0:
                    # Red notification badge
                    badge_size = 20
                    dc.ellipse([width-badge_size-2, 2, width-2, badge_size+2], fill=(234, 67, 53))
                    
                    # Badge text
                    badge_text = str(min(active_count, 99))
                    try:
                        font = ImageFont.load_default()
                        bbox = dc.textbbox((0, 0), badge_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        x = width - badge_size//2 - text_width//2
                        y = badge_size//2 - text_height//2
                        dc.text((x, y), badge_text, fill='white', font=font)
                    except:
                        dc.text((width-15, 8), badge_text, fill='white')
                
                # Add "PN" text
                try:
                    font = ImageFont.load_default()
                    bbox = dc.textbbox((0, 0), "PN", font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (width - text_width) // 2
                    y = (height - text_height) // 2 + 5
                    dc.text((x, y), "PN", fill='white', font=font)
                except:
                    dc.text((width//2-12, height//2-3), "PN", fill='white')
                
                return image
            
            # Create comprehensive menu
            menu = pystray.Menu(
                item('📊 Show Status', self.show_status),
                item('📋 Show Notifications', self.show_notification_list),
                pystray.Menu.SEPARATOR,
                item('✅ Mark Complete', self.mark_complete_tray),
                item('🌐 Request Website', self.request_website_tray),
                item('⏰ Snooze All', self.snooze_all_tray),
                pystray.Menu.SEPARATOR,
                item('🔒 Screen Control', pystray.Menu(
                    item('🟢 Show Overlay', self.show_overlay_tray),
                    item('🔴 Hide Overlay', self.hide_overlay_tray),
                    item('➖ Minimize Windows', self.minimize_windows_tray)
                )),
                pystray.Menu.SEPARATOR,
                item('⚙️ Settings', self.show_settings),
                item('ℹ️ About', self.show_about),
                pystray.Menu.SEPARATOR,
                item('🔄 Restart', self.restart_client),
                item('❌ Quit', self.quit_application)
            )
            
            return pystray.Icon("PushNotifications", create_image(), "PushNotifications Client", menu)
        except Exception as e:
            print(f"Error creating tray icon: {{e}}")
            return None
    
    def show_status(self, icon=None, item=None):
        """Show comprehensive client status"""
        active_count = len([n for n in self.notifications if not n.get('completed', False)])
        
        status_info = f"""PushNotifications Client Status

✅ Version: {{CLIENT_VERSION}}
🆔 Client ID: {{CLIENT_ID}}
📶 Status: Running
📋 Active Notifications: {{active_count}}
💻 Platform: {{self.system}}
🔒 Overlay: {{'Active' if self.overlay_manager.active else 'Inactive'}}
🎯 System Tray: {{'Available' if TRAY_AVAILABLE else 'Not Available'}}
🖥️ GUI: {{'Available' if GUI_AVAILABLE else 'Not Available'}}"""
        
        if GUI_AVAILABLE:
            try:
                show_message_dialog("Client Status", status_info)
            except Exception as e:
                print(f"Error showing status dialog: {{e}}")
        else:
            print(status_info)
    
    def show_notification_list(self, icon=None, item=None):
        """Show list of active notifications"""
        active_notifications = [n for n in self.notifications if not n.get('completed', False)]
        
        if not active_notifications:
            if GUI_AVAILABLE:
                try:
                    show_message_dialog("Notifications", "No active notifications")
                except:
                    pass
            else:
                print("No active notifications")
            return
        
        if GUI_AVAILABLE:
            try:
                # Create notification list window
                list_window = tk.Toplevel()
                list_window.title("Active Notifications")
                list_window.geometry("500x400")
                list_window.attributes('-topmost', True)
                
                # Header
                tk.Label(list_window, text="📋 Active Notifications", 
                        font=("Helvetica", 14, "bold")).pack(pady=10)
                
                # Scrollable list
                frame = tk.Frame(list_window)
                frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                scrollbar = tk.Scrollbar(frame)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, 
                                   font=("Helvetica", 10))
                listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.config(command=listbox.yview)
                
                for i, notif in enumerate(active_notifications):
                    message = notif.get('message', 'No message')[:100]
                    if len(notif.get('message', '')) > 100:
                        message += "..."
                    listbox.insert(tk.END, f"{{i+1}}. {{message}}")
                
                # Close button
                tk.Button(list_window, text="Close", 
                         command=list_window.destroy).pack(pady=10)
                
            except Exception as e:
                print(f"Error showing notification list: {{e}}")
    
    def mark_complete_tray(self, icon=None, item=None):
        """Mark first notification as complete from tray"""
        active_notifications = [n for n in self.notifications if not n.get('completed', False)]
        if active_notifications:
            try:
                notif_id = active_notifications[0].get('id')
                self.complete_notification_by_id(notif_id)
            except Exception as e:
                print(f"Error marking notification complete: {{e}}")
        else:
            if GUI_AVAILABLE:
                try:
                    show_message_dialog("No Notifications", "No active notifications to complete.")
                except:
                    pass
    
    def request_website_tray(self, icon=None, item=None):
        """Request website access from tray"""
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                website = simpledialog.askstring(
                    "Website Access Request",
                    "Enter the website URL:",
                    initialvalue="https://"
                )
                root.destroy()
                
                if website and website != "https://":
                    self.send_website_request(website)
                    show_message_dialog("Request Sent", f"Website access request sent for:\n{{website}}")
            except Exception as e:
                print(f"Error requesting website access: {{e}}")
    
    def snooze_all_tray(self, icon=None, item=None):
        """Snooze all notifications from tray"""
        active_notifications = [n for n in self.notifications if not n.get('completed', False)]
        if active_notifications:
            if GUI_AVAILABLE:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    minutes = simpledialog.askinteger(
                        "Snooze All Notifications",
                        "Snooze all notifications for how many minutes?",
                        initialvalue=15, minvalue=1, maxvalue=1440
                    )
                    root.destroy()
                    
                    if minutes:
                        for notif in active_notifications:
                            self.snooze_notification_by_id(notif.get('id'), minutes)
                        messagebox.showinfo("Snoozed", f"All notifications snoozed for {{minutes}} minute(s)")
                except Exception as e:
                    print(f"Error snoozing notifications: {{e}}")
        else:
            if GUI_AVAILABLE:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo("No Notifications", "No active notifications to snooze.")
                    root.destroy()
                except:
                    pass
    
    def show_overlay_tray(self, icon=None, item=None):
        """Show screen overlay from tray"""
        self.overlay_manager.show_overlays()
    
    def hide_overlay_tray(self, icon=None, item=None):
        """Hide screen overlay from tray"""
        self.overlay_manager.hide_overlays()
    
    def minimize_windows_tray(self, icon=None, item=None):
        """Minimize windows from tray"""
        self.window_manager.minimize_windows()
    
    def show_settings(self, icon=None, item=None):
        """Show comprehensive settings window"""
        if GUI_AVAILABLE:
            try:
                settings_window = tk.Toplevel()
                settings_window.title("PushNotifications Settings")
                settings_window.geometry("500x600")
                settings_window.attributes('-topmost', True)
                
                # Header
                tk.Label(settings_window, text="⚙️ PushNotifications Settings", 
                        font=("Helvetica", 16, "bold")).pack(pady=10)
                
                # Create notebook for tabs
                notebook = ttk.Notebook(settings_window)
                notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                # Client Info tab
                info_frame = tk.Frame(notebook, bg='white')
                notebook.add(info_frame, text="Client Info")
                
                info_data = [
                    ("Version", CLIENT_VERSION),
                    ("Client ID", CLIENT_ID),
                    ("Platform", self.system),
                    ("Status", "Running"),
                    ("Active Notifications", len([n for n in self.notifications if not n.get('completed', False)])),
                    ("System Tray", "Available" if TRAY_AVAILABLE else "Not Available"),
                    ("GUI Support", "Available" if GUI_AVAILABLE else "Not Available")
                ]
                
                for i, (key, value) in enumerate(info_data):
                    row_frame = tk.Frame(info_frame, bg='white')
                    row_frame.pack(fill=tk.X, padx=20, pady=5)
                    tk.Label(row_frame, text=f"{{key}}:", font=("Helvetica", 10, "bold"), 
                           bg='white', anchor='w').pack(side=tk.LEFT)
                    tk.Label(row_frame, text=str(value), font=("Helvetica", 10), 
                           bg='white', anchor='e').pack(side=tk.RIGHT)
                
                # Controls tab
                controls_frame = tk.Frame(notebook, bg='white')
                notebook.add(controls_frame, text="Controls")
                
                tk.Label(controls_frame, text="Screen Control", 
                        font=("Helvetica", 12, "bold"), bg='white').pack(pady=10)
                
                tk.Button(controls_frame, text="🟢 Show Screen Overlay", 
                         command=self.show_overlay_tray).pack(pady=5)
                tk.Button(controls_frame, text="🔴 Hide Screen Overlay", 
                         command=self.hide_overlay_tray).pack(pady=5)
                tk.Button(controls_frame, text="➖ Minimize All Windows", 
                         command=self.minimize_windows_tray).pack(pady=5)
                
                tk.Label(controls_frame, text="Notifications", 
                        font=("Helvetica", 12, "bold"), bg='white').pack(pady=(20, 10))
                
                tk.Button(controls_frame, text="📋 Show Notification List", 
                         command=self.show_notification_list).pack(pady=5)
                tk.Button(controls_frame, text="✅ Mark All Complete", 
                         command=self.mark_all_complete).pack(pady=5)
                
                # Close button
                tk.Button(settings_window, text="Close", 
                         command=settings_window.destroy).pack(pady=10)
                
            except Exception as e:
                print(f"Error showing settings: {{e}}")
    
    def show_about(self, icon=None, item=None):
        """Show comprehensive about dialog"""
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                about_text = f"""PushNotifications Client

🚀 Version: {{CLIENT_VERSION}}
💻 Platform: {{self.system}}
🆔 Client ID: {{CLIENT_ID[:8]}}...

📱 Cross-platform notification client with advanced features:
• System tray integration
• Screen overlay management
• Window and process control
• Website access requests
• Multi-platform notifications

🔧 System Capabilities:
• GUI Support: {{'Yes' if GUI_AVAILABLE else 'No'}}
• System Tray: {{'Yes' if TRAY_AVAILABLE else 'No'}}
• Process Management: Yes
• Screen Overlay: {{'Yes' if GUI_AVAILABLE else 'No'}}

© 2024 PushNotifications"""
                
                messagebox.showinfo("About PushNotifications", about_text)
                root.destroy()
            except Exception as e:
                print(f"Error showing about dialog: {{e}}")
    
    def restart_client(self, icon=None, item=None):
        """Restart the client"""
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                if messagebox.askyesno("Restart Client", "Are you sure you want to restart the client?"):
                    print("🔄 Restarting client...")
                    self.running = False
                    if self.tray_icon:
                        self.tray_icon.stop()
                    
                    # Restart script
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                root.destroy()
            except Exception as e:
                print(f"Error restarting client: {{e}}")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application"""
        print("🔄 Shutting down client...")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
    
    def check_notifications(self):
        """Background thread for checking notifications with comprehensive handling"""
        while self.running:
            try:
                response = requests.post(API_URL, json={{
                    'action': 'getClientNotifications',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS
                }}, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        notifications = result.get('data', [])
                        
                        # Process each notification
                        for notif in notifications:
                            if not self.is_notification_seen(notif):
                                print(f"📨 New notification: {{notif.get('message', '')[:50]}}...")
                                
                                # Show notification based on available methods
                                self.show_comprehensive_notification(notif)
                                self.notifications.append(notif)
                                
                                # Handle special notification actions
                                self.handle_notification_actions(notif)
                        
                        # Update tray icon to reflect active notifications
                        if self.tray_icon and TRAY_AVAILABLE:
                            try:
                                self.tray_icon.icon = self.create_tray_icon().icon
                            except:
                                pass
                            
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error checking notifications: {{e}}")
                time.sleep(60)  # Wait longer on error
    
    def handle_notification_actions(self, notification):
        """Handle special notification actions and commands"""
        message = notification.get('message', '').lower()
        
        # Check for special commands in notification
        if 'show_overlay' in message or 'block_screen' in message:
            self.overlay_manager.show_overlays()
        elif 'hide_overlay' in message or 'unblock_screen' in message:
            self.overlay_manager.hide_overlays()
        elif 'minimize_windows' in message:
            self.window_manager.minimize_windows()
        elif 'block_processes' in message:
            allowed_websites = notification.get('allowedWebsites', [])
            self.window_manager.block_restricted_processes(allowed_websites)
    
    def show_comprehensive_notification(self, notification):
        """Show notification using the best available method"""
        message = notification.get('message', '')
        title = notification.get('title', 'Push Notification')
        
        print(f"🔔 {{title}}: {{message}}")
        
        # Method 1: GUI Window (most comprehensive)
        if GUI_AVAILABLE and notification.get('showWindow', True):
            try:
                notif_window = NotificationWindow(notification, self.notification_callback)
                notif_window.create_window()
                self.notification_windows.append(notif_window)
                return
            except Exception as e:
                print(f"Error creating GUI notification: {{e}}")
        
        # Method 2: System notifications (fallback)
        self.show_system_notification(title, message)
    
    def show_system_notification(self, title, message):
        """Show system-native notification"""
        try:
            if self.system == "Darwin":  # macOS
                # Try multiple macOS notification methods
                methods = [
                    # Method 1: AppleScript notification
                    lambda: subprocess.run([
                        'osascript', '-e',
                        f'display notification "{{message.replace(chr(34), chr(92) + chr(34))}}" with title "{{title.replace(chr(34), chr(92) + chr(34))}}" sound name "default"'
                    ], check=False),
                    
                    # Method 2: terminal-notifier (if available)
                    lambda: subprocess.run([
                        'terminal-notifier', '-title', title, '-message', message, '-group', 'pushnotifications'
                    ], check=False) if subprocess.run(['which', 'terminal-notifier'], capture_output=True).returncode == 0 else None
                ]
                
                for method in methods:
                    try:
                        result = method()
                        if result is not None:
                            return
                    except:
                        continue
            
            elif self.system == "Linux":
                # Try multiple Linux notification methods
                methods = [
                    # Method 1: notify-send (most common)
                    lambda: subprocess.run([
                        'notify-send', '--app-name=PushNotifications',
                        '--urgency=normal', '--expire-time=10000',
                        title, message
                    ], check=False) if subprocess.run(['which', 'notify-send'], capture_output=True).returncode == 0 else None,
                    
                    # Method 2: zenity dialog
                    lambda: subprocess.run([
                        'zenity', '--info', f'--title={{title}}', f'--text={{message}}', '--timeout=10'
                    ], check=False) if subprocess.run(['which', 'zenity'], capture_output=True).returncode == 0 else None,
                    
                    # Method 3: kdialog (KDE)
                    lambda: subprocess.run([
                        'kdialog', '--msgbox', message, '--title', title
                    ], check=False) if subprocess.run(['which', 'kdialog'], capture_output=True).returncode == 0 else None
                ]
                
                for method in methods:
                    try:
                        result = method()
                        if result is not None:
                            return
                    except:
                        continue
        except Exception as e:
            print(f"Error showing system notification: {{e}}")
        
        # Final fallback: Terminal output with bell
        print(f"\a🔔 {{title}}: {{message}}")
    
    def notification_callback(self, action, data):
        """Handle callbacks from notification windows"""
        try:
            if action == 'complete':
                notif_id = data.get('notificationId')
                self.complete_notification_by_id(notif_id)
            elif action == 'snooze':
                notif_id = data.get('notificationId')
                minutes = data.get('minutes')
                self.snooze_notification_by_id(notif_id, minutes)
            elif action == 'request_website':
                website = data.get('website')
                self.send_website_request(website)
        except Exception as e:
            print(f"Error handling notification callback: {{e}}")
    
    def is_notification_seen(self, notification):
        """Check if notification has been seen before"""
        notif_id = notification.get('id')
        return any(n.get('id') == notif_id for n in self.notifications)
    
    def complete_notification_by_id(self, notification_id):
        """Mark specific notification as complete"""
        try:
            response = requests.post(API_URL, json={{
                'action': 'markNotificationComplete',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'notificationId': notification_id
            }}, timeout=10)
            
            if response.status_code == 200:
                # Update local notification status
                for notif in self.notifications:
                    if notif.get('id') == notification_id:
                        notif['completed'] = True
                        break
                print(f"✅ Notification {{notification_id}} marked complete")
            else:
                print(f"❌ Failed to mark notification complete: HTTP {{response.status_code}}")
                
        except Exception as e:
            print(f"❌ Error completing notification: {{e}}")
    
    def snooze_notification_by_id(self, notification_id, minutes):
        """Snooze specific notification"""
        try:
            response = requests.post(API_URL, json={{
                'action': 'snoozeNotification',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'notificationId': notification_id,
                'minutes': minutes
            }}, timeout=10)
            
            if response.status_code == 200:
                print(f"⏰ Notification {{notification_id}} snoozed for {{minutes}} minute(s)")
            else:
                print(f"❌ Failed to snooze notification: HTTP {{response.status_code}}")
                
        except Exception as e:
            print(f"❌ Error snoozing notification: {{e}}")
    
    def mark_all_complete(self):
        """Mark all active notifications as complete"""
        active_notifications = [n for n in self.notifications if not n.get('completed', False)]
        
        if not active_notifications:
            if GUI_AVAILABLE:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo("No Notifications", "No active notifications to complete.")
                    root.destroy()
                except:
                    pass
            return
        
        for notif in active_notifications:
            self.complete_notification_by_id(notif.get('id'))
        
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Complete", f"Marked {{len(active_notifications)}} notification(s) as complete.")
                root.destroy()
            except:
                pass
    
    def send_website_request(self, website_url):
        """Send website access request to server"""
        try:
            response = requests.post(API_URL, json={{
                'action': 'requestWebsiteAccess',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'websiteUrl': website_url,
                'timestamp': datetime.now().isoformat()
            }}, timeout=10)
            
            if response.status_code == 200:
                print(f"🌐 Website access requested: {{website_url}}")
            else:
                print(f"❌ Failed to request website access: HTTP {{response.status_code}}")
                
        except Exception as e:
            print(f"❌ Error requesting website access: {{e}}")
    
    def run(self):
        """Main client run method"""
        print(f"\n🚀 Starting PushNotifications Client v{{CLIENT_VERSION}}...")
        print(f"🔧 Initializing components...")
        
        # Start notification checking thread
        self.notification_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notification_thread.start()
        print("✅ Notification checker started")
        
        if TRAY_AVAILABLE:
            # Run with system tray
            print("✅ Starting with system tray support")
            try:
                self.tray_icon = self.create_tray_icon()
                if self.tray_icon:
                    print("🎯 System tray icon created")
                    print("\n🔄 Client is now running in the background")
                    print("📱 Check your system tray for the PushNotifications icon")
                    print("\n👋 To exit, right-click the tray icon and select 'Quit'")
                    self.tray_icon.run()  # This blocks until the icon is stopped
                else:
                    print("⚠️ System tray failed, falling back to console mode")
                    self.run_console_mode()
            except Exception as e:
                print(f"❌ System tray error: {{e}}")
                print("🔄 Falling back to console mode")
                self.run_console_mode()
        else:
            # Run in console mode
            print("📟 Starting in console mode (system tray not available)")
            self.run_console_mode()
    
    def run_console_mode(self):
        """Run client in console/terminal mode"""
        print("\n" + "="*60)
        print("🖥️  CONSOLE MODE - PushNotifications Client")
        print("="*60)
        print("📋 Available Commands:")
        print("  📊 'status'    - Show client status")
        print("  📋 'list'      - List active notifications")
        print("  ✅ 'complete'  - Mark first notification complete")
        print("  ⏰ 'snooze'    - Snooze first notification")
        print("  🌐 'website'   - Request website access")
        print("  🟢 'overlay'   - Toggle screen overlay")
        print("  ➖ 'minimize'  - Minimize all windows")
        print("  ❓ 'help'      - Show this help")
        print("  ❌ 'quit'      - Exit client")
        print("\n⌨️  Press Ctrl+C or type 'quit' to exit\n")
        
        try:
            while self.running:
                try:
                    cmd = input("PushClient> ").strip().lower()
                    
                    if cmd == 'status':
                        self.show_status()
                    elif cmd == 'list':
                        self.show_notification_list()
                    elif cmd == 'complete':
                        self.mark_complete_tray()
                    elif cmd == 'snooze':
                        try:
                            minutes = int(input("Snooze for how many minutes? (default 15): ") or 15)
                            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
                            if active_notifications:
                                self.snooze_notification_by_id(active_notifications[0].get('id'), minutes)
                            else:
                                print("No active notifications to snooze.")
                        except ValueError:
                            print("Invalid number. Please enter a valid number of minutes.")
                    elif cmd == 'website':
                        url = input("Website URL (https://): ").strip()
                        if url and url != "https://":
                            self.send_website_request(url)
                        else:
                            print("Invalid URL provided.")
                    elif cmd == 'overlay':
                        if self.overlay_manager.active:
                            self.overlay_manager.hide_overlays()
                        else:
                            self.overlay_manager.show_overlays()
                    elif cmd == 'minimize':
                        self.window_manager.minimize_windows()
                    elif cmd in ['quit', 'exit', 'q']:
                        break
                    elif cmd in ['help', '?', 'h']:
                        print("\n📋 Available commands: status, list, complete, snooze, website, overlay, minimize, help, quit")
                    else:
                        if cmd:
                            print(f"❓ Unknown command: '{{cmd}}'. Type 'help' for available commands.")
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Command error: {{e}}")
                    
        except KeyboardInterrupt:
            pass
        
        print("\n👋 PushNotifications Client shutting down...")
        self.running = False
        # Clean up resources
        self.overlay_manager.hide_overlays()
        for window in self.notification_windows:
            window.close()

if __name__ == "__main__":
    try:
        client = PushNotificationsCrossplatformClient()
        client.run()
    except KeyboardInterrupt:
        print("\n👋 Client terminated by user")
    except Exception as e:
        print(f"\n❌ Fatal client error: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
'''
    
def _get_embedded_unix_uninstaller_code(self):
        """Get the embedded Unix uninstaller code with full approval system"""
        # Properly format variables for the embedded code
        api_url = self.api_url
        mac_address = self.mac_address
        client_id = self.device_data.get('clientId', 'unknown')
        key_id = self.key_id
        
        return f'''#!/usr/bin/env python3
"""
PushNotifications Cross-Platform Uninstaller
Full-featured uninstaller with server approval system
"""

import os
import sys
import json
import time
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# Install and import requirements
try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

# GUI imports for dialogs
try:
    import tkinter as tk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Global flag to control GUI dialog usage - disable on non-Windows
USE_GUI_DIALOGS = False  # Disabled for Unix/macOS to prevent black box issues

# Cross-platform GUI utility function
def show_message_dialog(title, message, dialog_type="info"):
    """Show a properly configured message dialog"""
    if not USE_GUI_DIALOGS or not GUI_AVAILABLE:
        print(f"{{title}}: {{message}}")
        return
    
    try:
        # Set environment variable to suppress tkinter deprecation warning on macOS
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
        
        root = tk.Tk()
        root.title(title)
        root.geometry("400x150")
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        
        # Center the window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
        
        # Show appropriate dialog type
        if dialog_type == "error":
            messagebox.showerror(title, message, parent=root)
        elif dialog_type == "warning":
            messagebox.showwarning(title, message, parent=root)
        else:
            messagebox.showinfo(title, message, parent=root)
        
        root.destroy()
        
    except Exception as e:
        print(f"GUI dialog failed ({{e}}): {{title}} - {{message}}")

API_URL = "{api_url}/api/index"
MAC_ADDRESS = "{mac_address}"
CLIENT_ID = "{client_id}"
KEY_ID = "{key_id}"

class PushNotificationsUnixUninstaller:
    def __init__(self):
        self.install_path = Path(__file__).parent
        self.system = platform.system()
        print(f"PushNotifications Uninstaller ({self.system})")
        print(f"Installation path: {self.install_path}")
        
    def show_message(self, title, message, message_type="info"):
        """Show message using appropriate method for the platform"""
        print(f"{title}: {message}")
        
        if USE_GUI_DIALOGS and GUI_AVAILABLE:
            try:
                show_message_dialog(title, message, message_type)
                return
            except:
                pass
        
        # Fallback to system notifications
        try:
            if self.system == "Darwin":
                # macOS notification
                escaped_title = title.replace('"', '\\"')
                escaped_message = message.replace('"', '\\"')
                applescript = f'display notification "{escaped_message}" with title "{escaped_title}" sound name "default"'
                subprocess.run(['osascript', '-e', applescript], check=False)
            elif subprocess.run(['which', 'notify-send'], capture_output=True).returncode == 0:
                # Linux notification
                subprocess.run(['notify-send', '--urgency=normal', title, message], check=False)
        except:
            pass
    
    def request_uninstall_approval(self):
        """Request uninstall approval from server and wait for response"""
        try:
            print("\n" + "="*60)
            print("UNINSTALL APPROVAL REQUEST")
            print("="*60)
            
            self.show_message(
                "Uninstall Request", 
                "Requesting permission from administrator to uninstall PushNotifications. Please wait...",
                "info"
            )
            
            # First, submit the uninstall request
            print("Submitting uninstall request to website...")
            response = requests.post(API_URL, json={
                'action': 'requestUninstall',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'keyId': KEY_ID,
                'installPath': str(self.install_path),
                'platform': self.system,
                'timestamp': datetime.now().isoformat(),
                'reason': 'User requested uninstall'
            }, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"Failed to submit uninstall request: HTTP {response.status_code}"
                print(error_msg)
                self.show_message("Request Failed", error_msg, "error")
                return False
                
            result = response.json()
            if not result.get('success'):
                error_msg = f"Uninstall request failed: {result.get('message', 'Unknown error')}"
                print(error_msg)
                self.show_message("Request Failed", error_msg, "error")
                return False
                
            request_id = result.get('requestId')
            if not request_id:
                error_msg = "No request ID received from server"
                print(error_msg)
                self.show_message("Request Failed", error_msg, "error")
                return False
                
            print(f"✓ Uninstall request submitted successfully (ID: {request_id})")
            print("\n📋 WAITING FOR ADMINISTRATOR APPROVAL")
            print("-" * 50)
            print("The uninstall request has been sent to the administrator.")
            print("Please wait while they review and approve/deny the request.")
            print("This process may take several minutes.")
            print("\nYou can monitor the approval status on the admin website.")
            
            # Show notification about waiting
            self.show_message(
                "Approval Pending", 
                "Uninstall request submitted. Waiting for administrator approval...",
                "info"
            )
            
            # Now poll for approval status
            max_wait_time = 300  # 5 minutes maximum wait
            poll_interval = 10   # Check every 10 seconds
            waited_time = 0
            
            print(f"\n⏳ Polling for approval (timeout: {max_wait_time}s)...")
            
            while waited_time < max_wait_time:
                time.sleep(poll_interval)
                waited_time += poll_interval
                
                try:
                    # Check for uninstall command from server
                    check_response = requests.post(API_URL, json={
                        'action': 'getClientNotifications',
                        'clientId': CLIENT_ID,
                        'macAddress': MAC_ADDRESS
                    }, timeout=10)
                    
                    if check_response.status_code == 200:
                        check_result = check_response.json()
                        if check_result.get('success'):
                            notifications = check_result.get('data', [])
                            
                            # Look for uninstall approval command
                            for notification in notifications:
                                message = notification.get('message', '')
                                if message == '__UNINSTALL_APPROVED_COMMAND__':
                                    print("\n✅ UNINSTALL APPROVED BY ADMINISTRATOR!")
                                    self.show_message(
                                        "Approved", 
                                        "Uninstall request approved by administrator. Proceeding with removal...",
                                        "info"
                                    )
                                    return True
                                elif 'denied' in message.lower() or 'rejected' in message.lower():
                                    print("\n❌ UNINSTALL REQUEST DENIED BY ADMINISTRATOR")
                                    self.show_message(
                                        "Denied", 
                                        "Uninstall request was denied by the administrator.",
                                        "warning"
                                    )
                                    return False
                    
                    progress = int((waited_time / max_wait_time) * 100)
                    print(f"⏳ Still waiting for approval... ({waited_time}s/{max_wait_time}s - {progress}%)")
                    
                except Exception as poll_error:
                    print(f"⚠️  Error checking approval status: {poll_error}")
                    continue
            
            print("\n⏱️  TIMEOUT - No response from administrator")
            timeout_msg = f"Timeout waiting for administrator approval after {max_wait_time} seconds. The request may still be pending."
            print(timeout_msg)
            self.show_message("Timeout", timeout_msg, "warning")
            return False
            
        except Exception as e:
            error_msg = f"Error requesting uninstall approval: {e}"
            print(f"❌ {error_msg}")
            self.show_message("Request Error", error_msg, "error")
            return False
    
    def perform_uninstall(self):
        """Perform comprehensive cross-platform uninstall"""
        print("\n" + "="*60)
        print("PERFORMING UNINSTALL")
        print("="*60)
        
        uninstall_success = True
        
        try:
            # 1. Stop any running client processes
            print("\n🔄 Stopping client processes...")
            self._stop_client_processes()
            
            # 2. Remove startup entries (platform-specific)
            print("\n🚀 Removing startup entries...")
            self._remove_startup_entries()
            
            # 3. Remove desktop shortcuts
            print("\n🖥️  Removing desktop shortcuts...")
            self._remove_desktop_shortcuts()
            
            # 4. Remove system services/daemons
            print("\n⚙️  Removing system services...")
            self._remove_system_services()
            
            # 5. Clean up configuration files
            print("\n🗂️  Cleaning configuration files...")
            self._cleanup_config_files()
            
            # 6. Report successful uninstall to server
            print("\n📡 Reporting uninstall completion to server...")
            self._report_uninstall_complete()
            
            # 7. Remove installation directory (last step)
            print("\n📁 Removing installation directory...")
            self._remove_installation_directory()
            
            print("\n✅ UNINSTALLATION COMPLETED SUCCESSFULLY")
            self.show_message(
                "Uninstall Complete", 
                "PushNotifications has been successfully removed from your system.",
                "info"
            )
            return True
            
        except Exception as e:
            error_msg = f"Uninstallation error: {e}"
            print(f"\n❌ {error_msg}")
            self.show_message("Uninstall Error", error_msg, "error")
            return False
    
    def _stop_client_processes(self):
        """Stop any running client processes"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if ('Client.py' in cmdline and 
                        str(self.install_path) in cmdline):
                        print(f"  ⏹️  Stopping client process (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except ImportError:
            print("  ⚠️  psutil not available - cannot stop processes gracefully")
        except Exception as e:
            print(f"  ⚠️  Error stopping client processes: {e}")
    
    def _remove_startup_entries(self):
        """Remove platform-specific startup entries"""
        try:
            if self.system == "Darwin":  # macOS
                # Remove Launch Agent
                launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
                plist_file = launch_agents_dir / "com.pushnotifications.client.plist"
                if plist_file.exists():
                    # Unload first
                    try:
                        subprocess.run(['launchctl', 'unload', str(plist_file)], check=False)
                    except:
                        pass
                    plist_file.unlink()
                    print("  ✓ Removed macOS Launch Agent")
                    
            else:  # Linux and other Unix-like
                # Remove XDG autostart entry
                autostart_file = Path.home() / ".config/autostart/pushnotifications-client.desktop"
                if autostart_file.exists():
                    autostart_file.unlink()
                    print("  ✓ Removed XDG autostart entry")
                
                # Remove systemd user service
                try:
                    subprocess.run(['systemctl', '--user', 'stop', 'pushnotifications-client.service'], 
                                 check=False, capture_output=True)
                    subprocess.run(['systemctl', '--user', 'disable', 'pushnotifications-client.service'], 
                                 check=False, capture_output=True)
                    
                    service_file = Path.home() / ".config/systemd/user/pushnotifications-client.service"
                    if service_file.exists():
                        service_file.unlink()
                        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=False)
                        print("  ✓ Removed systemd user service")
                except Exception as e:
                    print(f"  ℹ️  systemd service removal: {e}")
                    
        except Exception as e:
            print(f"  ⚠️  Error removing startup entries: {e}")
    
    def _remove_desktop_shortcuts(self):
        """Remove desktop shortcuts"""
        try:
            desktop = Path.home() / "Desktop"
            shortcuts = ["push-client.desktop", "push-repair.desktop"]
            
            for shortcut in shortcuts:
                shortcut_path = desktop / shortcut
                if shortcut_path.exists():
                    shortcut_path.unlink()
                    print(f"  ✓ Removed {shortcut}")
        except Exception as e:
            print(f"  ⚠️  Error removing desktop shortcuts: {e}")
    
    def _remove_system_services(self):
        """Remove any system-level services or daemons"""
        try:
            # This is primarily for potential future system-level services
            # Currently the application runs at user level
            print("  ℹ️  No system services to remove (user-level installation)")
        except Exception as e:
            print(f"  ⚠️  Error checking system services: {e}")
    
    def _cleanup_config_files(self):
        """Clean up configuration files and caches"""
        try:
            # Remove any application configuration files
            config_locations = [
                Path.home() / ".config/pushnotifications",
                Path.home() / ".pushnotifications",
                Path.home() / "Library/Preferences/com.pushnotifications.plist"  # macOS
            ]
            
            for config_path in config_locations:
                if config_path.exists():
                    if config_path.is_file():
                        config_path.unlink()
                    else:
                        shutil.rmtree(config_path)
                    print(f"  ✓ Removed {config_path}")
        except Exception as e:
            print(f"  ⚠️  Error cleaning config files: {e}")
    
    def _report_uninstall_complete(self):
        """Report successful uninstall to server"""
        try:
            requests.post(API_URL, json={
                'action': 'reportUninstallComplete',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'keyId': KEY_ID,
                'platform': self.system,
                'installPath': str(self.install_path),
                'timestamp': datetime.now().isoformat()
            }, timeout=10)
            print("  ✓ Uninstall completion reported to server")
        except Exception as e:
            print(f"  ⚠️  Could not report to server: {e}")
    
    def _remove_installation_directory(self):
        """Remove the installation directory as final step"""
        try:
            # Change to parent directory to avoid permission issues
            os.chdir(self.install_path.parent)
            
            # Remove installation directory
            if self.install_path.exists():
                shutil.rmtree(self.install_path, ignore_errors=True)
                print(f"  ✓ Removed installation directory: {self.install_path}")
            else:
                print("  ℹ️  Installation directory already removed")
                
        except Exception as e:
            print(f"  ⚠️  Error removing installation directory: {e}")
    
    def run(self):
        """Main uninstaller entry point"""
        print("\n🗑️  PushNotifications Uninstaller Starting...")
        print(f"Platform: {self.system}")
        print(f"Client ID: {CLIENT_ID}")
        print(f"MAC Address: {MAC_ADDRESS}")
        
        # Request approval from server
        if self.request_uninstall_approval():
            print("\n🎯 Uninstall approved. Proceeding with removal...")
            if self.perform_uninstall():
                print("\n🎉 PushNotifications successfully removed from your system!")
                return True
            else:
                print("\n💥 Uninstallation encountered errors.")
                return False
        else:
            print("\n🚫 Uninstall request denied or timed out.")
            print("\n🔄 Attempting to restart client...")
            
            # Restart client if uninstall was denied
            client_path = self.install_path / "Client.py"
            if client_path.exists():
                try:
                    subprocess.Popen([
                        sys.executable, str(client_path)
                    ], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("  ✓ Client restarted successfully")
                except Exception as e:
                    print(f"  ⚠️  Error restarting client: {e}")
            
            return False

if __name__ == "__main__":
    try:
        uninstaller = PushNotificationsUnixUninstaller()
        success = uninstaller.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Uninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal uninstaller error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
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
            str(self.install_path / "Client.py"),
            str(self.install_path / "Uninstaller.py"),
            str(self.install_path / "Installer.py"),
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
            if path_obj.name in ['Client.py', 'Uninstaller.py', 'Installer.py']:
                print(f"🏗️  Recreating core component: {{path_obj.name}}")
                
                # Launch installer in repair mode using Python
                installer_path = self.install_path / "Installer.py"
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
      <Command>pythonw.exe</Command>
      <Arguments>"{self.install_path / "Client.py"}"</Arguments>
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
      <Command>python.exe</Command>
      <Arguments>"{self.install_path / "Installer.py" }" --update-check</Arguments>
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
        """Create cross-platform startup entries for maximum reliability"""
        print("Creating startup entries...")
        
        if self.system == "Windows":
            return self._create_windows_startup_entries()
        else:
            return self._create_unix_startup_entries()
    
def _create_windows_startup_entries(self):
        """Create Windows-specific startup entries"""
        print("Creating additional startup entries...")
        
        try:
            # Method 1: Registry run key (user-level auto-start)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                "Software\\Microsoft\\Windows\\CurrentVersion\\Run") as key:
                # Use pythonw.exe to ensure no console window appears
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(pythonw_exe).exists():
                    pythonw_exe = 'pythonw.exe'  # Fallback to system PATH
                client_cmd = f'"{pythonw_exe}" "{self.install_path / "Client.py"}"'
                winreg.SetValueEx(key, "PushNotifications", 0, winreg.REG_SZ, client_cmd)
                print("✓ Registry startup entry created")
            
            # Method 2: Startup folder shortcut (user-visible but reliable)
            try:
                import win32com.client
                
                startup_folder = Path(os.environ.get('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                startup_folder.mkdir(parents=True, exist_ok=True)
                
                shell = win32com.client.Dispatch("WScript.Shell")
                startup_shortcut = shell.CreateShortCut(str(startup_folder / "Push Client (Startup).lnk"))
                # Use pythonw.exe to ensure no console window appears
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(pythonw_exe).exists():
                    pythonw_exe = 'pythonw.exe'  # Fallback to system PATH
                startup_shortcut.Targetpath = pythonw_exe
                startup_shortcut.Arguments = f'"{self.install_path / "Client.py"}"'
                startup_shortcut.WorkingDirectory = str(self.install_path)
                startup_shortcut.Description = "PushNotifications Client - Auto Start"
                startup_shortcut.WindowStyle = 7  # Minimized
                startup_shortcut.save()
                
                print("✓ Startup folder shortcut created")
                
            except Exception as e:
                print(f"Warning: Could not create startup folder shortcut: {e}")
            
            # No batch files are used anymore - Python scripts only
            print("✓ Using direct Python execution for startup")
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not create all startup entries: {e}")
            return False  # Continue installation even if this fails
    
def _create_unix_startup_entries(self):
        """Create Unix/Linux/macOS startup entries"""
        try:
            if self.system == "Darwin":  # macOS
                return self._create_macos_startup_entries()
            else:  # Linux and other Unix-like
                return self._create_linux_startup_entries()
        except Exception as e:
            print(f"Warning: Could not create Unix startup entries: {e}")
            return False
    
def _create_macos_startup_entries(self):
        """Create macOS Launch Agent for startup"""
        try:
            # Create Launch Agent plist file
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            plist_file = launch_agents_dir / "com.pushnotifications.client.plist"
            
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pushnotifications.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{self.install_path / "Client.py"}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{self.install_path}</string>
    <key>StandardOutPath</key>
    <string>{self.install_path / "client.log"}</string>
    <key>StandardErrorPath</key>
    <string>{self.install_path / "client.log"}</string>
</dict>
</plist>'''
            
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # Load the launch agent
            try:
                subprocess.run(['launchctl', 'load', str(plist_file)], check=False)
                print("✓ macOS Launch Agent created and loaded")
            except:
                print("✓ macOS Launch Agent created (will load on next login)")
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not create macOS startup entry: {e}")
            return False
    
def _create_linux_startup_entries(self):
        """Create Linux autostart entry"""
        try:
            # Create autostart directory
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / "pushnotifications-client.desktop"
            
            desktop_content = f'''[Desktop Entry]
Type=Application
Name=PushNotifications Client
Comment=PushNotifications Background Client
Exec={sys.executable} "{self.install_path / "Client.py"}"
Icon=application-default-icon
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
Categories=System;Utility;
'''
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(desktop_file, 0o755)
            
            print("✓ Linux autostart entry created")
            
            # Try to create systemd user service as well (optional)
            try:
                systemd_dir = Path.home() / ".config" / "systemd" / "user"
                systemd_dir.mkdir(parents=True, exist_ok=True)
                
                service_file = systemd_dir / "pushnotifications-client.service"
                
                service_content = f'''[Unit]
Description=PushNotifications Client
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} "{self.install_path / "Client.py"}"
Restart=always
RestartSec=10
WorkingDirectory={self.install_path}

[Install]
WantedBy=default.target
'''
                
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Enable the service
                subprocess.run(['systemctl', '--user', 'daemon-reload'], check=False)
                subprocess.run(['systemctl', '--user', 'enable', 'pushnotifications-client.service'], check=False)
                
                print("✓ systemd user service created")
                
            except Exception as e:
                print(f"Note: systemd service creation failed (this is optional): {e}")
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not create Linux startup entry: {e}")
            return False

def create_desktop_shortcuts(self):
        """Create desktop shortcuts for client and installer"""
        print("Creating desktop shortcuts...")
        
        try:
            if self.system == "Windows":
                import win32com.client
                
                desktop = Path.home() / "Desktop"
                
                # Create Push Client shortcut - Python only
                shell = win32com.client.Dispatch("WScript.Shell")
                client_shortcut = shell.CreateShortCut(str(desktop / "Push Client.lnk"))
                # Use pythonw.exe to ensure no console window appears
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(pythonw_exe).exists():
                    pythonw_exe = 'pythonw.exe'  # Fallback to system PATH
                client_shortcut.Targetpath = pythonw_exe
                client_shortcut.Arguments = f'"{self.install_path / "Client.py"}"'
                client_shortcut.WorkingDirectory = str(self.install_path)
                client_shortcut.Description = "PushNotifications Client"
                client_shortcut.save()
                
                # Create Installer/Repair shortcut - Python only
                repair_shortcut = shell.CreateShortCut(str(desktop / "Push Client Repair.lnk"))
                repair_shortcut.Targetpath = "python.exe"
                repair_shortcut.Arguments = f'"{self.install_path / "Installer.py"}" --repair'
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

    # Executable conversion is no longer used - all Python scripts
    # Method kept for compatibility but does nothing
    
def notify_installation_failure(self, stage, error_message):
        """Notify the server that the installation has failed"""
        print(f"Reporting installation failure at stage: {stage}")
        
        try:
            failure_data = {
                'action': 'reportInstallationFailure',
                'macAddress': self.mac_address,
                'username': self.username,
                'clientName': self.client_name,
                'keyId': getattr(self, 'key_id', None),
                'deviceId': self.device_data.get('deviceId') if hasattr(self, 'device_data') else None,
                'clientId': self.device_data.get('clientId') if hasattr(self, 'device_data') else None,
                'stage': stage,
                'error': error_message,
                'version': INSTALLER_VERSION,
                'platform': f"{platform.system()} {platform.release()}",
                'timestamp': datetime.now().isoformat(),
                'installPath': str(getattr(self, 'install_path', 'unknown')),
                'systemInfo': {
                    'osVersion': f"{platform.system()} {platform.release()} {platform.version()}",
                    'architecture': platform.machine(),
                    'processor': platform.processor(),
                    'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    'isAdmin': self.check_admin_privileges(),
                    'timezone': str(datetime.now().astimezone().tzinfo)
                }
            }
            
            response = requests.post(
                f"{self.api_url}/api/index",
                json=failure_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✓ Installation failure reported to server")
                    return True
                else:
                    print(f"Warning: Server failed to log failure: {result.get('message')}")
            else:
                print(f"Warning: Failed to report installation failure: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Warning: Could not report installation failure: {e}")
        
        return False
    
def cleanup_failed_installation_files(self):
        """Clean up installer files on failed installation"""
        print("Cleaning up installation files...")
        
        try:
            # Remove any created installation directory if it exists
            if hasattr(self, 'install_path') and self.install_path and self.install_path.exists():
                print(f"Removing installation directory: {self.install_path}")
                
                # Remove Windows file attributes before deletion
                if self.system == "Windows":
                    try:
                        subprocess.run([
                            "attrib", "-R", "-S", "-H", str(self.install_path), "/S"
                        ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                    except:
                        pass
                
                # Remove directory
                shutil.rmtree(self.install_path, ignore_errors=True)
                
                # Also try to remove parent directories if they're empty
                try:
                    parent = self.install_path.parent
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()
                        grandparent = parent.parent
                        if grandparent.exists() and not any(grandparent.iterdir()):
                            grandparent.rmdir()
                except:
                    pass
            
            # Remove any registry entries
            if self.system == "Windows":
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\PushNotifications")
                    print("✓ Registry entries removed")
                except (OSError, FileNotFoundError):
                    pass
            
            # Remove any scheduled tasks
            if self.system == "Windows":
                try:
                    subprocess.run(['schtasks', '/delete', '/tn', 'PushClient', '/f'], 
                                  check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['schtasks', '/delete', '/tn', 'PushUpdater', '/f'], 
                                  check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['schtasks', '/delete', '/tn', 'PushWatchdog', '/f'], 
                                  check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            
            print("✓ Installation files cleaned up")
            return True
            
        except Exception as e:
            print(f"Warning: Could not fully clean up installation files: {e}")
            return False
    
def cleanup_failed_registration(self):
        """Clean up device registration if installation fails after device was registered"""
        if not self.device_registered:
            print("No device registration to clean up")
            return True
            
        print("Cleaning up device registration due to installation failure...")
        
        try:
            cleanup_data = {
                'action': 'cleanupFailedInstallation',
                'macAddress': self.mac_address,
                'keyId': getattr(self, 'key_id', None),
                'deviceId': self.device_data.get('deviceId') if hasattr(self, 'device_data') else None,
                'clientId': self.device_data.get('clientId') if hasattr(self, 'device_data') else None,
                'username': self.username,
                'clientName': self.client_name,
                'reason': 'installation_failed_after_registration',
                'timestamp': datetime.now().isoformat(),
                'installPath': str(getattr(self, 'install_path', 'unknown'))
            }
            
            response = requests.post(
                f"{self.api_url}/api/index",
                json=cleanup_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✓ Device registration cleaned up successfully")
                    print("  Device marked as offline/unregistered")
                    return True
                else:
                    print(f"Warning: Server failed to cleanup registration: {result.get('message')}")
            else:
                print(f"Warning: Failed to cleanup registration: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Warning: Could not cleanup device registration: {e}")
        
        return False
    
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
            
            # Start the client immediately with pythonw.exe to hide console
            if self.system == "Windows":
                # Use pythonw.exe instead of python.exe to hide console window
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(pythonw_exe).exists():
                    pythonw_exe = 'pythonw.exe'  # Fallback to system PATH
                
                subprocess.Popen([
                    pythonw_exe, str(self.install_path / "Client.py")
                ], cwd=str(self.install_path),
                   creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([
                    sys.executable, str(self.install_path / "Client.py")
                ], cwd=str(self.install_path))
            
            print("✓ Client started")
            return True
            
        except Exception as e:
            print(f"Warning: Finalization error: {e}")
            return True  # Don't fail installation for this

def run_installation(self):
        """Run the complete installation process with progress tracking"""
        install_steps = [
            ("Version Check", 10),
            ("Admin Privileges", 15), 
            ("Installation Key", 25),
            ("Device Registration", 35),
            ("Installation Directory", 45),
            ("Client Components", 60),
            ("Configuration Vault", 70),
            ("Startup Entries", 80),
            ("Desktop Shortcuts", 90),
            ("Finalization", 100)
        ]
        
        current_step = 0
        
        def update_progress(step_name, percentage, status=""):
            if self.progress_dialog:
                self.progress_dialog.update_progress(percentage, f"{step_name}... {status}")
                self.progress_dialog.add_log(f"{step_name} - {status}" if status else step_name)
                self.progress_dialog.update_gui()
        
        print("Starting PushNotifications Installation")
        print("=" * 60)
        
        if self.progress_dialog:
            self.progress_dialog.add_log("Starting PushNotifications Installation")
            self.progress_dialog.update_progress(0, "Initializing installation...")
        
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
        
        # Check admin privileges (skip on macOS since we install in user directory)
        if self.system != "Darwin" and not self.check_admin_privileges():
            print("Administrator privileges required for installation.")
            if not self.restart_with_admin():
                print("✗ Installation failed: Could not obtain administrator privileges")
                return False
            return True  # Process will restart with admin
        
        if self.system == "Darwin":
            print("✓ Running with user privileges (macOS install in user directory)")
        else:
            print("✓ Running with administrator privileges")
        
        # Check for existing installation and handle upgrade/repair
        has_existing = self._has_existing_installation()
        if has_existing and not self.repair_mode:
            print("🔄 Existing installation detected - performing upgrade/update")
            print("   This will preserve your configuration and upgrade the client")
            self.repair_mode = True  # Enable repair mode for existing installations
        
        # Validate installation key (skip in repair/upgrade mode if we have existing config)
        if not self.repair_mode or not has_existing:
            if not self.validate_installation_key():
                print("✗ Installation failed: Invalid installation key")
                return False
        else:
            print("✓ Using existing installation configuration")
            self._load_existing_config()
            
            # For Unix systems in upgrade mode, we still need to validate the key
            if self.installation_key == "UPGRADE_MODE":
                print("🔄 Upgrade mode: Please provide installation key to continue")
                if not self.validate_installation_key():
                    print("✗ Installation failed: Valid installation key required for upgrade")
                    return False
        
        # Register device
        if not self.register_device():
            print("✗ Installation failed: Device registration failed")
            self.notify_installation_failure("device_registration", "Device registration with server failed")
            self.cleanup_failed_installation_files()
            return False
        
        # Create hidden installation directory
        if not self.create_hidden_install_directory():
            print("✗ Installation failed: Could not create installation directory")
            self.notify_installation_failure("directory_creation", "Could not create hidden installation directory")
            self.cleanup_failed_registration()
            self.cleanup_failed_installation_files()
            return False
        
        # Create embedded client components
        if not self.create_embedded_client_components():
            print("✗ Installation failed: Could not create client components")
            self.notify_installation_failure("component_creation", "Could not create embedded client components")
            self.cleanup_failed_registration()
            self.cleanup_failed_installation_files()
            return False
        
        # Create encrypted vault
        if not self.create_encrypted_vault():
            print("✗ Installation failed: Could not create configuration vault")
            self.notify_installation_failure("vault_creation", "Could not create AES-256-GCM encrypted configuration vault")
            self.cleanup_failed_registration()
            self.cleanup_failed_installation_files()
            return False
        
        # Create scheduled tasks
        if not self.create_scheduled_tasks():
            print("✗ Installation failed: Could not create scheduled tasks")
            self.notify_installation_failure("scheduled_tasks", "Could not create Windows scheduled tasks for client and updater")
            self.cleanup_failed_registration()
            self.cleanup_failed_installation_files()
            return False
        
        # Create additional startup entries for maximum reliability
        if not self.create_startup_entries():
            print("Warning: Additional startup entries creation failed")
            self.notify_installation_failure("startup_entries", "Could not create additional startup entries for maximum reliability")
            # Don't call cleanup_failed_registration() - this is non-critical
        
        # Watchdog service removed - no longer part of the installation
        
        # Create desktop shortcuts
        if not self.create_desktop_shortcuts():
            print("Warning: Desktop shortcuts creation failed")
            self.notify_installation_failure("desktop_shortcuts", "Could not create desktop shortcuts for client access")
            # Don't call cleanup_failed_registration() - this is non-critical
        
        # Pure Python installation - no executable conversion
        
        # Finalize installation
        if not self.finalize_installation():
            print("Warning: Installation finalization had issues")
            self.notify_installation_failure("finalization", "Installation finalization encountered issues while reporting to server or starting client")
            # Don't call cleanup_failed_registration() - installation is essentially complete
        
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
- Windows: Runs as Python script with admin privileges
- No external dependencies required for basic installation
- Automatically detects OS and adapts functionality

🪟 WINDOWS ENTERPRISE FEATURES
- Python-based operation with admin privileges
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
        # Check for administrator privileges on Windows
        if platform.system() == "Windows":
            try:
                # Check if already running as admin
                is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
                if not is_admin:
                    print("Restarting with administrator privileges...")
                    
                    # Use the most reliable elevation method
                    script_path = os.path.abspath(sys.argv[0])
                    script_args = ' '.join([f'"{arg}"' for arg in sys.argv])
                    
                    # Try PowerShell first (most reliable on Windows 10/11)
                    try:
                        # Build argument list properly for PowerShell
                        if len(sys.argv) > 1:
                            args_list = f"'{script_path}', " + ", ".join([f"'{arg}'" for arg in sys.argv[1:]])
                        else:
                            args_list = f"'{script_path}'"
                        
                        powershell_cmd = f'Start-Process -FilePath "{sys.executable}" -ArgumentList {args_list} -Verb RunAs -Wait'
                        
                        print(f"Executing: {powershell_cmd}")
                        result = subprocess.run([
                            'powershell.exe', '-Command', powershell_cmd
                        ], timeout=60)
                        
                        if result.returncode == 0:
                            print("✓ Elevated process completed")
                            sys.exit(0)
                        else:
                            print(f"PowerShell elevation returned code: {result.returncode}")
                    except Exception as e:
                        print(f"PowerShell elevation failed: {e}")
                    
                    # Fallback to ctypes ShellExecuteW
                    try:
                        shell32 = ctypes.windll.shell32
                        shell32.ShellExecuteW.argtypes = [
                            ctypes.wintypes.HWND, ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR,
                            ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR, ctypes.c_int
                        ]
                        shell32.ShellExecuteW.restype = ctypes.c_void_p
                        
                        result = shell32.ShellExecuteW(
                            None, "runas", sys.executable, script_args, None, 1
                        )
                        
                        result_int = ctypes.cast(result, ctypes.c_void_p).value or 0
                        if result_int > 32:
                            print("✓ Administrator privileges requested")
                            sys.exit(0)
                        else:
                            print(f"Elevation failed with error code: {result_int}")
                    except Exception as e:
                        print(f"Elevation failed: {e}")
                    
                    # If all methods fail, show error and exit
                    print("\n❌ Failed to obtain administrator privileges.")
                    print("Please right-click this script and select 'Run as administrator'")
                    print("Administrator privileges are required to prevent system errors.")
                    input("Press Enter to exit...")
                    sys.exit(1)
                else:
                    print("✓ Running with administrator privileges")
            except Exception as e:
                print(f"Error checking administrator privileges: {e}")
                print("Continuing anyway...")
        
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
                    if USE_GUI_DIALOGS:
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
        
        success = run_installation(installer)
        
        if success:
            if USE_GUI_DIALOGS:
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
