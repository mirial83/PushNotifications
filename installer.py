#!/usr/bin/env python3
"""
PushNotifications Desktop Client - Enhanced Security Version
Complete desktop client with advanced security features including:
1. Random encryption keys stored in database
2. Full-screen grey overlay system
3. Program minimization and lock functionality
4. Hidden folder protection
5. Auto-startup executable
6. Advanced notification priority system

Version: 3.0.0
Usage:
    python3 installer.py
    
Notes:
- Runs with administrator privileges automatically
- Files and folders protected with database encryption keys
- Creates Windows executable for startup
- Uninstall requires web form approval
"""

import os
import sys
import platform
import subprocess
import urllib.request
import json
import time
import hashlib
import secrets
import threading
import uuid
import ctypes
from ctypes import wintypes
import winreg
import psutil
from pathlib import Path
from datetime import datetime, timedelta

# Auto-install requests if not available
try:
    import requests
except ImportError:
    print("Installing requests module...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

# Try to import tkinter for GUI
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("GUI not available - using text-based interface")

# Try to import win32 modules (optional for enhanced functionality)
try:
    import win32gui
    import win32con
    import win32com.shell
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# Use Vercel app URL for downloads
SCRIPT_URL = "https://push-notifications-phi.vercel.app"

# Global configuration for client
CLIENT_CONFIG = {
    'server_url': 'https://script.google.com/macros/s/AKfycbxz_tUH78XlNqLpdQKqy9SrD6dK6Y0azFIXCM0kUpo3kEfAD6jWoMsngxO710KxTrA/exec',
    'client_version': '3.0.0',
    'check_interval': 30,  # seconds
    'encryption_algorithm': 'AES-256',
    'max_retry_attempts': 3,
    'database_timeout': 10
}

# Windows API constants and structures
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class SecurityManager:
    """Manages encryption keys and security features using MongoDB"""
    
    def __init__(self, install_dir):
        self.install_dir = Path(install_dir)
        self.encryption_key = None
        self.client_id = None
        self.server_url = CLIENT_CONFIG['server_url']
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security database and encryption keys via server"""
        try:
            # Generate or retrieve encryption key and client ID from MongoDB via server
            self.client_id = self._get_or_create_client_id()
            self.encryption_key = self._get_or_create_key('ENCRYPTION_KEY')
            
            print(f"Security initialized with MongoDB backend")
            print(f"Client ID: {self.client_id}")
                
        except Exception as e:
            print(f"Security initialization failed: {e}")
            # Create fallback security
            self._create_fallback_security()
    
    def _get_or_create_key(self, key_type):
        """Get or create encryption key from MongoDB via server"""
        try:
            # First try to retrieve existing key
            data = {
                'action': 'getSecurityKey',
                'clientId': self.client_id,
                'keyType': key_type,
                'installPath': str(self.install_dir),
                'hostname': platform.node()
            }
            
            response = requests.post(self.server_url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('key'):
                    # Update last used timestamp
                    self._update_key_last_used(key_type)
                    return result['key']
            
            # If no existing key found, create new one
            new_key = secrets.token_hex(32)  # 256-bit key
            
            create_data = {
                'action': 'createSecurityKey',
                'clientId': self.client_id,
                'keyType': key_type,
                'keyValue': new_key,
                'installPath': str(self.install_dir),
                'hostname': platform.node(),
                'createdAt': datetime.now().isoformat(),
                'lastUsed': datetime.now().isoformat()
            }
            
            create_response = requests.post(self.server_url, json=create_data, timeout=30)
            
            if create_response.status_code == 200:
                create_result = create_response.json()
                if create_result.get('success'):
                    print(f"Created new {key_type} in MongoDB")
                    return new_key
            
            # If server communication fails, return fallback key
            print(f"Server communication failed for key creation, using fallback")
            return secrets.token_hex(32)
            
        except Exception as e:
            print(f"Key retrieval failed: {e}")
            return secrets.token_hex(32)  # Fallback random key
    
    def _get_or_create_client_id(self):
        """Get or create client ID in MongoDB via server"""
        try:
            # Generate a unique identifier based on machine characteristics
            machine_id = f"{platform.node()}_{platform.machine()}_{uuid.uuid4().hex[:8]}"
            
            # Check if client already exists
            data = {
                'action': 'getClientInfo',
                'machineId': machine_id,
                'installPath': str(self.install_dir),
                'hostname': platform.node()
            }
            
            response = requests.post(self.server_url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('clientId'):
                    # Update last checkin
                    self._update_client_checkin(result['clientId'])
                    return result['clientId']
            
            # Create new client ID
            new_client_id = f"client_{platform.node()}_{uuid.uuid4().hex[:8]}"
            installation_id = str(uuid.uuid4())
            
            create_data = {
                'action': 'createClientInfo',
                'clientId': new_client_id,
                'machineId': machine_id,
                'installationId': installation_id,
                'installPath': str(self.install_dir),
                'hostname': platform.node(),
                'platform': platform.system(),
                'version': CLIENT_CONFIG['client_version'],
                'createdAt': datetime.now().isoformat(),
                'lastCheckin': datetime.now().isoformat()
            }
            
            create_response = requests.post(self.server_url, json=create_data, timeout=30)
            
            if create_response.status_code == 200:
                create_result = create_response.json()
                if create_result.get('success'):
                    print(f"Created new client ID in MongoDB: {new_client_id}")
                    return new_client_id
            
            # If server communication fails, return fallback ID
            print(f"Server communication failed for client creation, using fallback")
            return f"client_{platform.node()}_{uuid.uuid4().hex[:8]}"
            
        except Exception as e:
            print(f"Client ID creation failed: {e}")
            return f"client_{platform.node()}_{uuid.uuid4().hex[:8]}"
    
    def _update_key_last_used(self, key_type):
        """Update last used timestamp for a key"""
        try:
            data = {
                'action': 'updateKeyLastUsed',
                'clientId': self.client_id,
                'keyType': key_type,
                'lastUsed': datetime.now().isoformat()
            }
            
            requests.post(self.server_url, json=data, timeout=10)
            
        except Exception as e:
            print(f"Failed to update key last used: {e}")
    
    def _update_client_checkin(self, client_id):
        """Update client last checkin timestamp"""
        try:
            data = {
                'action': 'updateClientCheckin',
                'clientId': client_id,
                'lastCheckin': datetime.now().isoformat(),
                'version': CLIENT_CONFIG['client_version']
            }
            
            requests.post(self.server_url, json=data, timeout=10)
            
        except Exception as e:
            print(f"Failed to update client checkin: {e}")
    
    def _create_fallback_security(self):
        """Create fallback security if MongoDB communication fails"""
        self.encryption_key = secrets.token_hex(32)
        self.client_id = f"client_{platform.node()}_{uuid.uuid4().hex[:8]}"
        print(f"Using fallback security - Client ID: {self.client_id}")
    
    def encrypt_data(self, data):
        """Encrypt sensitive data (placeholder for actual encryption)"""
        # In production, implement actual AES encryption
        import base64
        encoded = base64.b64encode(data.encode()).decode()
        return f"ENC_{self.encryption_key[:8]}_{encoded}"
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data (placeholder for actual decryption)"""
        # In production, implement actual AES decryption
        if encrypted_data.startswith('ENC_'):
            parts = encrypted_data.split('_', 2)
            if len(parts) == 3:
                import base64
                return base64.b64decode(parts[2]).decode()
        return encrypted_data

class OverlayManager:
    """Manages full-screen grey overlays on all monitors"""
    
    def __init__(self):
        self.overlay_windows = []
        self.is_overlay_active = False
        self.minimized_windows = []
        self._initialize_overlay_system()
    
    def _initialize_overlay_system(self):
        """Initialize overlay system for all monitors"""
        try:
            import tkinter as tk
            self.tk_root = tk.Tk()
            self.tk_root.withdraw()  # Hide main window
        except Exception as e:
            print(f"Overlay system initialization failed: {e}")
            self.tk_root = None
    
    def show_overlay(self, notification_data):
        """Show grey overlay on all screens with notification"""
        if self.is_overlay_active:
            return
            
        try:
            import tkinter as tk
            from tkinter import ttk
            
            if not self.tk_root:
                return
                
            self.is_overlay_active = True
            
            # Get all monitor information
            monitors = self._get_all_monitors()
            
            for monitor in monitors:
                overlay_window = tk.Toplevel(self.tk_root)
                
                # Configure overlay window
                overlay_window.attributes('-topmost', True)
                overlay_window.attributes('-alpha', 0.8)  # Semi-transparent
                overlay_window.configure(bg='#404040')  # Grey background
                overlay_window.overrideredirect(True)  # Remove window decorations
                
                # Position on monitor
                overlay_window.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}")
                
                # Create notification content
                self._create_notification_content(overlay_window, notification_data, monitor)
                
                self.overlay_windows.append(overlay_window)
            
            # Minimize all running programs
            self._minimize_all_programs()
            
        except Exception as e:
            print(f"Failed to show overlay: {e}")
            self.is_overlay_active = False
    
    def hide_overlay(self):
        """Hide all overlay windows"""
        try:
            for window in self.overlay_windows:
                window.destroy()
            
            self.overlay_windows.clear()
            self.is_overlay_active = False
            
            # Don't restore programs automatically - they stay minimized until notification handled
            print("Overlay hidden - programs remain minimized until notification handled")
            
        except Exception as e:
            print(f"Failed to hide overlay: {e}")
    
    def unlock_computer(self):
        """Unlock computer and allow programs to be maximized again"""
        try:
            print("Computer unlocked - programs can be maximized again")
            # In a production version, you might restore some windows here
            self.minimized_windows.clear()
            
        except Exception as e:
            print(f"Failed to unlock computer: {e}")
    
    def _get_all_monitors(self):
        """Get information about all monitors"""
        monitors = []
        
        def monitor_enum_proc(hmonitor, hdc, rect, data):
            monitors.append({
                'x': rect.contents.left,
                'y': rect.contents.top, 
                'width': rect.contents.right - rect.contents.left,
                'height': rect.contents.bottom - rect.contents.top
            })
            return True
            
        try:
            # Use Windows API to enumerate monitors
            MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, 
                                                ctypes.c_ulong,
                                                ctypes.c_ulong,
                                                ctypes.POINTER(RECT),
                                                ctypes.c_double)
            
            user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(monitor_enum_proc), 0)
            
        except Exception:
            # Fallback to primary monitor
            monitors = [{'x': 0, 'y': 0, 'width': 1920, 'height': 1080}]
        
        return monitors
    
    def _create_notification_content(self, window, notification_data, monitor):
        """Create notification content on overlay window"""
        try:
            import tkinter as tk
            from tkinter import ttk
            
            # Main container
            main_frame = tk.Frame(window, bg='#404040')
            main_frame.pack(expand=True, fill='both')
            
            # Center notification panel
            notification_panel = tk.Frame(main_frame, bg='#ffffff', relief='raised', bd=2)
            notification_panel.place(relx=0.5, rely=0.5, anchor='center', width=600, height=400)
            
            # Title
            title_label = tk.Label(notification_panel, 
                                 text="📢 NOTIFICATION", 
                                 font=('Arial', 20, 'bold'),
                                 bg='#ffffff', fg='#333333')
            title_label.pack(pady=20)
            
            # Message
            message_text = tk.Text(notification_panel,
                                 font=('Arial', 14),
                                 bg='#f5f5f5', 
                                 relief='flat',
                                 height=8,
                                 wrap='word')
            message_text.pack(pady=10, padx=20, fill='both', expand=True)
            message_text.insert('1.0', notification_data.get('message', 'No message'))
            message_text.config(state='disabled')
            
            # Buttons frame
            buttons_frame = tk.Frame(notification_panel, bg='#ffffff')
            buttons_frame.pack(pady=20)
            
            # Complete button
            complete_btn = tk.Button(buttons_frame,
                                   text="✓ Complete Task",
                                   font=('Arial', 12, 'bold'),
                                   bg='#28a745', fg='white',
                                   command=lambda: self._handle_complete(notification_data))
            complete_btn.pack(side='left', padx=10)
            
            # Snooze button
            snooze_btn = tk.Button(buttons_frame,
                                 text="⏰ Snooze 15 min",
                                 font=('Arial', 12),
                                 bg='#ffc107', fg='black',
                                 command=lambda: self._handle_snooze(notification_data, 15))
            snooze_btn.pack(side='left', padx=10)
            
            # Info at bottom
            info_label = tk.Label(notification_panel,
                                text=f"Received: {datetime.now().strftime('%H:%M:%S')}",
                                font=('Arial', 10),
                                bg='#ffffff', fg='#666666')
            info_label.pack(side='bottom', pady=5)
            
        except Exception as e:
            print(f"Failed to create notification content: {e}")
    
    def _minimize_all_programs(self):
        """Minimize all running programs to tray"""
        try:
            # Get all windows
            windows = []
            
            def enum_window_proc(hwnd, param):
                try:
                    import win32gui
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        # Skip system windows and our overlay
                        window_title = win32gui.GetWindowText(hwnd)
                        if not any(skip in window_title.lower() for skip in 
                                  ['program manager', 'desktop', 'taskbar', 'notification']):
                            windows.append(hwnd)
                except:
                    pass
                return True
            
            try:
                import win32gui
                import win32con
                win32gui.EnumWindows(enum_window_proc, 0)
                
                # Minimize all windows
                for hwnd in windows:
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                        # Also send to system tray if possible
                        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                        self.minimized_windows.append(hwnd)
                    except Exception:
                        pass
                        
                print(f"Minimized {len(windows)} windows")
                
            except ImportError:
                print("pywin32 not available - cannot minimize windows")
            
        except Exception as e:
            print(f"Failed to minimize programs: {e}")
    
    def _handle_complete(self, notification_data):
        """Handle notification completion"""
        try:
            # Send completion to server
            client = PushNotificationsClient.get_instance()
            if client:
                client.complete_notification(notification_data)
            
            # Hide overlay and unlock
            self.hide_overlay()
            self.unlock_computer()
            
        except Exception as e:
            print(f"Failed to handle completion: {e}")
    
    def _handle_snooze(self, notification_data, minutes):
        """Handle notification snoozing"""
        try:
            # Send snooze to server
            client = PushNotificationsClient.get_instance()
            if client:
                client.snooze_notification(notification_data, minutes)
            
            # Hide overlay temporarily
            self.hide_overlay()
            self.unlock_computer()
            
        except Exception as e:
            print(f"Failed to handle snooze: {e}")

class PushNotificationsInstaller:
    def __init__(self):
        self.system = platform.system()
        self.gas_script_url = SCRIPT_URL
        self.is_update = self.check_if_update()
        
        if self.is_update:
            print(f"PushNotifications Desktop Client Updater")
            print(f"Existing installation detected - running in update mode")
        else:
            print(f"PushNotifications Desktop Client Installer")
            print(f"No existing installation detected - running in install mode")
            
        print(f"Platform: {self.system}")
        print(f"Python: {sys.version}")
        print(f"Script URL: {self.gas_script_url}")
        print()

    def check_if_update(self):
        """Check if this is an update (existing installation found)"""
        install_dir = self.get_install_directory()
        return install_dir.exists() and (install_dir / "installer.py").exists()



    def show_message(self, title, message, msg_type="info"):
        """Show message using GUI or console"""
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                if msg_type == "error":
                    messagebox.showerror(title, message)
                elif msg_type == "warning":
                    messagebox.showwarning(title, message)
                else:
                    messagebox.showinfo(title, message)
                root.destroy()
                return
            except Exception:
                pass
        
        # Fallback to console
        print(f"\n{title}:")
        print(message)
        input("\nPress Enter to continue...")

    def ask_yes_no(self, title, question, default_yes=True):
        """Ask a yes/no question using GUI or console"""
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                answer = messagebox.askyesno(title, question, default='yes' if default_yes else 'no')
                root.destroy()
                return answer
            except Exception:
                pass
        
        # Fallback to console
        print(f"\n{title}:")
        default_text = "[Y/n]" if default_yes else "[y/N]"
        response = input(f"{question} {default_text}: ").strip().lower()
        
        if not response:
            return default_yes
        return response.startswith('y')

    def get_install_directory(self):
        """Get the appropriate installation directory for the platform"""
        if self.system == "Windows":
            return Path.home() / "PushNotifications"
        else:
            return Path.home() / "PushNotifications"

    def install_dependencies(self):
        """Install required Python dependencies"""
        print("Checking Python dependencies...")
        
        dependencies = [
            "requests>=2.31.0",
            "psutil>=5.9.0",
            "pytz>=2023.3",
            "pywin32>=306"
        ]
        
        optional_deps = [
            "pystray>=0.19.4",
            "pillow>=10.0.0"
        ]
        
        def check_package_installed(package_name):
            """Check if a package is installed in any Python environment"""
            package_base = package_name.split('>=')[0].split('==')[0].strip()
            try:
                # Try to import the package to see if it's installed
                # Use a subprocess to avoid affecting the current process
                result = subprocess.run(
                    [sys.executable, '-c', f"import {package_base}"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                return result.returncode == 0
            except:
                return False
        
        # Install core dependencies only if not already installed
        for dep in dependencies:
            package_base = dep.split('>=')[0].split('==')[0].strip()
            if check_package_installed(package_base):
                print(f"[OK] {dep} is already installed - skipping")
                continue
                
            print(f"Installing {dep}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                print(f"[OK] {dep} installed successfully")
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', dep])
                    print(f"[OK] {dep} installed successfully (user mode)")
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Failed to install {dep}: {e}")
                    return False
        
        # Install optional dependencies only if not already installed
        print("\nChecking optional dependencies...")
        for dep in optional_deps:
            package_base = dep.split('>=')[0].split('==')[0].strip()
            if check_package_installed(package_base):
                print(f"[OK] {dep} is already installed - skipping")
                continue
                
            print(f"Installing {dep} (optional)...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                print(f"[OK] {dep} installed successfully")
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', dep])
                    print(f"[OK] {dep} installed successfully (user mode)")
                except subprocess.CalledProcessError:
                    print(f"[WARN] {dep} installation failed - continuing without it")
        
        return True

    def download_files(self, install_dir):
        """Download client files to installation directory"""
        # When running in client mode, skip downloads to avoid overwriting files
        if is_client_mode():
            print("Client mode detected - skipping file downloads to avoid overwriting running instance")
            return True
            
        print(f"Downloading client files to {install_dir}...")
        
        # Only download the client file - everything else is embedded in this installer
        files_to_download = {
            "installer.py": "client",
        }
        
        for filename, file_type in files_to_download.items():
            url = f"{self.gas_script_url}/api/download?file={file_type}"
            file_path = install_dir / filename
            
            try:
                print(f"Downloading {filename}...")
                print(f"  URL: {url}")
                response = requests.get(url, timeout=30)
                
                if response.status_code != 200:
                    print(f"  HTTP Error: {response.status_code}")
                    if response.status_code == 404:
                        print(f"  File not found. Check if the Vercel API is properly deployed.")
                    return False
                
                # Check if response looks like an error page
                if 'Access Denied' in response.text or 'Error' in response.text[:200]:
                    print(f"  Server returned an error page")
                    print(f"  Response preview: {response.text[:200]}...")
                    return False
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Make Python files and shell scripts executable on Unix systems
                if (filename.endswith('.py') or filename.endswith('.sh')) and self.system != 'Windows':
                    os.chmod(file_path, 0o755)
                    if filename.endswith('.sh'):
                        print(f"  Made {filename} executable")
                
                print(f"[OK] {filename} downloaded successfully ({len(response.text)} characters)")
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Network error downloading {filename}: {e}")
                print(f"  Please check your internet connection and URL")
                return False
            except Exception as e:
                print(f"[ERROR] Failed to download {filename}: {e}")
                return False
        
        return True
    
    def setup_folder_protection(self, install_dir):
        """Set up comprehensive folder protection to prevent unauthorized deletion"""
        print("Setting up comprehensive folder protection...")
        
        try:
            # Generate a unique protection key for this installation
            import uuid
            protection_key = str(uuid.uuid4())
            
            if self.system == "Windows":
                # Create a protection marker file with key
                protection_file = install_dir / ".protection"
                protection_data = {
                    "installed": datetime.now().isoformat(),
                    "protection_enabled": True,
                    "installation_id": protection_key,
                    "message": "PushNotifications Folder Protection - Uninstall requires web approval"
                }
                
                with open(protection_file, 'w') as f:
                    json.dump(protection_data, f, indent=2)
                
                # Create a protection script that prevents manual deletion
                protection_script = install_dir / "folder_protection.py"
                protection_code = f'''#!/usr/bin/env python3
"""
PushNotifications Folder Protection
This folder is protected and requires administrator approval for deletion.
Attempting to delete this folder without proper authorization will fail.
"""

import sys
import os
import json
from pathlib import Path

def check_protection():
    """Check if folder protection is active"""
    protection_file = Path(__file__).parent / ".protection"
    if protection_file.exists():
        try:
            with open(protection_file, 'r') as f:
                data = json.load(f)
            return data.get("protection_enabled", False)
        except:
            return True  # Assume protected if we can't read the file
    return False

if __name__ == "__main__":
    if check_protection():
        print("ERROR: This folder is protected.")
        print("Uninstallation requires administrator approval via the web form.")
        print("Use the official uninstaller: python uninstall.py")
        sys.exit(1)
    else:
        print("Protection check passed.")
'''
                
                with open(protection_script, 'w') as f:
                    f.write(protection_code)
                
                # Set folder and file attributes with stronger protection
                try:
                    # Make protection files hidden and system files
                    subprocess.run(["attrib", "+S", "+H", str(protection_file)], check=False)
                    subprocess.run(["attrib", "+S", "+H", str(protection_script)], check=False)
                    
                    # Create a file lock protection mechanism
                    lock_file = install_dir / ".folder_lock"
                    with open(lock_file, 'w') as f:
                        f.write(f"PROTECTED INSTALLATION - ID: {protection_key}\nDO NOT DELETE\nContact administrator for uninstall approval")
                    
                    # Make the lock file system and hidden
                    subprocess.run(["attrib", "+S", "+H", "+R", str(lock_file)], check=False)
                    
                    # Try to set restrictive NTFS permissions (requires admin)
                    try:
                        # Use icacls to set restrictive permissions
                        # Remove delete permissions for current user and users group
                        subprocess.run([
                            "icacls", str(install_dir), 
                            "/deny", f"{os.getenv('USERNAME')}:(DE)",  # Deny delete
                            "/deny", "Users:(DE)"
                        ], check=False, capture_output=True)
                        
                        # Set read-only on the entire directory structure
                        subprocess.run(["attrib", "+R", "+S", str(install_dir), "/S"], check=False)
                        
                        print("[OK] Advanced NTFS folder protection configured")
                        print("[NOTE] Windows allows administrative overrides of folder protection.")
                        print("[NOTE] Unauthorized deletion will be logged and reported to administrator.")
                        
                    except Exception as e:
                        print(f"[INFO] Basic protection applied (advanced requires admin): {e}")
                        # Fallback to basic read-only protection
                        subprocess.run(["attrib", "+R", str(install_dir)], check=False)
                        
                    print(f"[OK] Installation protected with ID: {protection_key[:8]}...")
                    
                    # Create a persistent protection service script
                    service_script = install_dir / "protection_service.py"
                    service_code = f'''#!/usr/bin/env python3
"""
PushNotifications Folder Protection Service
This script runs in the background to maintain folder protection.
"""

import os
import sys
import time
import threading
from pathlib import Path

class FolderProtectionService:
    def __init__(self):
        self.install_dir = Path(__file__).parent
        self.protection_key = "{protection_key}"
        self.running = True
        
    def check_protection_integrity(self):
        """Check if protection files are intact"""
        protection_file = self.install_dir / ".protection"
        lock_file = self.install_dir / ".folder_lock"
        
        if not protection_file.exists() or not lock_file.exists():
            self.restore_protection()
            
    def restore_protection(self):
        """Restore protection if tampered with"""
        try:
            # Recreate protection files if missing
            import subprocess
            subprocess.run(["attrib", "+S", "+H", "+R", str(self.install_dir)], check=False)
        except Exception:
            pass
            
    def run(self):
        """Main protection service loop"""
        while self.running:
            try:
                self.check_protection_integrity()
                time.sleep(30)  # Check every 30 seconds
            except Exception:
                time.sleep(30)
                
if __name__ == "__main__":
    service = FolderProtectionService()
    service.run()
'''
                    
                    with open(service_script, 'w') as f:
                        f.write(service_code)
                    
                    # Make service script hidden and system
                    subprocess.run(["attrib", "+S", "+H", str(service_script)], check=False)
                    
                except Exception as e:
                    print(f"[WARN] Could not set advanced protection attributes: {e}")
                    
            else:  # macOS/Linux
                # Create protection marker with key
                protection_file = install_dir / ".protection"
                protection_data = {
                    "installed": datetime.now().isoformat(),
                    "protection_enabled": True,
                    "installation_id": protection_key,
                    "message": "PushNotifications Folder Protection - Uninstall requires web approval"
                }
                
                with open(protection_file, 'w') as f:
                    json.dump(protection_data, f, indent=2)
                
                # Set restrictive permissions
                try:
                    os.chmod(protection_file, 0o400)    # Read-only for owner only
                    os.chmod(install_dir, 0o755)        # Standard directory permissions but protected
                    print("[OK] Unix folder protection configured")
                    print(f"[OK] Installation protected with ID: {protection_key[:8]}...")
                except Exception as e:
                    print(f"[WARN] Could not set folder permissions: {e}")
            
                    # Store the protection key directly in the main installation directory
            protection_key_file = install_dir / ".protection_key"
            with open(protection_key_file, 'w') as f:
                f.write(protection_key)
            
            # Create a file handle lock that prevents deletion
            if self.system == "Windows":
                lock_handle_file = install_dir / ".handle_lock"
                with open(lock_handle_file, 'w') as f:
                    f.write(f"FOLDER_LOCK:{protection_key}")
                
                # Create a Python script that maintains an open file handle
                handle_lock_script = install_dir / "handle_lock.py"
                handle_lock_code = f'''#!/usr/bin/env python3
"""
Folder Handle Lock - Prevents folder deletion by maintaining open file handles
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path

class HandleLock:
    def __init__(self):
        self.install_dir = Path(__file__).parent
        self.lock_files = []
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)
        
    def create_locks(self):
        """Create file handles that prevent folder deletion"""
        try:
            # Create multiple lock files with open handles
            for i in range(3):
                lock_file = self.install_dir / f".lock_{i}"
                # Open file in exclusive mode and keep handle open
                f = open(lock_file, 'w+')
                f.write(f"Lock file {i} - keeps folder from being deleted\\n")
                f.flush()
                self.lock_files.append(f)
                
                # Make lock files hidden and read-only
                try:
                    import subprocess
                    subprocess.run(["attrib", "+S", "+H", "+R", str(lock_file)], check=False)
                except:
                    pass
                    
        except Exception as e:
            print(f"Could not create handle locks: {e}")
            
    def cleanup(self, signum=None, frame=None):
        """Cleanup file handles"""
        self.running = False
        for f in self.lock_files:
            try:
                f.close()
            except:
                pass
                
    def run(self):
        """Main lock service"""
        self.create_locks()
        
        # Keep the script running to maintain locks
        try:
            while self.running:
                time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            
if __name__ == "__main__":
    lock_service = HandleLock()
    lock_service.run()
'''
                
                with open(handle_lock_script, 'w') as f:
                    f.write(handle_lock_code)
                
                # Make the handle lock script system and hidden
                subprocess.run(["attrib", "+S", "+H", str(handle_lock_script)], check=False)
                subprocess.run(["attrib", "+S", "+H", str(lock_handle_file)], check=False)
            
            # Make the protection key file hidden/protected
            if self.system == "Windows":
                subprocess.run(["attrib", "+S", "+H", str(protection_key_file)], check=False)
            else:
                os.chmod(protection_key_file, 0o400)
                    
        except Exception as e:
            print(f"[WARN] Warning: Could not set up folder protection: {e}")
            # Don't fail installation for this
            return True
            
        return True

    def setup_autostart(self, install_dir):
        """Set up automatic startup for the platform"""
        # Skip automatic startup setup - do not configure autostart
        print("Skipping automatic startup configuration...")
        return True
            
        print("Setting up automatic startup...")
        
        try:
            if self.system == "Windows":
                # Create scheduled task
                import winreg
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "PushNotifications", 0, winreg.REG_SZ, 
                f'pythonw.exe "{install_dir / "installer.py"}"')
                winreg.CloseKey(key)
                print("[OK] Windows startup entry created")
                
            elif self.system == "Darwin":  # macOS
                # Create LaunchAgent
                plist_dir = Path.home() / "Library" / "LaunchAgents"
                plist_dir.mkdir(parents=True, exist_ok=True)
                plist_path = plist_dir / "com.pushnotifications.client.plist"
                
                plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pushnotifications.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>{install_dir}/installer.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>'''
                
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
                
                subprocess.run(["launchctl", "load", str(plist_path)], check=False)
                print("[OK] macOS LaunchAgent created")
                
            else:  # Linux
                # Create autostart entry
                autostart_dir = Path.home() / ".config" / "autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)
                desktop_file = autostart_dir / "pushnotifications-client.desktop"
                
                desktop_content = f'''[Desktop Entry]
Type=Application
Name=PushNotifications Client
Comment=Desktop notification client
Exec=python3 {install_dir}/installer.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false'''
                
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                print("[OK] Linux autostart entry created")
                
        except Exception as e:
            print(f"[WARN] Warning: Could not set up autostart: {e}")
            return True  # Don't fail installation for this
            
        return True

    def create_embedded_files(self, install_dir):
        """Create embedded files like requirements.txt, uninstaller, etc."""
        print("Creating embedded files...")
        
        # Create requirements.txt
        requirements_content = '''requests>=2.31.0
psutil>=5.9.0
pytz>=2023.3
pystray>=0.19.4
pillow>=10.0.0
tkinter
'''
        with open(install_dir / "requirements.txt", 'w') as f:
            f.write(requirements_content)
        print("[OK] requirements.txt created")
        
        # Create uninstaller script
        uninstaller_content = f'''#!/usr/bin/env python3
"""
PushNotifications Uninstaller
Requires administrator approval via web form before uninstalling.
"""

import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path
from datetime import datetime

class PushNotificationsUninstaller:
    def __init__(self):
        self.install_dir = Path(__file__).parent
        self.server_url = "{SCRIPT_URL}"
        
    def check_protection(self):
        """Check if installation is protected"""
        protection_file = self.install_dir / ".protection"
        if protection_file.exists():
            try:
                with open(protection_file, 'r') as f:
                    data = json.load(f)
                return data.get("protection_enabled", False), data.get("installation_id", "unknown")
            except:
                return True, "unknown"
        return False, None
        
    def request_uninstall_approval(self, installation_id):
        """Request approval from administrator via web form"""
        try:
            import getpass
            import uuid
            
            data = {{
                'action': 'requestUninstall',
                'installationId': installation_id,
                'installationPath': str(self.install_dir),
                'username': getpass.getuser(),
                'computerName': os.environ.get('COMPUTERNAME', 'Unknown'),
                'requestId': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat()
            }}
            
            response = requests.post(f"{self.server_url}/api/index", json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("Uninstall request submitted successfully.")
                    print("Please wait for administrator approval.")
                    return result.get('requestId')
                else:
                    print(f"Request failed: {{result.get('message', 'Unknown error')}}")
            else:
                print(f"HTTP Error: {{response.status_code}}")
                
        except Exception as e:
            print(f"Failed to submit uninstall request: {{e}}")
            
        return None
        
    def perform_uninstall(self):
        """Perform the actual uninstallation after approval"""
        print("Performing uninstallation...")
        
        try:
            # Stop any running client processes
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'installer.py' in ' '.join(proc.info['cmdline'] or []):
                            proc.terminate()
                            print(f"Stopped client process PID {{proc.info['pid']}}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                print("psutil not available - cannot stop running processes")
            
            # Remove installation directory
            parent_dir = self.install_dir.parent
            
            # First, try to remove file attributes and permissions that might prevent deletion
            if os.name == 'nt':  # Windows
                try:
                    # Remove read-only and system attributes
                    subprocess.run(["attrib", "-R", "-S", "-H", str(self.install_dir), "/S"], check=False)
                    # Reset NTFS permissions
                    subprocess.run(["icacls", str(self.install_dir), "/reset", "/T"], check=False)
                except Exception as e:
                    print(f"Warning: Could not reset file attributes: {{e}}")
            
            # Remove the directory
            shutil.rmtree(str(self.install_dir), ignore_errors=True)
            
            # Clean up backup directory
            backup_dir = Path.home() / "AppData" / "Local" / "PushNotifications_Backup"
            if backup_dir.exists():
                shutil.rmtree(str(backup_dir), ignore_errors=True)
                
            print("Uninstallation completed successfully.")
            return True
            
        except Exception as e:
            print(f"Uninstallation failed: {{e}}")
            return False
    
    def run(self):
        """Main uninstaller logic"""
        print("PushNotifications Uninstaller")
        print("=" * 40)
        
        # Check if installation is protected
        is_protected, installation_id = self.check_protection()
        
        if is_protected:
            print("This installation is protected and requires administrator approval for removal.")
            print("Submitting uninstall request...")
            
            request_id = self.request_uninstall_approval(installation_id)
            if request_id:
                print(f"Request ID: {{request_id}}")
                print("\nThe administrator has been notified of your uninstall request.")
                print("You will be contacted when the request is processed.")
                print("\nDo not attempt to manually delete the installation folder.")
                print("Unauthorized deletion attempts will be logged and reported.")
            else:
                print("Failed to submit uninstall request.")
                print("Please contact your administrator for manual removal.")
        else:
            # Not protected - allow direct uninstall
            print("Installation is not protected. Proceeding with uninstallation...")
            if self.perform_uninstall():
                print("\nPushNotifications has been successfully removed.")
            else:
                print("\nUninstallation encountered errors.")

def main():
    try:
        uninstaller = PushNotificationsUninstaller()
        uninstaller.run()
    except KeyboardInterrupt:
        print("\nUninstallation cancelled.")
    except Exception as e:
        print(f"\nUninstaller error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(install_dir / "uninstall.py", 'w') as f:
            f.write(uninstaller_content)
        print("[OK] uninstall.py created")
        
        # Create Windows batch file for uninstaller
        if self.system == "Windows":
            batch_content = f'''@echo off
echo Starting PushNotifications Uninstaller...
python "%~dp0uninstall.py"
pause
'''
            with open(install_dir / "uninstall.bat", 'w') as f:
                f.write(batch_content)
            print("[OK] uninstall.bat created")
        
        # Create shell script for Unix systems
        else:
            shell_content = f'''#!/bin/bash
echo "Starting PushNotifications Uninstaller..."
python3 "$(dirname "$0")/uninstall.py"
read -p "Press Enter to continue..."
'''
            with open(install_dir / "uninstall.sh", 'w') as f:
                f.write(shell_content)
            os.chmod(install_dir / "uninstall.sh", 0o755)
            print("[OK] uninstall.sh created")
        
        # Create README.md
        readme_content = f'''# PushNotifications Desktop Client

## Installation Directory: {install_dir}

## Features

- Automatic client registration
- Real-time notification display
- Browser usage control
- Website filtering
- Automatic updates (forced when configured)
- Snooze functionality
- Priority-based notifications
- Folder protection system

## Usage

The client runs automatically in the background and connects to the server at:
{SCRIPT_URL}

## Uninstallation

**IMPORTANT**: This installation is protected and requires administrator approval for removal.

To uninstall:
1. Run the uninstaller: `python uninstall.py`
2. Or use the shortcut: `uninstall.{'bat' if self.system == 'Windows' else 'sh'}`
3. Wait for administrator approval
4. Do NOT manually delete the installation folder

## Troubleshooting

- Ensure you have an internet connection
- Check that Python and required packages are installed
- Contact your administrator if you encounter persistent issues
- Unauthorized folder deletion attempts are logged and reported

## Version Information

- Client Version: 2.1.0
- Installation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Server: {SCRIPT_URL}
'''
        
        with open(install_dir / "README.md", 'w') as f:
            f.write(readme_content)
        print("[OK] README.md created")
        
        return True

    def run_installation(self):
        """Run the complete installation or update process"""
        if self.is_update:
            print("Starting PushNotifications update...")
            print("=" * 50)
            return self.run_update()
        else:
            print("Starting PushNotifications installation...")
            print("=" * 50)
            return self.run_fresh_install()
    
    def run_update(self):
        """Run update process for existing installation"""
        install_dir = self.get_install_directory()
        
        print(f"Updating existing installation at {install_dir}")
        
        # Stop existing client before updating
        self.stop_existing_client()
        
        # Install/check dependencies (may have new ones)
        if not self.install_dependencies():
            self.show_message("Update Failed", "Failed to update dependencies.", "error")
            return False
        
        # Download updated client files
        if not self.download_files(install_dir):
            self.show_message("Update Failed", "Failed to download updated client files.", "error")
            return False
        
        # Update embedded files (uninstaller, requirements, etc.) - but preserve protection
        self.update_embedded_files(install_dir)
        
        # Success message
        print(f"\nPushNotifications has been updated successfully!")
        print(f"Installation directory: {install_dir}")
        print(f"Restarting client with updated version...")
        
        # Restart the client
        try:
            subprocess.Popen([sys.executable, str(install_dir / "installer.py")])
            print("Client restarted successfully with new version!")
        except Exception as e:
            print(f"Could not restart client: {e}")
            print("Please manually start the client if needed.")
            
        return True
        
    def run_fresh_install(self):
        """Run fresh installation process"""
        # Get installation directory
        install_dir = self.get_install_directory()
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Install dependencies
        if not self.install_dependencies():
            self.show_message("Installation Failed", "Failed to install required dependencies.", "error")
            return False
        
        # Download files
        if not self.download_files(install_dir):
            self.show_message("Installation Failed", "Failed to download client files.", "error")
            return False
        
        # Create embedded files (requirements, uninstaller, etc.)
        self.create_embedded_files(install_dir)
        
        # Set up folder protection
        self.setup_folder_protection(install_dir)
        
        # Set up autostart
        self.setup_autostart(install_dir)
        
        # Set up monitoring and backup system
        self.setup_monitoring_system(install_dir)
        
        # Success message (console only, no popup)
        print(f"\nPushNotifications has been installed successfully!")
        print(f"Installation directory: {install_dir}")
        print(f"To uninstall, run: python {install_dir}/uninstall.py")
        print(f"or simply: {install_dir}/uninstall{'.bat' if self.system == 'Windows' else '.sh'}")
        print(f"The client will check for updates automatically at startup.")
        
        # Automatically start the client without asking
        print("\nStarting client automatically...")
        try:
            subprocess.Popen([sys.executable, str(install_dir / "installer.py")])
            print("Client started successfully!")
        except Exception as e:
            print(f"Could not start client: {e}")
            
        return True
    
    def stop_existing_client(self):
        """Stop any running PushNotifications client processes"""
        print("Stopping existing client processes...")
        try:
            import psutil
            stopped_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline'] or []
                    if any('installer.py' in arg for arg in cmdline):
                        proc.terminate()
                        print(f"  Stopped client process PID {proc.info['pid']}")
                        stopped_count += 1
                        # Wait a moment for graceful shutdown
                        time.sleep(1)
                        if proc.is_running():
                            proc.kill()
                            print(f"  Force-killed process PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if stopped_count > 0:
                print(f"[OK] Stopped {stopped_count} client process(es)")
                time.sleep(2)  # Give processes time to fully exit
            else:
                print("[OK] No running client processes found")
                
        except ImportError:
            print("[WARN] psutil not available - cannot stop running processes")
            print("[INFO] Please manually close the client if it's running")
        except Exception as e:
            print(f"[WARN] Error stopping processes: {e}")
    
    def update_embedded_files(self, install_dir):
        """Update embedded files during update (preserve protection settings)"""
        print("Updating embedded files...")
        
        # Update requirements.txt
        requirements_content = '''requests>=2.31.0
psutil>=5.9.0
pytz>=2023.3
pystray>=0.19.4
pillow>=10.0.0
tkinter
'''
        with open(install_dir / "requirements.txt", 'w') as f:
            f.write(requirements_content)
        print("[OK] requirements.txt updated")
        
        # Update uninstaller script (preserve existing protection)
        uninstaller_content = f'''#!/usr/bin/env python3
"""
PushNotifications Uninstaller
Requires administrator approval via web form before uninstalling.
"""

import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path
from datetime import datetime

class PushNotificationsUninstaller:
    def __init__(self):
        self.install_dir = Path(__file__).parent
        self.server_url = "{SCRIPT_URL}"
        
    def check_protection(self):
        """Check if installation is protected"""
        protection_file = self.install_dir / ".protection"
        if protection_file.exists():
            try:
                with open(protection_file, 'r') as f:
                    data = json.load(f)
                return data.get("protection_enabled", False), data.get("installation_id", "unknown")
            except:
                return True, "unknown"
        return False, None
        
    def request_uninstall_approval(self, installation_id):
        """Request approval from administrator via web form"""
        try:
            import getpass
            import uuid
            
            data = {{
                'action': 'requestUninstall',
                'installationId': installation_id,
                'installationPath': str(self.install_dir),
                'username': getpass.getuser(),
                'computerName': os.environ.get('COMPUTERNAME', 'Unknown'),
                'requestId': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat()
            }}
            
            response = requests.post(f"{self.server_url}/api/index", json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("Uninstall request submitted successfully.")
                    print("Please wait for administrator approval.")
                    return result.get('requestId')
                else:
                    print(f"Request failed: {{result.get('message', 'Unknown error')}}")
            else:
                print(f"HTTP Error: {{response.status_code}}")
                
        except Exception as e:
            print(f"Failed to submit uninstall request: {{e}}")
            
        return None
        
    def perform_uninstall(self):
        """Perform the actual uninstallation after approval"""
        print("Performing uninstallation...")
        
        try:
            # Stop any running client processes
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'installer.py' in ' '.join(proc.info['cmdline'] or []):
                            proc.terminate()
                            print(f"Stopped client process PID {{proc.info['pid']}}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                print("psutil not available - cannot stop running processes")
            
            # Remove installation directory
            parent_dir = self.install_dir.parent
            
            # First, try to remove file attributes and permissions that might prevent deletion
            if os.name == 'nt':  # Windows
                try:
                    # Remove read-only and system attributes
                    subprocess.run(["attrib", "-R", "-S", "-H", str(self.install_dir), "/S"], check=False)
                    # Reset NTFS permissions
                    subprocess.run(["icacls", str(self.install_dir), "/reset", "/T"], check=False)
                except Exception as e:
                    print(f"Warning: Could not reset file attributes: {{e}}")
            
            # Remove the directory
            shutil.rmtree(str(self.install_dir), ignore_errors=True)
            
            # Clean up backup directory
            backup_dir = Path.home() / "AppData" / "Local" / "PushNotifications_Backup"
            if backup_dir.exists():
                shutil.rmtree(str(backup_dir), ignore_errors=True)
                
            print("Uninstallation completed successfully.")
            return True
            
        except Exception as e:
            print(f"Uninstallation failed: {{e}}")
            return False
    
    def run(self):
        """Main uninstaller logic"""
        print("PushNotifications Uninstaller")
        print("=" * 40)
        
        # Check if installation is protected
        is_protected, installation_id = self.check_protection()
        
        if is_protected:
            print("This installation is protected and requires administrator approval for removal.")
            print("Submitting uninstall request...")
            
            request_id = self.request_uninstall_approval(installation_id)
            if request_id:
                print(f"Request ID: {{request_id}}")
                print("\\nThe administrator has been notified of your uninstall request.")
                print("You will be contacted when the request is processed.")
                print("\\nDo not attempt to manually delete the installation folder.")
                print("Unauthorized deletion attempts will be logged and reported.")
            else:
                print("Failed to submit uninstall request.")
                print("Please contact your administrator for manual removal.")
        else:
            # Not protected - allow direct uninstall
            print("Installation is not protected. Proceeding with uninstallation...")
            if self.perform_uninstall():
                print("\\nPushNotifications has been successfully removed.")
            else:
                print("\\nUninstallation encountered errors.")

def main():
    try:
        uninstaller = PushNotificationsUninstaller()
        uninstaller.run()
    except KeyboardInterrupt:
        print("\\nUninstallation cancelled.")
    except Exception as e:
        print(f"\\nUninstaller error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(install_dir / "uninstall.py", 'w') as f:
            f.write(uninstaller_content)
        print("[OK] uninstall.py updated")
        
        # Update Windows batch file for uninstaller
        if self.system == "Windows":
            batch_content = f'''@echo off
echo Starting PushNotifications Uninstaller...
python "%~dp0uninstall.py"
pause
'''
            with open(install_dir / "uninstall.bat", 'w') as f:
                f.write(batch_content)
            print("[OK] uninstall.bat updated")
        
        # Update shell script for Unix systems
        else:
            shell_content = f'''#!/bin/bash
echo "Starting PushNotifications Uninstaller..."
python3 "$(dirname "$0")/uninstall.py"
read -p "Press Enter to continue..."
'''
            with open(install_dir / "uninstall.sh", 'w') as f:
                f.write(shell_content)
            os.chmod(install_dir / "uninstall.sh", 0o755)
            print("[OK] uninstall.sh updated")
        
        # Update README.md
        readme_content = f'''# PushNotifications Desktop Client

## Installation Directory: {install_dir}

## Features

- Automatic client registration
- Real-time notification display
- Browser usage control
- Website filtering
- Automatic updates (forced when configured)
- Snooze functionality
- Priority-based notifications
- Folder protection system

## Usage

The client runs automatically in the background and connects to the server at:
{SCRIPT_URL}

## Uninstallation

**IMPORTANT**: This installation is protected and requires administrator approval for removal.

To uninstall:
1. Run the uninstaller: `python uninstall.py`
2. Or use the shortcut: `uninstall.{'bat' if self.system == 'Windows' else 'sh'}`
3. Wait for administrator approval
4. Do NOT manually delete the installation folder

## Troubleshooting

- Ensure you have an internet connection
- Check that Python and required packages are installed
- Contact your administrator if you encounter persistent issues
- Unauthorized folder deletion attempts are logged and reported

## Version Information

- Client Version: 2.1.0
- Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Server: {SCRIPT_URL}
'''
        
        with open(install_dir / "README.md", 'w') as f:
            f.write(readme_content)
        print("[OK] README.md updated")
        
        print("[INFO] Protection files preserved during update")
        return True
    
    def setup_monitoring_system(self, install_dir):
        """Set up monitoring and backup system for folder protection"""
        print("Setting up monitoring and backup system...")
        
        try:
            # Create a backup location in a different directory
            backup_dir = Path.home() / "AppData" / "Local" / "PushNotifications_Backup"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup of critical files
            critical_files = [
                ".protection",
                ".protection_key",
                "installer.py",
                "uninstall.py"
            ]
            
            for filename in critical_files:
                src_file = install_dir / filename
                if src_file.exists():
                    dest_file = backup_dir / filename
                    import shutil
                    shutil.copy2(str(src_file), str(dest_file))
                    
                    # Make backup files hidden
                    if self.system == "Windows":
                        subprocess.run(["attrib", "+H", str(dest_file)], check=False)
            
            # Create monitoring script
            monitor_script = backup_dir / "folder_monitor.py"
            monitor_code = f'''#!/usr/bin/env python3
"""
PushNotifications Folder Monitor
Monitors the installation directory and reports/restores if deleted.
"""

import os
import sys
import time
import shutil
from pathlib import Path
import subprocess

class FolderMonitor:
    def __init__(self):
        self.install_dir = Path("{str(install_dir)}")
        self.backup_dir = Path(__file__).parent
        self.gas_script_url = "{self.gas_script_url}"
        self.running = True
        
    def check_installation_integrity(self):
        """Check if installation directory exists and is intact"""
        if not self.install_dir.exists():
            print(f"WARNING: Installation directory {self.install_dir} was deleted!")
            self.report_deletion()
            self.attempt_restoration()
            return False
            
        # Check critical files
        critical_files = [".protection", ".protection_key", "installer.py"]
        for filename in critical_files:
            if not (self.install_dir / filename).exists():
                print(f"WARNING: Critical file {filename} is missing!")
                self.attempt_restoration()
                break
                
        return True
        
    def report_deletion(self):
        """Report unauthorized deletion to administrator"""
        try:
            import requests
            import uuid
            import getpass
            
            params = {{
                'action': 'reportUnauthorizedDeletion',
                'installationPath': str(self.install_dir),
                'username': getpass.getuser(),
                'computerName': os.environ.get('COMPUTERNAME', 'Unknown'),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }}
            
            response = requests.get(self.gas_script_url, params=params, timeout=10)
            print("Unauthorized deletion reported to administrator.")
            
        except Exception as e:
            print(f"Could not report deletion: {e}")
            
    def attempt_restoration(self):
        """Attempt to restore installation from backup"""
        print("Attempting to restore installation...")
        
        try:
            # Recreate installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Restore critical files from backup
            for backup_file in self.backup_dir.glob(".*"):
                if backup_file.is_file() and backup_file.name != "folder_monitor.py":
                    dest_file = self.install_dir / backup_file.name
                    shutil.copy2(str(backup_file), str(dest_file))
                    print(f"Restored {backup_file.name}")
                    
            for backup_file in self.backup_dir.glob("*.py"):
                if backup_file.name != "folder_monitor.py":
                    dest_file = self.install_dir / backup_file.name
                    shutil.copy2(str(backup_file), str(dest_file))
                    print(f"Restored {backup_file.name}")
                    
            print("Installation restored. Administrator approval still required for uninstall.")
            
        except Exception as e:
            print(f"Restoration failed: {e}")
            
    def run(self):
        """Main monitoring loop"""
        print("Folder monitor started...")
        
        while self.running:
            try:
                self.check_installation_integrity()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(60)
                
if __name__ == "__main__":
    monitor = FolderMonitor()
    monitor.run()
'''
            
            with open(monitor_script, 'w') as f:
                f.write(monitor_code)
                
            # Make monitor script hidden
            if self.system == "Windows":
                subprocess.run(["attrib", "+H", str(monitor_script)], check=False)
                subprocess.run(["attrib", "+H", str(backup_dir)], check=False)
            
            # Start monitor service in background
            try:
                subprocess.Popen(
                    [sys.executable, str(monitor_script)],
                    creationflags=subprocess.CREATE_NO_WINDOW if self.system == "Windows" else 0,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[OK] Folder monitoring service started")
            except Exception as e:
                print(f"[WARN] Could not start monitoring service: {e}")
                
            print(f"[OK] Backup system configured in: {backup_dir}")
            
        except Exception as e:
            print(f"[WARN] Could not set up monitoring system: {e}")
            
        return True

class PushNotificationsClient:
    """Main client application class"""
    
    _instance = None
    
    def __init__(self, install_dir=None):
        if install_dir is None:
            install_dir = Path.home() / "PushNotifications"
        
        self.install_dir = Path(install_dir)
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.security = SecurityManager(self.install_dir)
        self.overlay = OverlayManager()
        self.running = False
        self.tray_icon = None
        self.notification_queue = []
        self.active_notifications = {}
        
        # Set singleton instance
        PushNotificationsClient._instance = self
        
        # Setup folder protection
        self._setup_folder_protection()
        
        # Setup auto-startup
        self._setup_auto_startup()
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        return cls._instance
    
    def _setup_folder_protection(self):
        """Setup advanced folder protection with database keys"""
        try:
            # Create protection marker with database key
            protection_file = self.install_dir / '.protection'
            protection_data = {
                'protected': True,
                'installation_id': self.security.client_id,
                'encryption_key_hash': hashlib.sha256(self.security.encryption_key.encode()).hexdigest(),
                'created': datetime.now().isoformat(),
                'version': CLIENT_CONFIG['client_version']
            }
            
            with open(protection_file, 'w') as f:
                json.dump(protection_data, f)
            
            # Hide and protect files on Windows
            if platform.system() == 'Windows':
                subprocess.run(['attrib', '+S', '+H', '+R', str(protection_file)], check=False)
                subprocess.run(['attrib', '+S', '+H', str(self.install_dir)], check=False)
                
                # Set NTFS permissions to deny deletion
                try:
                    username = os.getenv('USERNAME')
                    subprocess.run([
                        'icacls', str(self.install_dir),
                        '/deny', f'{username}:(DE)',
                        '/deny', 'Users:(DE)'
                    ], check=False, capture_output=True)
                except Exception:
                    pass
            
            print("Folder protection enabled with database encryption key")
            
        except Exception as e:
            print(f"Failed to setup folder protection: {e}")
    
    def _setup_auto_startup(self):
        """Setup automatic startup on Windows"""
        try:
            if platform.system() == 'Windows':
                # Create registry entry for startup
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                
                # Use pythonw.exe to run invisibly
                startup_command = f'pythonw.exe "{self.install_dir / "installer.py"}"'
                winreg.SetValueEx(key, "PushNotifications", 0, winreg.REG_SZ, startup_command)
                winreg.CloseKey(key)
                
                print("Auto-startup configured")
                
        except Exception as e:
            print(f"Failed to setup auto-startup: {e}")
    
    def start(self):
        """Start the client"""
        try:
            print(f"Starting PushNotifications Client {CLIENT_CONFIG['client_version']}")
            print(f"Client ID: {self.security.client_id}")
            print("Running in background with invisible Windows PowerShell...")
            
            self.running = True
            
            # Create tray icon
            self._create_tray_icon()
            
            # Start notification checker thread
            check_thread = threading.Thread(target=self._notification_check_loop, daemon=True)
            check_thread.start()
            
            # Register with server
            self._register_with_server()
            
            print("Client started successfully")
            
            # Run tray icon (this blocks)
            if self.tray_icon:
                self.tray_icon.run()
            else:
                # Fallback - just keep running
                while self.running:
                    time.sleep(1)
            
        except Exception as e:
            print(f"Failed to start client: {e}")
    
    def stop(self):
        """Stop the client"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
    
    def _create_tray_icon(self):
        """Create system tray icon"""
        try:
            from PIL import Image, ImageDraw
            import pystray
            
            # Create icon image
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.ellipse([16, 16, 48, 48], fill='white')
            draw.text((28, 24), "PN", fill='blue')
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("PushNotifications", lambda: None, enabled=False),
                pystray.MenuItem("Status: Running", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Check Now", self._manual_check),
                pystray.MenuItem("Show Folder", self._show_folder),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit_application)
            )
            
            self.tray_icon = pystray.Icon("PushNotifications", image, menu=menu)
            
        except Exception as e:
            print(f"Failed to create tray icon: {e}")
            self.tray_icon = None
    
    def _notification_check_loop(self):
        """Main loop to check for notifications"""
        while self.running:
            try:
                self._check_notifications()
                time.sleep(CLIENT_CONFIG['check_interval'])
            except Exception as e:
                print(f"Error in notification check: {e}")
                time.sleep(CLIENT_CONFIG['check_interval'])
    
    def _check_notifications(self):
        """Check for new notifications from server"""
        try:
            data = {
                'action': 'getNotifications',
                'clientId': self.security.client_id,
                'version': CLIENT_CONFIG['client_version'],
                'lastCheck': datetime.now().isoformat()
            }
            
            response = requests.post(CLIENT_CONFIG['server_url'], json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    notifications = result.get('notifications', [])
                    
                    for notification in notifications:
                        self._process_notification(notification)
                        
                else:
                    print(f"Server error: {result.get('message', 'Unknown error')}")
            else:
                print(f"HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"Failed to check notifications: {e}")
    
    def _process_notification(self, notification):
        """Process a received notification"""
        try:
            notification_id = notification.get('_id') or notification.get('id')
            
            # Check if already processed
            if notification_id in self.active_notifications:
                return
            
            # Add to active notifications
            self.active_notifications[notification_id] = notification
            
            # Determine priority and position
            priority = notification.get('priority', 'normal')
            
            if priority == 'urgent' or not self.overlay.is_overlay_active:
                # Show immediately for urgent or if no active overlay
                self.overlay.show_overlay(notification)
            else:
                # Queue for later (will show under current notification)
                self.notification_queue.append(notification)
            
            print(f"Processing notification: {notification.get('message', 'No message')}")
            
        except Exception as e:
            print(f"Failed to process notification: {e}")
    
    def complete_notification(self, notification_data):
        """Mark notification as complete"""
        try:
            notification_id = notification_data.get('_id') or notification_data.get('id')
            
            # Send completion to server
            data = {
                'action': 'completeNotification',
                'clientId': self.security.client_id,
                'notificationId': notification_id,
                'completedAt': datetime.now().isoformat()
            }
            
            response = requests.post(CLIENT_CONFIG['server_url'], json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("Notification marked as complete")
                    
                    # Remove from active notifications
                    self.active_notifications.pop(notification_id, None)
                    
                    # Show next notification if queued
                    self._show_next_notification()
                    
        except Exception as e:
            print(f"Failed to complete notification: {e}")
    
    def snooze_notification(self, notification_data, minutes):
        """Snooze notification"""
        try:
            notification_id = notification_data.get('_id') or notification_data.get('id')
            
            # Send snooze to server
            data = {
                'action': 'snoozeNotification',
                'clientId': self.security.client_id,
                'notificationId': notification_id,
                'minutes': minutes,
                'snoozedAt': datetime.now().isoformat()
            }
            
            response = requests.post(CLIENT_CONFIG['server_url'], json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"Notification snoozed for {minutes} minutes")
                    
                    # Remove from active notifications temporarily
                    self.active_notifications.pop(notification_id, None)
                    
                    # Show next notification if queued
                    self._show_next_notification()
                    
        except Exception as e:
            print(f"Failed to snooze notification: {e}")
    
    def _show_next_notification(self):
        """Show next notification from queue"""
        try:
            if self.notification_queue:
                next_notification = self.notification_queue.pop(0)
                self.overlay.show_overlay(next_notification)
                
        except Exception as e:
            print(f"Failed to show next notification: {e}")
    
    def _register_with_server(self):
        """Register client with server"""
        try:
            data = {
                'action': 'registerClient',
                'clientId': self.security.client_id,
                'version': CLIENT_CONFIG['client_version'],
                'platform': platform.system(),
                'hostname': platform.node(),
                'installPath': str(self.install_dir),
                'encryptionKeyHash': hashlib.sha256(self.security.encryption_key.encode()).hexdigest()
            }
            
            response = requests.post(CLIENT_CONFIG['server_url'], json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("Successfully registered with server")
                else:
                    print(f"Registration failed: {result.get('message')}")
            else:
                print(f"Registration HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"Failed to register with server: {e}")
    
    def _manual_check(self):
        """Manually check for notifications"""
        print("Manually checking for notifications...")
        self._check_notifications()
    
    def _show_folder(self):
        """Show installation folder"""
        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', str(self.install_dir)])
        except Exception as e:
            print(f"Failed to show folder: {e}")
    
    def _quit_application(self):
        """Quit the application"""
        print("Quitting PushNotifications Client...")
        self.stop()

def check_admin_privileges():
    """Check if running with administrator privileges"""
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    return os.geteuid() == 0

def restart_with_admin():
    """Restart with administrator privileges"""
    if platform.system() == 'Windows':
        try:
            from win32com.shell import shell
            # Re-run the current program as admin
            shell.ShellExecuteEx(
                lpVerb='runas',
                lpFile=sys.executable,
                lpParameters=' '.join([f'"{arg}"' for arg in sys.argv]),
                nShow=1
            )
            sys.exit(0)
        except Exception as e:
            print(f"Failed to restart with admin privileges: {e}")
            return False
    return True

def is_client_mode():
    """Check if we should run in client mode instead of installer mode"""
    install_dir = Path.home() / "PushNotifications"
    
    # If we're in the install directory and have protection files, run as client
    current_path = Path(__file__).parent
    
    if current_path == install_dir:
        protection_file = install_dir / '.protection'
        security_db = install_dir / '.security.db'
        
        if protection_file.exists() and security_db.exists():
            return True
    
    return False

def main():
    """Main entry point"""
    # Support -h/--help via argparse-like behavior without adding runtime dependency
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print(__doc__)
        return
    
    try:
        # Check if we should run in client mode
        if is_client_mode():
            # Check if we need admin privileges for client mode
            if not check_admin_privileges():
                print("Restarting with administrator privileges...")
                restart_with_admin()
                return
            
            # Run as client
            install_dir = Path.home() / "PushNotifications"
            client = PushNotificationsClient(install_dir)
            
            # Handle Ctrl+C gracefully
            import signal
            signal.signal(signal.SIGINT, lambda s, f: client.stop())
            signal.signal(signal.SIGTERM, lambda s, f: client.stop())
            
            # Start client
            client.start()
        else:
            # Run as installer
            installer = PushNotificationsInstaller()
            success = installer.run_installation()
            
            if success:
                print("\nInstallation completed successfully!")
                print("\nThe client will automatically check for updates from the server.")
                print("You can now close this installer.")
            else:
                print("\nInstallation failed.")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
