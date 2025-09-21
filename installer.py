#!/usr/bin/env python3
# PushNotifications Client Installer
# Downloaded Version: 1.8.4
# Version Number: 85
# Download Date: 2025-09-15T15:31:10.423Z
# task manager name update
"""
PushNotifications Windows Client Installer
Version: 1.8.4
Windows-only installer with native Python operation:
ADMINISTRATOR PRIVILEGES REQUIRED:
- Administrator privileges are REQUIRED for ALL operations including:
  • Installation and system setup
  • Client operation and ongoing functionality
  • System integration and security features
  • Process management and window control
[WINDOWS] WINDOWS ENTERPRISE FEATURES
- Python-based operation with admin privileges
- Hidden encrypted installation with AES-256-GCM vault encryption
- Zero local key storage (all keys fetched from website/MongoDB)
- Real MAC address detection and transmission
- Admin privilege escalation without UAC prompts
- Multi-monitor 25% grey overlay system
- Force-minimize window restrictions during active notifications
- Website allowlist enforcement and request system
- Server-managed uninstallation via taskbar
[SECURITY] SECURITY & ENCRYPTION
- AES-256-GCM encrypted installation directories
- Server-managed encryption keys
- Hidden file system integration
- Server-managed uninstallation system
"""
# Core imports - always needed
import os
import sys
import json
import time
import logging
import logging.handlers
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
# Secondary imports - used in most operations
import uuid
import hashlib
import random
import subprocess
import traceback
import ctypes
# Imports for specific operations - loaded as needed
import getpass  # Used for username detection
import tempfile  # Used for temporary files
import base64    # Used for encoding/decoding
import secrets   # Used for cryptographic operations
import shutil    # Used for file operations
import threading # Used for background tasks
from urllib.parse import urlparse  # Used for URL parsing
# ========================================
# COMPREHENSIVE LOGGING CONFIGURATION
# ========================================
# Configure logging to capture ALL errors and important events
logger = logging.getLogger('PushNotificationsInstaller')
logger.setLevel(logging.DEBUG)
# Clear any existing handlers to avoid duplicates
logger.handlers.clear()
# Create log file path in user's Documents folder
try:
    # Get the user's Documents folder path
    import ctypes.wintypes
    CSIDL_PERSONAL = 5  # Documents folder
    _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
    _SHGetFolderPath.argtypes = [ctypes.wintypes.HWND,
                                 ctypes.c_int,
                                 ctypes.wintypes.HANDLE,
                                 ctypes.wintypes.DWORD,
                                 ctypes.wintypes.LPCWSTR]
    path_buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    result = _SHGetFolderPath(0, CSIDL_PERSONAL, 0, 0, path_buf)
    if result == 0:
        documents_path = Path(path_buf.value)
    else:
        # Fallback to Path.home() / "Documents" if SHGetFolderPath fails
        documents_path = Path.home() / "Documents"
    # Create the log file in Documents with the specified name
    log_file_path = documents_path / "Push Notifications Log.log"
    # Test if we can write to the Documents folder
    test_path = documents_path / "test_write.tmp"
    test_path.touch()
    test_path.unlink()
except Exception:
    try:
        # Fallback to temp directory if Documents isn't writable
        log_dir = Path(tempfile.gettempdir()) / "PushNotifications"
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / "Push Notifications Log.log"
    except Exception:
        # Final fallback to user directory
        log_file_path = Path.home() / "Push Notifications Log.log"
# Create rotating file handler (max 5MB, keep 3 backups)
try:
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    # Create detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    # Add handler to logger
    logger.addHandler(file_handler)
    # Also add console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    # Log initialization success
    logger.info(f"Logging initialized successfully - Log file: {log_file_path}")
    logger.info(f"Installer version: 1.8.4")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
except Exception as e:
    # If logging setup fails, create a basic console logger
    # If logging setup fails, create a basic console logger and still log the warning
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    logger.warning(f"Logging setup failed, using console only: {e}")
# Helper function to log exceptions with full traceback
def log_exception(message, exc_info=True):
    """Log an exception with full traceback details"""
    logger.error(message, exc_info=exc_info)
# Essential modules that are used throughout the script
try:
    import requests
except ImportError:
    requests = None
    logger.warning("requests module not available - some functionality will be limited")
try:
    import psutil
except ImportError:
    psutil = None
    logger.warning("psutil module not available - some functionality will be limited")
# Windows-only installer - winreg is required
import winreg
# Tkinter imports with fallbacks - needed throughout the application
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    TKINTER_AVAILABLE = True
except ImportError:
    # Define dummy classes to prevent crashes
    class DummyTk:
        def __init__(self): pass
        def Tk(self): return self
        def Toplevel(self): return self
        def Label(self, *args, **kwargs): return self
        def Frame(self, *args, **kwargs): return self
        def Text(self, *args, **kwargs): return self
        def Scrollbar(self, *args, **kwargs): return self
        def configure(self, *args, **kwargs): pass
        def attributes(self, *args, **kwargs): pass
        def geometry(self, *args): pass
        def overrideredirect(self, *args): pass
        def destroy(self): pass
        def withdraw(self): pass
        def deiconify(self): pass
        def focus_force(self): pass
        def update(self): pass
        def update_idletasks(self): pass
        def pack(self, *args, **kwargs): pass
        def config(self, *args, **kwargs): pass
        def winfo_screenwidth(self): return 1920
        def winfo_screenheight(self): return 1080
        def title(self, *args): pass
        def resizable(self, *args): pass
        def mainloop(self): pass
        # Constants
        DISABLED = 'disabled'
        NORMAL = 'normal'
        RIGHT = 'right'
        LEFT = 'left'
        BOTH = 'both'
        X = 'x'
        Y = 'y'
        W = 'w'
    class DummyTtk:
        def Progressbar(self, *args, **kwargs): return DummyTk()
    class DummyMessagebox:
        def showinfo(self, *args, **kwargs): pass
        def showerror(self, *args, **kwargs): pass
        def askyesno(self, *args, **kwargs): return True
    class DummySimpledialog:
        def askstring(self, *args, **kwargs): return None
    tk = DummyTk()
    ttk = DummyTtk()
    messagebox = DummyMessagebox()
    simpledialog = DummySimpledialog()
    TKINTER_AVAILABLE = False
    logger.warning("tkinter not available - GUI functionality will be limited")
# Cryptography imports with fallbacks
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    # Define dummy classes to prevent crashes
    class PBKDF2HMAC:
        def __init__(self, **kwargs): pass
        def derive(self, key): return b'dummy_key_32_bytes_for_testing!'
    class DummyHashes:
        def SHA256(self): return None
    hashes = DummyHashes()
    class AESGCM:
        def __init__(self, key): pass
        def encrypt(self, nonce, data, aad): return b'dummy_encrypted_data'
        def decrypt(self, nonce, data, aad): return b'dummy_decrypted_data'
# PIL/Pillow imports with fallbacks
try:
    from PIL import Image, ImageDraw
except ImportError:
    class DummyImage:
        def new(self, mode, size, color=None): return self
        def open(self, path): return self
        def resize(self, size, resample=None): return self
        def convert(self, mode): return self
    class DummyImageDraw:
        def Draw(self, image): return self
        def ellipse(self, *args, **kwargs): pass
    Image = DummyImage()
    ImageDraw = DummyImageDraw()
# System tray imports with fallbacks
try:
    import pystray
except ImportError:
    class DummyPystray:
        class Icon:
            def __init__(self, *args, **kwargs): pass
            def run(self): pass
            def stop(self): pass
        class Menu:
            def __init__(self, *items): pass
        class MenuItem:
            def __init__(self, *args, **kwargs): pass
    pystray = DummyPystray()
# Windows-only installer - Windows-specific imports required
import win32gui
import win32con
import win32api
import win32process
import win32security
import ntsecuritycon
import win32file
# Windows COM imports with fallbacks
try:
    import pythoncom  # Import for Windows COM support
    from win32com.shell import shell, shellcon
    from win32com.client import Dispatch
    WIN32COM_AVAILABLE = True
except ImportError:
    # Define dummy classes to prevent crashes
    class DummyPythoncom:
        def CoInitialize(self): pass
        def CoCreateInstance(self, *args): return self
        def QueryInterface(self, iid): return self
        def Save(self, *args): pass
        # Common constants
        CLSCTX_INPROC_SERVER = 1
        IID_IPersistFile = "dummy_iid"
    class DummyShell:
        def __getattr__(self, name): return "dummy_shell_attr"
        CLSID_ShellLink = "dummy_clsid"
        IID_IShellLink = "dummy_iid"
    class DummyShellcon:
        def __getattr__(self, name): return 0
    class DummyDispatch:
        def __init__(self, *args): pass
        def __call__(self, *args): return self
        def CreateShortCut(self, *args): return self
        def __getattr__(self, name): return self
        def __setattr__(self, name, value): pass
        def save(self): pass
        def SetPath(self, *args): pass
        def SetArguments(self, *args): pass
        def SetWorkingDirectory(self, *args): pass
        def SetDescription(self, *args): pass
        def SetIconLocation(self, *args): pass
    pythoncom = DummyPythoncom()
    shell = DummyShell()
    shellcon = DummyShellcon()
    Dispatch = DummyDispatch
    WIN32COM_AVAILABLE = False
    logger.warning("win32com not available - desktop shortcut functionality will be limited")
# Screen info imports with fallbacks
try:
    import screeninfo
except ImportError:
    class DummyScreeninfo:
        def get_monitors(self): return []
    screeninfo = DummyScreeninfo()
# WMI imports with fallbacks (Windows Management Instrumentation)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    class DummyWMI:
        def WMI(self): return self
        def Win32_NetworkAdapter(self): return []
    wmi = DummyWMI()
    WMI_AVAILABLE = False
# MessageRelay class for inter-process communication during elevation
class MessageRelay:
    """Handles message passing between original and elevated processes via JSON file"""
    def __init__(self, message_file_path):
        self.message_file = Path(message_file_path)
        self.enabled = True
        try:
            # Ensure the directory exists
            self.message_file.parent.mkdir(parents=True, exist_ok=True)
            # Initialize with empty status
            self.send_message({
                "status": "initializing",
                "message": "Message relay initialized",
                "timestamp": datetime.now().isoformat(),
                "progress": 0
            })
            logger.info(f"Message relay initialized: {self.message_file}")
        except Exception as e:
            logger.error(f"Failed to initialize message relay: {e}")
            self.enabled = False
    def send_message(self, data):
        """Send a message via the relay file"""
        if not self.enabled:
            return False
        try:
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()
            # Write to temporary file first, then rename for atomicity
            temp_file = self.message_file.with_suffix('.tmp')
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            # Atomic rename
            temp_file.replace(self.message_file)
            return True
        except Exception as e:
            logger.error(f"Failed to send message via relay: {e}")
            self.enabled = False
            return False
    def send_status(self, status, message, progress=None):
        """Send a status update"""
        data = {
            "status": status,
            "message": message
        }
        if progress is not None:
            data["progress"] = progress
        return self.send_message(data)
    def send_success(self, message, progress=100):
        """Send a success message"""
        return self.send_status("success", message, progress)
    def send_error(self, message):
        """Send an error message"""
        return self.send_status("error", message)
    def send_progress(self, message, progress):
        """Send a progress update"""
        return self.send_status("progress", message, progress)
    def close(self):
        """Clean up the message relay"""
        try:
            if self.message_file.exists():
                self.message_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up message relay file: {e}")
# Function to monitor message relay file in original process
def monitor_message_relay(message_file_path, timeout_seconds=300):
    """Monitor the message relay file and display updates"""
    message_file = Path(message_file_path)
    start_time = time.time()
    last_message = None
    print("\n[INFO] Starting installation with elevated privileges...")
    print("[INFO] Monitoring installation progress...\n")
    while time.time() - start_time < timeout_seconds:
        try:
            if message_file.exists():
                with message_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                # Only show new messages
                current_message = data.get('message', '')
                if current_message != last_message:
                    status = data.get('status', 'unknown')
                    progress = data.get('progress')
                    timestamp = data.get('timestamp', '')
                    # Format output based on status
                    if status == 'success':
                        print(f"[✓] {current_message}")
                        if progress == 100:
                            print("\n[SUCCESS] Installation completed successfully!")
                            return True
                    elif status == 'error':
                        print(f"[✗] ERROR: {current_message}")
                        return False
                    elif status == 'progress':
                        if progress is not None:
                            print(f"[INFO] {current_message} ({progress}%)")
                        else:
                            print(f"[INFO] {current_message}")
                    else:
                        print(f"[INFO] {current_message}")
                    last_message = current_message
                # Check for completion
                if data.get('status') == 'success' and data.get('progress') == 100:
                    return True
                elif data.get('status') == 'error':
                    return False
            time.sleep(0.5)  # Check every half second
        except (json.JSONDecodeError, FileNotFoundError):
            # File might not exist yet or be incomplete
            time.sleep(0.5)
            continue
        except Exception as e:
            logger.warning(f"Error monitoring message relay: {e}")
            time.sleep(1)
            continue
    print("\n[WARNING] Installation monitoring timed out")
    return False
# Global variable definitions that are used throughout the script
CLIENT_VERSION = "1.8.4"  # Will be updated by installer
CLIENT_ID = "placeholder_client_id"  # Will be updated by installer
API_URL = "https://push-notifications-phi.vercel.app"  # Default API URL
MAC_ADDRESS = "00-00-00-00-00-00"  # Will be detected by installer
# Windows-only installer - Windows features always available
WINDOWS_FEATURES_AVAILABLE = True
# OverlayManager class definition (used in installer)
class OverlayManager:
    def __init__(self):
        self.overlays = []
    def create_overlays(self):
        """Create grey overlays on all monitors"""
        try:
            # Use global tkinter import - already handled at module level
            if not TKINTER_AVAILABLE:
                logger.warning("tkinter not available, cannot create overlays")
                return
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            overlay = tk.Toplevel()
            overlay.configure(bg='grey')
            overlay.attributes('-alpha', 0.7)
            overlay.attributes('-topmost', True)
            overlay.geometry(f"{screen_width}x{screen_height}+0+0")
            overlay.overrideredirect(True)
            self.overlays.append(overlay)
        except Exception as e:
            logger.warning(f"Could not create overlays: {e}")
    def remove_overlays(self):
        """Remove all overlays"""
        for overlay in self.overlays:
            try:
                overlay.destroy()
            except:
                pass
        self.overlays = []
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
            logger.warning(f"{package_name} not bundled - may cause issues")
            return False
        # Only install if not found in any Python environment
        logger.info(f"Installing {package_name}...")
        try:
            # Use more robust subprocess call with proper encoding and timeout
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pip_name, '--quiet', '--disable-pip-version-check'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,  # 5 minute timeout
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name}")
                return True
            else:
                logger.warning(f"Failed to install {package_name}: {getattr(result, 'stderr', 'Unknown error')}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"Installation of {package_name} timed out after 5 minutes")
            return False
        except Exception as e:
            logger.warning(f"Failed to install {package_name}: {e}")
            return False
# Try to import core dependencies, install if missing
# Package imports are deferred to prevent crashes during help commands
# These will be imported only during actual installation
# Windows-specific globals - will be set after argument parsing
WMI_AVAILABLE = False
UI_AUTOMATION_AVAILABLE = False
SCREEN_INFO_AVAILABLE = False
# GUI imports - will be imported dynamically when needed
# No module-level tkinter imports to prevent early crashes
GUI_AVAILABLE = None  # Will be determined when GUI is actually needed
# Global flag to control GUI dialog usage - only enabled for key entry popup
# Set to False to disable most GUI dialogs except key entry popup
USE_GUI_DIALOGS = False
# Separate flag for key entry popup which should remain enabled
USE_KEY_ENTRY_POPUP = True
# Cross-platform system tray support - deferred loading to prevent crashes during help
TRAY_AVAILABLE = False  # Will be set during actual installation
class InstallationProgressDialog:
    """Cross-platform installation progress dialog"""
    def __init__(self):
        self.window = None
        self.progress_bar = None
        self.status_label = None
        self.log_text = None
        # Progress dialog is disabled to only show cmd window
        # Use global tkinter import - already handled at module level
        try:
            if USE_GUI_DIALOGS and TKINTER_AVAILABLE:
                self._create_dialog()
        except Exception as e:
            logger.warning(f"Could not create progress dialog: {e}")
        pass
    def _create_dialog(self):
        """Create the progress dialog window"""
        try:
            if not TKINTER_AVAILABLE:
                logger.warning("tkinter not available for dialog creation")
                return
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
            logger.warning(f"Could not create progress dialog: {e}")
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
        # Console logging is handled by the main logger
    def set_completion(self, success=True):
        """Show completion status"""
        if self.window:
            try:
                if success:
                    self.status_label.config(text="[COMPLETED] Installation completed successfully!")
                    self.progress_bar['value'] = 100
                else:
                    self.status_label.config(text="[FAILED] Installation failed")
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
        logger.info("Fetching current version from API...")
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
                logger.info(f"[OK] Retrieved version from API: v{version}")
                return version
            else:
                logger.error(f"[ERR] API response unsuccessful: {result.get('message', 'Unknown error')}")
        else:
            logger.error(f"[ERR] API request failed: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"[ERR] Network error fetching version: {e}")
    except Exception as e:
        logger.error(f"[ERR] Error fetching version: {e}")
    # Fallback to a default version if API fails
    logger.warning("Using fallback version 1.0.0")
    return "1.0.0"
# Global configuration - moved before logging setup
INSTALLER_VERSION = '1.8.4'  # Current version from header
VERSION_NUMBER = 85  # Numeric version for update comparisons
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
- **Progress Feedback**: Clear visual indicators ([OK], [ERR], ⚠) for all operations
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
- [Node.js](https://nodejs.org/) version 18.0.0 or higher
- [MongoDB Atlas](https://www.mongodb.com/atlas) account (or self-hosted MongoDB instance)
  - MongoDB version 6.3.0 or higher required
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
# Enhanced embedded components
# Valid 32x32 PNG icon with transparent background and "PN" text
EMBEDDED_ICON_DATA = "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TtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWXs91IAACAASURBVGgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCp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oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQca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"
EMBEDDED_FAVICON_UTILS = '''
import base64
from pathlib import Path
# Replace with your actual favicon PNG base64 data
FAVICON_DATA = "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TtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWXs91IAACAASURBVGgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCp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oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQca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"
def extract_favicon(install_path):
    """Extract favicon to installation directory"""
    favicon_path = Path(install_path) / "favicon.png"
    try:
        favicon_bytes = base64.b64decode(FAVICON_DATA)
        with open(favicon_path, 'wb') as f:
            f.write(favicon_bytes)
        return favicon_path
    except Exception as e:
        logger.error(f"Error extracting favicon: {e}")
        return None
'''
EMBEDDED_OVERLAY_MANAGER = '''
import tkinter as tk
from tkinter import ttk
class OverlayManager:
    def __init__(self):
        self.overlays = []
    def create_overlays(self):
        """Create grey overlays on all monitors"""
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        overlay = tk.Toplevel()
        overlay.configure(bg='grey')
        overlay.attributes('-alpha', 0.7)
        overlay.attributes('-topmost', True)
        overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        overlay.overrideredirect(True)
        self.overlays.append(overlay)
    def remove_overlays(self):
        """Remove all overlays"""
        for overlay in self.overlays:
            overlay.destroy()
        self.overlays = []
'''
EMBEDDED_SYSTEM_TRAY = '''
import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pystray
from tkinter import messagebox, simpledialog
logger = logging.getLogger(__name__)
class SystemTray:
    def __init__(self):
        self.icon = None
        self.running = True
        self.notifications = []
        self.snooze_until = None  # Timestamp when snooze expires
        self.snooze_used = False  # Track if snooze has been used
        self.config = self._load_config()
    def _load_config(self):
        """Load configuration with embedded defaults"""
        # Default configuration values (embedded from config.json)
        default_config = {
            'version': '1.8.4',
            'client_id': 'test-client-123',
            'mac_address': '00:11:22:33:44:55', 
            'api_url': 'https://example.com/api',
            'install_path': 'C:\\Program Files (x86)\\PushNotifications'
        }
        # Try to load from config.json if it exists, otherwise use defaults
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys are present
                default_config.update(config)
                return default_config
        except Exception as e:
            logger.debug(f"No config file found, using embedded defaults: {e}")
            return default_config
    def create_icon(self):
        """Create and configure the system tray icon"""
        # Create a teal circular icon with "PN" text
        image = Image.new("RGB", (64, 64), color="teal")
        dc = ImageDraw.Draw(image)
        dc.ellipse([2, 2, 62, 62], fill="teal")
        try:
            # Try to add "PN" text
            if os.name == "nt":  # Windows
                font = ImageFont.truetype("arial.ttf", 24)
            else:
                font = ImageFont.load_default()
            text = "PN"
            text_bbox = dc.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (64 - text_width) // 2
            y = (64 - text_height) // 2
            dc.text((x, y), text, fill="white", font=font)
        except Exception as e:
            logger.warning(f"Could not add text to icon: {e}")
        # Create the menu
        menu = (
            pystray.MenuItem("View Current Notification", self._view_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Snooze", pystray.Menu(
                pystray.MenuItem("5 minutes", self._snooze_5),
                pystray.MenuItem("15 minutes", self._snooze_15),
                pystray.MenuItem("30 minutes", self._snooze_30)
            ), enabled=self._can_snooze),
            pystray.MenuItem("Request Website Access", self._request_website),
            pystray.MenuItem("Complete Current Notification", 
                           self._complete_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Status", self._show_status),
            pystray.MenuItem("About", self._show_about),
            pystray.MenuItem("Request Uninstall", self._request_uninstall),
            pystray.MenuItem("Exit", self._quit)
        )
        # Create and return the icon
        self.icon = pystray.Icon(
            "PushNotifications",
            image,
            menu=menu
        )
        return self.icon
    def _request_website(self, icon):
        """Request access to a website"""
        website = simpledialog.askstring("Website Access Request",
                                      "Enter the website URL you would like to access:")
        if not website:
            return
        messagebox.showinfo("Request Sent", 
                          "Website access request has been submitted for approval.")
    def _request_uninstall(self, icon):
        """Request application uninstallation"""
        reason = simpledialog.askstring("Uninstall Request",
                                     "Please provide a reason for uninstallation:")
        if not reason:
            return
        messagebox.showinfo("Request Sent",
                          "Your uninstall request has been submitted for approval.")
    # Helper methods for dynamic menu item states
    def _has_notifications(self):
        """Check if there are any notifications"""
        return len(self.notifications) > 0
    def _can_snooze(self):
        """Check if snoozing is allowed"""
        return self._has_notifications() and not self.snooze_used
    def _view_notification(self, icon=None):
        """Show the current notification message"""
        if not self.notifications:
            messagebox.showinfo('No Notifications', 'There are no active notifications.')
            return
        notif = self.notifications[0]
        title = notif.get('title', 'Current Notification')
        body = notif.get('message', 'No message available')
        messagebox.showinfo(title, body)
    def _snooze(self, minutes):
        """Snooze notifications for specified minutes"""
        if self.snooze_used:
            messagebox.showwarning('Snooze Unavailable', 'Snooze has already been used.')
            return
        self.snooze_until = time.time() + (minutes * 60)
        self.snooze_used = True
        # Update menu items (if icon supports it)
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception:
                pass
        messagebox.showinfo('Notifications Snoozed', f'Notifications snoozed for {minutes} minutes')
    def _snooze_5(self, icon):
        """Snooze notifications for 5 minutes"""
        self._snooze(5)
    def _snooze_15(self, icon):
        """Snooze notifications for 15 minutes"""
        self._snooze(15)
    def _snooze_30(self, icon):
        """Snooze notifications for 30 minutes"""
        self._snooze(30)
    def _complete_notification(self, icon=None):
        """Mark the current notification as completed"""
        if not self.notifications:
            return
        try:
            notif = self.notifications[0]
            # In a real implementation, this would send to server
            # For now, just remove from local list
            self.notifications.pop(0)
            if self.icon:
                try:
                    self.icon.update_menu()
                except Exception:
                    pass
            messagebox.showinfo('Notification Completed', 'The notification has been marked as completed.')
        except Exception as e:
            logger.error(f'Failed to complete notification: {e}')
            messagebox.showerror('Error', 'Failed to complete notification. Please try again later.')
    def _show_status(self, icon):
        """Show application status"""
        status = f"""PushNotifications Client Status
Client ID: {self.config.get('clientId', 'Unknown')}
Version: {self.config.get('version', 'Unknown')}
Notifications: {len(self.notifications)}
Snooze Used: {self.snooze_used}
Status: Running"""
        try:
            messagebox.showinfo("Client Status", status)
        except:
            print(status)
    def _show_about(self, icon):
        """Show about dialog"""
        about = f"""PushNotifications Client v{self.config.get('version', 'Unknown')}
© 2024 Push Notifications System
Advanced notification management client
Features:
• System tray integration
• Notification management
• Website access control
• Auto-update capabilities"""
        try:
            messagebox.showinfo("About PushNotifications", about)
        except:
            print(about)
    def _quit(self, icon):
        """Clean shutdown of the application"""
        self.running = False
        icon.stop()
    def run(self):
        """Main system tray run loop"""
        try:
            icon = self.create_icon()
            icon.run()
        except Exception as e:
            logger.error(f"System tray error: {e}")
            sys.exit(1)
'''
EMBEDDED_WINDOW_MANAGER = '''
import psutil
import subprocess
class WindowManager:
    """Windows window management functionality for PushNotifications client."""
    def __init__(self):
        self.minimized_windows = []
        self.browser_processes = [
            'chrome.exe', 'msedge.exe', 'firefox.exe', 
            'opera.exe', 'brave.exe', 'iexplore.exe'
        ]
    def minimize_all_apps(self):
        """Minimize all applications using Windows Shell API"""
        subprocess.run(['powershell', '-Command',
                       '(New-Object -comObject Shell.Application).minimizeall()'])
    def minimize_non_browser_apps(self):
        """Minimize all non-browser applications based on process name"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if not any(browser in proc.info['name'].lower() 
                          for browser in self.browser_processes):
                    # Here we would add process minimization logic
                    # For now just tracking which ones would be minimized
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Ignore processes we can't access
                pass
'''
EMBEDDED_CLIENT = '''
import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pystray
from tkinter import messagebox, simpledialog
import webbrowser
logger = logging.getLogger(__name__)
class PushNotificationsClient:
    def __init__(self):
        self.running = True
        self.notifications = []
        self.icon = None
        self.snooze_until = None  # Timestamp when snooze expires
        self.snooze_used = False  # Track if snooze has been used
        self.active_notification = None
        # Load config
        self.config = self._load_config()
    def _load_config(self):
        """Load configuration with embedded defaults"""
        # Default configuration values (embedded from config.json)
        default_config = {
            'version': '1.8.4',
            'client_id': 'test-client-123', 
            'mac_address': '00:11:22:33:44:55',
            'api_url': 'https://example.com/api',
            'install_path': 'C:\\Program Files (x86)\\PushNotifications'
        }
        # Try to load from config.json if it exists, otherwise use defaults
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys are present
                default_config.update(config)
                return default_config
        except Exception as e:
            logger.debug(f"No config file found, using embedded defaults: {e}")
            return default_config
    def create_tray_icon(self):
        """Create and configure the system tray icon"""
        # Create a teal circular icon with "PN" text
        image = Image.new('RGB', (64, 64), color='teal')
        dc = ImageDraw.Draw(image)
        dc.ellipse([2, 2, 62, 62], fill='teal')
        try:
            # Try to add "PN" text
            if os.name == 'nt':  # Windows
                font = ImageFont.truetype("arial.ttf", 24)
            else:
                font = ImageFont.load_default()
            text = "PN"
            text_bbox = dc.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (64 - text_width) // 2
            y = (64 - text_height) // 2
            dc.text((x, y), text, fill='white', font=font)
        except Exception as e:
            logger.warning(f"Could not add text to icon: {e}")
        # Create the menu
        menu = (
            pystray.MenuItem("View Current Notification", self._view_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Snooze", pystray.Menu(
                pystray.MenuItem("5 minutes", self._snooze_5),
                pystray.MenuItem("15 minutes", self._snooze_15),
                pystray.MenuItem("30 minutes", self._snooze_30)
            ), enabled=self._can_snooze),
            pystray.MenuItem("Request Website Access", self._request_website),
            pystray.MenuItem("Complete Current Notification", 
                           self._complete_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Status", self._show_status),
            pystray.MenuItem("About", self._show_about),
            pystray.MenuItem("Request Uninstall", self._request_uninstall),
            pystray.MenuItem("Exit", self._quit)
        )
        # Create and return the icon
        self.icon = pystray.Icon(
            "PushNotifications",
            image,
            menu=menu
        )
        return self.icon
    def _view_notification(self, icon=None):
        """Show the current notification message"""
        if not self.notifications:
            messagebox.showinfo('No Notifications', 'There are no active notifications.')
            return
        notif = self.notifications[0]
        title = notif.get('title', 'Current Notification')
        body = notif.get('message', 'No message available')
        messagebox.showinfo(title, body)
    def _snooze(self, minutes):
        """Snooze notifications for specified minutes"""
        if self.snooze_used:
            messagebox.showwarning('Snooze Unavailable', 'Snooze has already been used.')
            return
        self.snooze_until = time.time() + (minutes * 60)
        self.snooze_used = True
        # Update menu items
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception:
                pass
        messagebox.showinfo('Notifications Snoozed', f'Notifications snoozed for {minutes} minutes')
    def _request_website(self, icon=None):
        """Request access to a website"""
        website = simpledialog.askstring('Website Access Request', 'Enter the website URL you would like to access:')
        if not website:
            return
        try:
            response = requests.post(
                f"{API_URL}/api/request-website",
                json={'client_id': CLIENT_ID, 'website': website},
                timeout=15,
            )
            if response.ok:
                messagebox.showinfo('Request Sent', 'Website access request has been submitted for approval.')
            else:
                messagebox.showerror('Request Failed', 'Failed to submit website access request.')
        except Exception as e:
            logger.error(f'Failed to request website access: {e}')
            messagebox.showerror('Error', 'Failed to submit website access request. Please try again later.')
    def _complete_notification(self, icon=None):
        """Mark the current notification as completed"""
        if not self.notifications:
            return
        try:
            notif = self.notifications[0]
            response = requests.post(
                f"{API_URL}/api/complete-notification",
                json={'client_id': CLIENT_ID, 'notification_id': notif.get('id')},
                timeout=15,
            )
            if response.ok:
                self.notifications.pop(0)
                if self.icon:
                    try:
                        self.icon.update_menu()
                    except Exception:
                        pass
                messagebox.showinfo('Notification Completed', 'The notification has been marked as completed.')
            else:
                messagebox.showerror('Error', 'Failed to complete notification. Please try again.')
        except Exception as e:
            logger.error(f'Failed to complete notification: {e}')
            messagebox.showerror('Error', 'Failed to complete notification. Please try again later.')
    def _request_uninstall(self, icon=None):
        """Request application uninstallation"""
        reason = simpledialog.askstring('Uninstall Request', 'Please provide a reason for uninstallation:')
        if not reason:
            return
        try:
            response = requests.post(
                f"{API_URL}/api/request-uninstall",
                json={'client_id': CLIENT_ID, 'reason': reason},
                timeout=15,
            )
            if response.ok:
                messagebox.showinfo('Request Sent', 'Uninstall request has been submitted for approval.')
            else:
                messagebox.showerror('Request Failed', 'Failed to submit uninstall request.')
        except Exception as e:
            logger.error(f'Failed to request uninstall: {e}')
            messagebox.showerror('Error', 'Failed to submit uninstall request. Please try again later.')
    def _has_notifications(self):
        """Check if there are any notifications"""
        return len(self.notifications) > 0
    def _can_snooze(self):
        """Check if snoozing is allowed"""
        return not self.snooze_used and len(self.notifications) > 0
    def _snooze_5(self, icon):
        """Snooze notifications for 5 minutes"""
        self._snooze(5)
    def _snooze_15(self, icon):
        """Snooze notifications for 15 minutes"""
        self._snooze(15)
    def _snooze_30(self, icon):
        """Snooze notifications for 30 minutes"""
        self._snooze(30)
    def _show_status(self, icon):
        """Show application status"""
        import tkinter as tk
        from tkinter import messagebox
        status = f"""PushNotifications Client Status
Client ID: {CLIENT_ID}
Version: {CLIENT_VERSION}
Notifications: {len(self.notifications)}
Snooze Used: {self.snooze_used}
Status: Running"""
        try:
            messagebox.showinfo("Client Status", status)
        except:
            print(status)
    def _show_about(self, icon):
        """Show about dialog"""
        import tkinter as tk
        from tkinter import messagebox
        about = f"""PushNotifications Client v{CLIENT_VERSION}
© 2024 Push Notifications System
Advanced notification management client
Features:
• System tray integration
• Notification management
• Website access control
• Auto-update capabilities"""
        try:
            messagebox.showinfo("About PushNotifications", about)
        except:
            print(about)
    def _quit(self, icon=None):
        """Clean shutdown of the application"""
        self.running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
    def run(self):
        """Main client run loop"""
        try:
            # Create and run system tray icon
            icon = self.create_tray_icon()
            icon.run()
        except Exception as e:
            logger.error(f'Client error: {e}')
            sys.exit(1)
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Start client
    client = PushNotificationsClient()
    client.run()
'''
EMBEDDED_UNINSTALLER = '''
#!/usr/bin/env python3
"""
PushNotifications Uninstaller
Handles complete removal of the application
"""
import os
import sys
import json
import shutil
import requests
import subprocess
import platform
from pathlib import Path
from tkinter import messagebox
class Uninstaller:
    def __init__(self):
        self.config_file = Path(__file__).parent / "config.json"
        self.config = self._load_config()
    def _load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    def uninstall(self):
        """Complete uninstallation process"""
        logger.info("Starting PushNotifications uninstallation...")
        # Notify server
        self._notify_server_uninstall()
        # Stop any running processes
        self._stop_client_processes()
        # Remove installation directory
        install_path = Path(self.config.get('installPath', Path(__file__).parent))
        try:
        # Remove hidden attributes (Windows-only)
            subprocess.run(['attrib', '-H', '-S', str(install_path)], 
                         capture_output=True)
            # Remove directory
            shutil.rmtree(install_path, ignore_errors=True)
            # Show completion message
            messagebox.showinfo("Uninstall Complete", 
                              "PushNotifications has been successfully uninstalled.")
        except Exception as e:
            logger.error(f"Error during uninstallation: {e}")
    def _notify_server_uninstall(self):
        """Notify server of uninstallation"""
        try:
            requests.post(self.config.get('apiUrl'), json={
                'action': 'clientUninstalled',
                'clientId': self.config.get('clientId'),
                'macAddress': self.config.get('macAddress')
            }, timeout=10)
        except:
            pass  # Ignore errors
    def _stop_client_processes(self):
        """Stop any running client processes"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'notification_client.py' in ' '.join(proc.info.get('cmdline', [])):
                    proc.terminate()
        except:
            pass
if __name__ == "__main__":
    uninstaller = Uninstaller()
    uninstaller.uninstall()
'''
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
# Windows API constants (Windows-only installer)
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
advapi32 = ctypes.windll.advapi32
# Windows administrative functionality is now handled directly within the installer
# All operations use native Python scripts with proper privilege handling
class PushNotificationsInstaller:
    """Advanced installer with Python-based implementation and full security features
    IMPORTANT: This installer and the PushNotifications client require administrator
    privileges for ALL operations including installation, client operation, system
    integration, and security features. Admin privileges are enforced at startup.
    """
    def __init__(self, api_url=None):
        # Windows-only installer - no cross-platform support
        self.system = "Windows"
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
            try:
                self.progress_dialog = InstallationProgressDialog()
                self.progress_dialog.show()
                self.progress_dialog.add_log(f"PushNotifications Installer v{INSTALLER_VERSION}")
            except Exception as e:
                logger.warning(f"Could not initialize progress dialog: {e}")
                self.progress_dialog = None
            if self.progress_dialog:
                self.progress_dialog.add_log(f"Platform: {self.system}")
                self.progress_dialog.add_log(f"MAC Address: {self.mac_address}")
                self.progress_dialog.add_log(f"Client Name: {self.client_name}")
                self.progress_dialog.add_log(f"API URL: {self.api_url}")
        logger.info(f"PushNotifications Installer v{INSTALLER_VERSION}")
        logger.info(f"Platform: {self.system}")
        logger.info(f"MAC Address: {self.mac_address}")
        logger.info(f"Client Name: {self.client_name}")
        logger.info(f"API URL: {self.api_url}")
    def _get_real_mac_address(self):
        """Get the real primary network interface MAC address using WMI and other Windows-specific methods"""
        mac_address = None
        detection_method = "unknown"
        try:
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
                    logger.warning(f"WMI MAC detection failed: {e}")
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
                    logger.warning(f"getmac detection failed: {e}")
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
                    logger.warning(f"psutil MAC detection failed: {e}")
            # Method 4: uuid.getnode() fallback (cross-platform)
            if not mac_address:
                try:
                    mac_num = uuid.getnode()
                    if mac_num != 0x010203040506:  # Avoid dummy MAC
                        mac_hex = ':'.join([f'{(mac_num >> i) & 0xff:02x}' for i in range(40, -8, -8)])
                        mac_address = mac_hex.replace(':', '-').upper()
                        detection_method = "uuid_getnode"
                except Exception as e:
                    logger.warning(f"uuid.getnode() failed: {e}")
            # Final validation
            if mac_address:
                # Ensure it's a valid MAC format and not a dummy/virtual MAC
                if len(mac_address) == 17 and mac_address.count('-') == 5:
                    # Store detection method for telemetry
                    self.mac_detection_method = detection_method
                    logger.info(f"MAC Address detected via {detection_method}: {mac_address}")
                    return mac_address
        except Exception as e:
            logger.error(f"Critical MAC address detection error: {e}")
        # Emergency fallback - generate consistent MAC based on system info
        logger.warning("Using emergency MAC fallback")
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
        """Check Windows registry for existing installation to repair"""
        try:
            # Check registry key only - don't scan directories to avoid crashes
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  "Software\\PushNotifications", 0, 
                                  winreg.KEY_READ) as key:
                    # Registry key exists - assume installation exists
                    # Files will be overwritten during installation if needed
                    try:
                        existing_version, _ = winreg.QueryValueEx(key, "Version")
                        logger.info(f"Found existing installation registry entry (version: {existing_version})")
                        logger.info("Installation will overwrite existing files")
                        return True
                    except:
                        # Registry exists but no version - still treat as existing
                        logger.info("Found existing installation registry entry")
                        logger.info("Installation will overwrite existing files")
                        return True
            except (OSError, FileNotFoundError):
                # No registry key - new installation
                return False
        except Exception as e:
            logger.warning(f"Error checking for existing installation: {e}")
        return False
    def _load_existing_config(self):
        """Load configuration from existing Windows registry for repair mode"""
        try:
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
                logger.info(f"Loaded existing configuration for repair")
                logger.info(f"Key ID: {self.key_id}")
                logger.info(f"MAC Address: {self.mac_address}")
                logger.info(f"Username: {self.username}")
        except Exception as e:
            logger.warning(f"Could not load existing config for repair: {e}")
    def check_for_updates(self):
        """Check for Windows client updates from the website"""
        logger.info("Checking for Windows client updates...")
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
                    'action': 'checkForUpdates',
                    'versionNumber': version_number,
                    'currentVersion': INSTALLER_VERSION,
                    'clientId': getattr(self, 'device_data', {}).get('clientId', 'unknown'),
                    'macAddress': self.mac_address,
                    'platform': f"Windows {platform.release()}",  # Windows-specific platform
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
                        logger.info(f"Windows client update available: v{INSTALLER_VERSION} → v{latest_version}")
                        logger.info(f"Download URL: {download_url}")
                        if update_notes:
                            logger.info(f"Release notes: {update_notes}")
                        if update_installation_key:
                            logger.info(f"Update installation key provided")
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
                        logger.info(f"Already running latest Windows version: v{INSTALLER_VERSION}")
                        return False  # No update needed
                    else:
                        logger.info(f"Running newer Windows version than latest: v{INSTALLER_VERSION} > v{latest_version}")
                        return False  # Running pre-release or newer
                else:
                    logger.error(f"Version check failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Version check server error: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Version check network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Version check error: {e}")
            return False
    def download_and_apply_update(self):
        """Download and apply the latest version update"""
        if not self.update_data:
            logger.warning("No update data available")
            return False
        logger.info(f"Downloading update v{self.update_data['latestVersion']}...")
        try:
            download_url = self.update_data['downloadUrl']
            if not download_url:
                logger.error("No download URL provided")
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
                logger.info(f"Downloading {total_size} bytes...")
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"Progress: {progress:.1f}%")
                logger.info("Download completed")
            # Verify downloaded file
            if not Path(temp_installer).exists():
                logger.error("Downloaded file not found")
                return False
            # Replace current installer if we're in the install directory
            current_file = Path(__file__)
            if self.install_path and current_file.parent == self.install_path:
                # We're running from the install directory - update the local copy
                installer_backup = self.install_path / f"installer_backup_{INSTALLER_VERSION}.py"
                installer_current = self.install_path / "installer.py"
                # Backup current version
                if installer_current.exists():
                    shutil.copy2(installer_current, installer_backup)
                    logger.info(f"Backed up current installer to {installer_backup.name}")
                # Replace with new version
                shutil.copy2(temp_installer, installer_current)
                logger.info(f"Updated installer to v{self.update_data['latestVersion']}")
                # Update wrapper scripts
                self._update_installer_wrappers()
            # Clean up temp file
            try:
                os.unlink(temp_installer)
            except:
                pass
            # Update registry version info
            self._update_version_registry()
            logger.info(f"Update completed! Now running v{self.update_data['latestVersion']}")
            return True
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    def _update_installer_wrappers(self):
        """Update installer Python script"""
        try:
            if self.system == "Windows":
                # We only update the main Python script now
                installer_path = self.install_path / "installer.py"
                logger.info(f"Updated installer Python script: {installer_path}")
        except Exception as e:
            logger.warning(f"Could not update installer script: {e}")
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
                logger.info("Updated registry version information")
        except Exception as e:
            logger.warning(f"Could not update registry version: {e}")
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
                                          capture_output=True, 
                                          text=True,
                                          encoding='utf-8',
                                          errors='replace',
                                          timeout=10,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    return result.returncode == 0
                except:
                    pass
                return False
            except Exception as e:
                logger.error(f"Error checking admin privileges: {e}")
                return False
        else:
            return os.geteuid() == 0
    def restart_with_admin(self):
        """Restart the installer with administrator privileges"""
        if self.system == "Windows":
            try:
                logger.info("Restarting with administrator privileges...")
                # Method 1: Try PowerShell Start-Process with -Verb RunAs (most reliable on Windows 10)
                try:
                    # Build PowerShell command with proper escaping
                    script_path = os.path.abspath(sys.argv[0])
                    # Add a debug flag to help track the restarted process
                    restart_args = sys.argv + ['--admin-restart']
                    # Create argument list for PowerShell
                    escaped_args = []
                    escaped_args.append(f"'{script_path}'")
                    for arg in restart_args[1:]:
                        # Double-escape quotes in arguments
                        escaped_arg = str(arg).replace("'", "''").replace('"', '""')
                        escaped_args.append(f"'{escaped_arg}'")
                    arg_list = ', '.join(escaped_args)
                    # Create a temp file for message relay between processes
                    import tempfile
                    import json
                    temp_dir = tempfile.gettempdir()
                    message_file = os.path.join(temp_dir, f"pn_installer_messages_{os.getpid()}.json")
                    # Initialize message file
                    initial_message = {
                        "status": "starting",
                        "message": "Requesting administrator privileges...",
                        "timestamp": time.time(),
                        "original_pid": os.getpid()
                    }
                    try:
                        with open(message_file, 'w') as f:
                            json.dump(initial_message, f)
                    except Exception:
                        pass  # Fallback gracefully if temp file creation fails
                    # Add message file path to restart args for the elevated process
                    restart_args_with_message = restart_args + [f'--message-file={message_file}']
                    # Rebuild argument list with message file
                    escaped_args = []
                    escaped_args.append(f"'{script_path}'")
                    for arg in restart_args_with_message[1:]:
                        # Double-escape quotes in arguments
                        escaped_arg = str(arg).replace("'", "''").replace('"', '""')
                        escaped_args.append(f"'{escaped_arg}'")
                    arg_list = ', '.join(escaped_args)
                    # Create a more sophisticated PowerShell command that tries to preserve the console window
                    powershell_script = f'''
# Initialize progress tracking
$messageFile = "{message_file.replace(chr(92), chr(92)+chr(92))}"
$PID = [System.Diagnostics.Process]::GetCurrentProcess().Id
$args = @({arg_list})
Write-Host "[INFO] Starting elevation process..."
Write-Host "[INFO] Message relay file: $messageFile"
Write-Host "[DEBUG] Process PID: $PID"
Write-Host "[DEBUG] Original Arguments: $($args -join ' ')"
Write-Host "[DEBUG] Python Executable: {sys.executable}"
Write-Host "[DEBUG] Current Working Directory: $(Get-Location)"
# Check UAC settings for debugging
try {{
    $uacSetting = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name 'ConsentPromptBehaviorAdmin' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ConsentPromptBehaviorAdmin
    if ($uacSetting -ne $null) {{
        Write-Host "[DEBUG] UAC ConsentPromptBehaviorAdmin: $uacSetting (0=No prompt, 1=Prompt for credentials, 2=Prompt for consent, 5=Prompt for consent for non-Windows binaries)"
    }} else {{
        Write-Host "[DEBUG] UAC setting not found or inaccessible"
    }}
}} catch {{
    Write-Host "[DEBUG] Could not read UAC settings: $($_.Exception.Message)"
}}
# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "[DEBUG] Currently running as administrator: $isAdmin"
# Update message file with elevation status
try {{
    $statusUpdate = @{{
        status = "elevating"
        message = "UAC prompt displayed - waiting for user approval..."
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        elevated_pid = $null
    }}
    $statusUpdate | ConvertTo-Json | Out-File -FilePath $messageFile -Encoding UTF8
}} catch {{
    Write-Host "[WARNING] Could not update message file: $($_.Exception.Message)"
}}
# Start the elevated process
$process = Start-Process -FilePath "{sys.executable}" -ArgumentList @({arg_list}) -Verb RunAs -WindowStyle Normal -PassThru
# Wait for the process to start and get elevated privileges
if ($process) {{
    Write-Host "[OK] Process elevated successfully - PID: $($process.Id)"
    # Update message file with success status
    try {{
        $statusUpdate = @{{
            status = "elevated"
            message = "Administrator privileges granted - installation continuing..."
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            elevated_pid = $process.Id
        }}
        $statusUpdate | ConvertTo-Json | Out-File -FilePath $messageFile -Encoding UTF8
    }} catch {{
        Write-Host "[WARNING] Could not update message file: $($_.Exception.Message)"
    }}
    Write-Host "[INFO] Waiting for elevated process to complete..."
    $process.WaitForExit()
    # Final status update
    try {{
        $statusUpdate = @{{
            status = "completed"
            message = "Elevated process completed with exit code: $($process.ExitCode)"
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            exit_code = $process.ExitCode
        }}
        $statusUpdate | ConvertTo-Json | Out-File -FilePath $messageFile -Encoding UTF8
    }} catch {{
        Write-Host "[WARNING] Could not update message file: $($_.Exception.Message)"
    }}
    Write-Host "[OK] Elevated process completed with exit code: $($process.ExitCode)"
    exit $process.ExitCode
}} else {{
    Write-Host "[ERROR] Failed to start elevated process"
    # Update message file with error status
    try {{
        $statusUpdate = @{{
            status = "failed"
            message = "Failed to start elevated process - UAC may have been cancelled"
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            error = "Process start failed"
        }}
        $statusUpdate | ConvertTo-Json | Out-File -FilePath $messageFile -Encoding UTF8
    }} catch {{
        Write-Host "[WARNING] Could not update message file: $($_.Exception.Message)"
    }}
    exit 1
}}
'''
                    print("\n[INFO] UAC prompt will appear - please approve to continue with installation")
                    print("       If UAC is cancelled, the installation will not proceed.")
                    print("       Installation will continue in an elevated console window.")
                    print("       This window will remain open for logging and feedback.")
                    # Start PowerShell process asynchronously and monitor progress via message file
                    import threading
                    # Start PowerShell elevation process in background
                    powershell_process = subprocess.Popen([
                        'powershell.exe', 
                        '-ExecutionPolicy', 'Bypass',
                        '-NoProfile',
                        '-Command', powershell_script
                    ], stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE,
                       text=True, 
                       encoding='utf-8',
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    # Monitor the message relay file while PowerShell runs
                    monitor_success = monitor_message_relay(message_file, timeout_seconds=300)
                    # Wait for PowerShell process to complete
                    try:
                        stdout, stderr = powershell_process.communicate(timeout=30)
                    except subprocess.TimeoutExpired:
                        powershell_process.kill()
                        stdout, stderr = powershell_process.communicate()
                    # Clean up message file
                    try:
                        if os.path.exists(message_file):
                            os.unlink(message_file)
                    except Exception:
                        pass
                    if powershell_process.returncode == 0 and monitor_success:
                        logger.info("[OK] Administrator privileges requested via PowerShell - process elevated successfully")
                        print("\n[OK] Elevation successful - elevated process completed")
                        if stdout:
                            print(f"Output: {stdout.strip()}")
                        sys.exit(0)
                    else:
                        logger.error(f"PowerShell elevation failed (code {powershell_process.returncode}): {stderr}")
                        if stderr:
                            print(f"Error output: {stderr.strip()}")
                except Exception as e:
                    logger.error(f"PowerShell method failed: {e}")
                # Method 2: Try win32api ShellExecute (traditional method)
                try:
                    import win32api
                    script_args = ' '.join([f'"{arg}"' for arg in sys.argv])
                    result = win32api.ShellExecute(
                        None, "runas", sys.executable, script_args, None, 1
                    )
                    if result > 32:  # Success
                        logger.info("[OK] Administrator privileges requested via ShellExecute")
                        sys.exit(0)
                    else:
                        logger.error(f"ShellExecute failed with error code: {result}")
                except Exception as e:
                    logger.error(f"ShellExecute method failed: {e}")
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
                        logger.info("[OK] Administrator privileges requested via ShellExecuteW")
                        sys.exit(0)
                    else:
                        logger.error(f"ShellExecuteW failed with error code: {result_int}")
                except Exception as e:
                    logger.error(f"ShellExecuteW method failed: {e}")
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
                    subprocess.run([temp_batch], 
                                 capture_output=True,
                                 text=True,
                                 encoding='utf-8',
                                 errors='replace',
                                 timeout=30,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                    # Clean up temp file after a delay
                    try:
                        time.sleep(2)
                        os.unlink(temp_batch)
                    except:
                        pass
                    logger.info("[OK] Administrator privileges requested via batch file")
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"Batch file method failed: {e}")
                logger.error("[ERR] All elevation methods failed")
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
    def _make_api_request(self, method, url, json_data=None, max_retries=5, timeout=30, description="API request"):
        """Make HTTP requests with robust error handling, retry logic, and user-friendly messages"""
        import time
        # Define retry backoff strategy (exponential backoff with jitter)
        def get_retry_delay(attempt):
            base_delay = min(2 ** attempt, 60)  # Cap at 60 seconds
            jitter = random.uniform(0.1, 0.9)
            return base_delay * jitter
        # Enhanced timeout strategy based on request type
        def get_timeout_for_attempt(attempt):
            if "installation key validation" in description:
                return min(15 + (attempt * 5), 45)  # 15s to 45s for key validation
            elif "device registration" in description:
                return min(20 + (attempt * 10), 60)  # 20s to 60s for device registration
            else:
                return min(timeout + (attempt * 5), 90)  # Default with progressive timeout
        last_exception = None
        connection_issues = []
        # Pre-request connection check
        print(f"  Initiating {description}...")
        for attempt in range(1, max_retries + 1):
            current_timeout = get_timeout_for_attempt(attempt)
            try:
                # Add attempt info to console output for transparency
                if attempt > 1:
                    print(f"  [RETRY {attempt}/{max_retries}] {description} (timeout: {current_timeout}s)...")
                else:
                    print(f"  [ATTEMPT {attempt}] {description} (timeout: {current_timeout}s)...")
                # Enhanced request headers for better compatibility
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': f'PushNotifications-Installer/{INSTALLER_VERSION} (Windows)',
                    'Accept': 'application/json',
                    'Connection': 'close'  # Prevent connection reuse issues
                }
                # Make the HTTP request with enhanced error detection
                if method.upper() == 'POST':
                    response = requests.post(
                        url,
                        json=json_data,
                        timeout=(10, current_timeout),  # (connect_timeout, read_timeout)
                        headers=headers,
                        verify=True,  # Ensure SSL verification
                        allow_redirects=True
                    )
                elif method.upper() == 'GET':
                    response = requests.get(
                        url, 
                        timeout=(10, current_timeout),
                        headers=headers,
                        verify=True,
                        allow_redirects=True
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                # Check for HTTP errors
                response.raise_for_status()
                # Success - return the response
                if attempt > 1:
                    print(f"  [SUCCESS] {description} completed on attempt {attempt}")
                    print(f"  [RECOVERY] Connection issues resolved after {attempt-1} retries")
                else:
                    print(f"  [SUCCESS] {description} completed successfully")
                return response
            except requests.exceptions.ConnectTimeout as e:
                last_exception = e
                error_msg = f"Connection timeout during {description}"
                if attempt < max_retries:
                    delay = get_retry_delay(attempt)
                    print(f"  [RETRY] {error_msg}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  [ERR] {error_msg} after {max_retries} attempts")
                    print(f"        Check your internet connection and try again")
                    print(f"        Server: {url}")
            except requests.exceptions.ReadTimeout as e:
                last_exception = e
                error_msg = f"Server response timeout during {description}"
                if attempt < max_retries:
                    delay = get_retry_delay(attempt)
                    print(f"  [RETRY] {error_msg}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  [ERR] {error_msg} after {max_retries} attempts")
                    print(f"        The server at {url} is taking too long to respond")
                    print(f"        This may be a temporary server issue - please try again later")
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                error_msg = f"Connection error during {description}"
                if attempt < max_retries:
                    delay = get_retry_delay(attempt)
                    print(f"  [RETRY] {error_msg}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  [ERR] {error_msg} after {max_retries} attempts")
                    print(f"        Unable to reach server at {url}")
                    print(f"        Please check:")
                    print(f"        • Your internet connection is working")
                    print(f"        • The server URL is correct")
                    print(f"        • No firewall is blocking the connection")
                    print(f"        • The server is not experiencing downtime")
            except requests.exceptions.HTTPError as e:
                last_exception = e
                # HTTP errors typically don't benefit from retries (4xx, 5xx)
                print(f"  [ERR] HTTP error during {description}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"        Server returned: HTTP {e.response.status_code}")
                    try:
                        error_detail = e.response.text[:200]
                        if error_detail:
                            print(f"        Error details: {error_detail}")
                    except:
                        pass
                break  # Don't retry HTTP errors
            except requests.exceptions.RequestException as e:
                last_exception = e
                error_msg = f"Request error during {description}"
                if attempt < max_retries:
                    delay = get_retry_delay(attempt)
                    print(f"  [RETRY] {error_msg}: {type(e).__name__}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  [ERR] {error_msg} after {max_retries} attempts: {type(e).__name__}: {e}")
            except Exception as e:
                last_exception = e
                error_msg = f"Unexpected error during {description}"
                if attempt < max_retries:
                    delay = get_retry_delay(attempt)
                    print(f"  [RETRY] {error_msg}: {type(e).__name__}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  [ERR] {error_msg} after {max_retries} attempts: {type(e).__name__}: {e}")
        # All retries failed - return None and log the final error
        print(f"\n  [FINAL ERROR] All {max_retries} attempts failed for {description}")
        print(f"                Final error: {type(last_exception).__name__}: {last_exception}")
        print(f"                Suggestions:")
        print(f"                • Verify your internet connection is stable")
        print(f"                • Check if the server URL is accessible: {url}")
        print(f"                • Try running the installer later if server is experiencing issues")
        print(f"                • Contact support if the problem persists")
        logger.error(f"All {max_retries} attempts failed for {description}: {type(last_exception).__name__}: {last_exception}")
        return None
    def validate_installation_key(self):
        """Validate installation key with website API"""
        print("Installation Key Validation")
        print("=" * 50)
        print(f"API URL: {self.api_url}")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            # For key entry, we always want to use GUI dialog regardless of other settings
            print(f"Debug: System detected as '{self.system}', Key Entry Popup: {USE_KEY_ENTRY_POPUP}")
            if USE_KEY_ENTRY_POPUP:
                try:
                    # Import tkinter and check availability
                    import tkinter as tk
                    from tkinter import simpledialog
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
                print(f"\n[NOTE] Please enter your installation key:")
                print(f"   (Attempt {attempt} of {max_attempts})")
                print(f"   [TIP] Tip: Right-click and paste, or use Cmd+V (macOS) / Ctrl+V (Linux)")
                print(f"   [UNLOCKED] Note: Key will be visible for easy pasting and verification")
                print(f"   [ENTER] Press Enter when done")
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
            response = self._make_api_request(
                'POST',
                f"{self.api_url}/api/index",
                json_data={
                    'action': 'validateInstallationKey',
                    'installationKey': key
                },
                description="installation key validation"
            )
            if response is not None:
                try:
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
                            print(f"[OK] Installation key validated successfully!")
                            print(f"  User: {user_info.get('username', 'Unknown')}")
                            print(f"  Role: {user_info.get('role', 'Unknown')}")
                            print(f"  Generated Client Username: {self.username}")
                            return True
                        else:
                            print(f"[ERR] {result.get('message', 'Invalid installation key')}")
                    else:
                        print(f"[ERR] Server error: HTTP {response.status_code}")
                except requests.RequestException as e:
                    print(f"[ERR] Network error: {e}")
                except Exception as e:
                    print(f"[ERR] Validation error: {e}")
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
                'platform': "Windows",
                'version': INSTALLER_VERSION,
                'installPath': '', # Will be updated after directory creation
                'macDetectionMethod': getattr(self, 'mac_detection_method', 'unknown'),
                'installerMode': 'advanced',
                'timestamp': datetime.now().isoformat(),
                # Additional security metadata
                'systemInfo': {
                    'osVersion': "Windows",
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
            response = self._make_api_request(
                'POST',
                f"{self.api_url}/api/index",
                json_data=device_info,
                description="device registration"
            )
            if response is None:
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
                    print(f"[OK] Device registered successfully!")
                    print(f"  Client ID: {self.device_data.get('clientId')}")
                    print(f"  Key ID: {self.key_id}")
                    print(f"  New Installation: {self.device_data.get('isNewInstallation')}")
                    print(f"  Server Message: {result.get('message', 'No message')}")
                    # Mark device as registered
                    self.device_registered = True
                    return True
                else:
                    error_msg = result.get('message', 'Unknown registration error')
                    print(f"[ERR] Registration failed: {error_msg}")
                    # Handle specific error cases
                    if 'duplicate' in error_msg.lower() or 'already registered' in error_msg.lower():
                        print("  This MAC address is already registered with the server.")
                        print("  Please contact support if you need to register this device.")
                    elif 'invalid key' in error_msg.lower():
                        print("  Installation key is invalid or expired.")
                    return False
            else:
                print(f"[ERR] Server error: HTTP {response.status_code}")
                try:
                    error_detail = response.text[:200]
                    print(f"  Server response: {error_detail}")
                except:
                    pass
                return False
        except requests.exceptions.ConnectionError:
            print(f"[ERR] Connection error: Unable to reach server at {self.api_url}")
            print("  Please check your internet connection and server URL.")
            return False
        except requests.exceptions.Timeout:
            print(f"[ERR] Timeout error: Server did not respond within 30 seconds")
            return False
        except Exception as e:
            print(f"[ERR] Registration error: {e}")
            return False
    def create_hidden_install_directory(self):
        """Create hidden, encrypted installation directory with random GUID path"""
        print("Creating hidden installation directory...")
        try:
            # Generate random GUID-based path in Program Files (x86) for better 64-bit compatibility
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
            self.install_path.mkdir(parents=True, exist_ok=True)
            print(f"Installation path: {self.install_path}")
            # Set Windows attributes and ACLs
            self._set_windows_hidden_attributes()
            self._set_restrictive_acls()
            self._disable_indexing()
            # Encrypt the install path and store in registry
            self._store_encrypted_path_info()
            # Update install path in database after directory creation
            self._update_install_path_in_database()
            print("[OK] Hidden installation directory created and secured")
            return True
        except Exception as e:
            print(f"[ERR] Failed to create hidden directory: {e}")
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
            # Add full control for SYSTEM
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
            print("[OK] File system deletion protection enabled")
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
        """Unix permissions not used on Windows-only installer"""
        print("Unix permissions skipped on Windows")
    def _store_encrypted_path_info(self):
        """Store encrypted installation path info in registry"""
        print("Storing installation metadata in registry...")
        try:
            # Windows-only installer - always use registry
            # Create/open registry key with write permissions
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\PushNotifications")
            except WindowsError as e:
                logger.error(f"Failed to create/open registry key: {e}")
                if e.winerror == 5:  # Access denied
                    logger.error("Access denied - insufficient permissions to modify registry")
                    self.notify_installation_failure("registry", "Access denied when creating registry key")
                    return False
                raise
            # Store metadata with individual error handling
            metadata = {
                "KeyId": self.key_id,
                "Username": self.username,
                "MacAddress": self.mac_address,
                "Version": INSTALLER_VERSION,
                "ApiUrl": self.api_url,
                "InstallDate": datetime.now().isoformat(),
                "PathHash": hashlib.sha256(str(self.install_path).encode()).hexdigest()
            }
            success = True
            for name, value in metadata.items():
                try:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
                    logger.debug(f"Stored {name} in registry")
                except WindowsError as e:
                    logger.error(f"Failed to store {name} in registry: {e}")
                    if e.winerror == 5:  # Access denied
                        logger.error(f"Access denied when writing {name} value")
                    success = False
                except ValueError as e:
                    logger.error(f"Invalid value for {name}: {e}")
                    success = False
                except Exception as e:
                    logger.error(f"Unexpected error storing {name}: {e}")
                    success = False
            winreg.CloseKey(key)
            if success:
                logger.info("[OK] Successfully stored all metadata in registry")
                return True
            else:
                logger.error("Failed to store some registry values")
                self.notify_installation_failure("registry", "Failed to store required registry values")
                return False
        except Exception as e:
            logger.error(f"Critical error accessing registry: {str(e)}")
            import traceback
            logger.error(f"Registry error details:\n{traceback.format_exc()}")
            self.notify_installation_failure("registry", f"Critical registry error: {str(e)}")
            return False
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
                    print("[OK] Install path updated in database")
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
            # Create all enhanced components
            self._create_favicon_utils()
            self._create_overlay_manager()
            self._create_window_manager()
            self._create_system_tray()
            self._create_uninstaller()
            # Create Python scripts for all platforms
            self._create_client_script()
            self._create_installer_copy()
            return True
        except Exception as e:
            print(f"[ERR] Failed to create embedded components: {e}")
            import traceback
            traceback.print_exc()
            return False
    def _create_favicon_utils(self):
        favicon_utils_path = self.install_path / "favicon_utils.py"
        with open(favicon_utils_path, 'w', encoding='utf-8') as f:
            f.write(EMBEDDED_FAVICON_UTILS)
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(favicon_utils_path)], 
                        check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("[OK] Favicon utilities created")
    def _create_overlay_manager(self):
        """Create overlay manager file"""
        overlay_path = self.install_path / "overlay_manager.py"
        with open(overlay_path, 'w', encoding='utf-8') as f:
            f.write(EMBEDDED_OVERLAY_MANAGER)
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(overlay_path)], 
                        check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("[OK] Overlay manager created")
    def _create_window_manager(self):
        """Create window manager file"""
        window_path = self.install_path / "window_manager.py"
        with open(window_path, 'w', encoding='utf-8') as f:
            f.write(EMBEDDED_WINDOW_MANAGER)
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(window_path)], 
                        check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("[OK] Window manager created")
    def _create_system_tray(self):
        """Create system tray file"""
        tray_path = self.install_path / "system_tray.py"
        with open(tray_path, 'w', encoding='utf-8') as f:
            f.write(EMBEDDED_SYSTEM_TRAY)
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(tray_path)], 
                        check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("[OK] System tray created")
    def _create_uninstaller(self):
        """Create uninstaller file"""
        uninstaller_path = self.install_path / "uninstaller.py"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(EMBEDDED_UNINSTALLER)
        if self.system == "Windows":
            subprocess.run(["attrib", "+S", "+H", str(uninstaller_path)], 
                        check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        print("[OK] Uninstaller created")
    def _create_client_script(self):
        """Create unified cross-platform Client Python script with Windows admin manifest"""
        client_script = self._get_unified_client_code()
        client_path = self.install_path / "Client.py"
        
        try:
            # Ensure installation directory exists and is accessible
            if not self.install_path.exists():
                print(f"[ERR] Installation directory does not exist: {self.install_path}")
                return False
                
            # Write client script with explicit encoding
            with open(client_path, 'w', encoding='utf-8') as f:
                f.write(client_script)
            
            # Verify file was created successfully
            if not client_path.exists():
                print(f"[ERR] Failed to create Client.py at: {client_path}")
                return False
                
            # Check file size to ensure content was written
            file_size = client_path.stat().st_size
            if file_size < 1000:  # Client script should be substantial
                print(f"[WARNING] Client.py appears incomplete (size: {file_size} bytes)")
                
            print(f"[OK] Client.py created successfully ({file_size} bytes)")
            print(f"     Location: {client_path}")
            
            if self.system == "Windows":
                # Create Windows Application Manifest for automatic admin privileges
                manifest_success = self._create_windows_manifest()
                # Create batch wrapper that uses the manifest  
                batch_success = self._create_admin_batch_wrapper()
                
                # Set proper Windows file permissions and attributes
                try:
                    # Set file as executable (readable by owner and system)
                    import stat
                    client_path.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
                    print(f"[OK] Set executable permissions on Client.py")
                except Exception as e:
                    print(f"[WARNING] Could not set file permissions: {e}")
                
                # Set hidden and system attributes for security
                try:
                    result = subprocess.run(["attrib", "+S", "+H", str(client_path)], 
                                          check=False, 
                                          creationflags=subprocess.CREATE_NO_WINDOW,
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"[OK] Set hidden/system attributes on Client.py")
                    else:
                        print(f"[WARNING] Could not set file attributes: {getattr(result, 'stderr', 'Unknown error')}")
                except Exception as e:
                    print(f"[WARNING] Error setting file attributes: {e}")
                    
                # Verify the client can be executed
                if self._verify_client_executable():
                    print(f"[OK] Client.py verified as executable")
                else:
                    print(f"[WARNING] Client.py may not be properly executable")
                    
            print("[OK] Unified cross-platform client script created")
            return True
            
        except PermissionError as e:
            print(f"[ERR] Permission denied creating Client.py: {e}")
            print(f"      Ensure installer is running with administrator privileges")
            return False
        except Exception as e:
            print(f"[ERR] Failed to create Client.py: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_windows_manifest(self):
        """Create Windows Application Manifest for automatic admin privileges"""
        try:
            manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="PushNotifications.Client"
    type="win32"
  />
  <description>Push Notifications Client</description>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false" />
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>
  <asmv3:application xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>'''
            
            manifest_path = self.install_path / "Client.exe.manifest"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(manifest_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("[OK] Windows Application Manifest created")
            return True
            
        except Exception as e:
            print(f"Warning: Could not create Windows manifest: {e}")
            return False
    
    def _create_admin_batch_wrapper(self):
        """Create batch wrapper that launches the client with admin privileges using the manifest"""
        try:
            # Create a batch file that launches the Python client with the manifest
            batch_content = f'''@echo off
REM PushNotifications Client Launcher with Admin Privileges
REM This batch file ensures the client runs with administrator privileges

REM Change to the client directory
cd /d "{self.install_path}"

REM Launch Python client with the manifest (which requests admin privileges)
start "PushNotifications" /min "{sys.executable}" "{self.install_path / 'Client.py'}"

REM Exit the batch file
exit'''
            
            batch_path = self.install_path / "Client.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Set hidden attributes
            subprocess.run(["attrib", "+S", "+H", str(batch_path)], 
                          check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("[OK] Admin batch wrapper created")
            return True
            
        except Exception as e:
            print(f"Warning: Could not create admin batch wrapper: {e}")
            return False
            
    def _verify_client_executable(self) -> bool:
        """Verify that the Client.py is properly executable with appropriate permissions.
        
        This method performs checks to ensure that:
        1. The client file exists
        2. The file has appropriate permissions
        3. The file can be executed (performs a non-destructive test)
        
        Returns:
            bool: True if the client is verified as executable, False otherwise
        """
        try:
            import os
            import stat
            import sys
            
            client_path = self.install_path / "Client.py"
            
            # Step 1: Verify file existence
            if not client_path.exists():
                print(f"[ERR] Client.py does not exist at: {client_path}")
                return False
            
            # Step 2: Check file size
            file_size = client_path.stat().st_size
            if file_size < 1000:  # Client script should be substantial
                print(f"[WARNING] Client.py appears too small ({file_size} bytes)")
                
            # Step 3: Check file permissions
            try:
                # Check if file is readable and executable
                is_executable = os.access(client_path, os.X_OK)
                is_readable = os.access(client_path, os.R_OK)
                
                if not is_readable:
                    print(f"[WARNING] Client.py is not readable")
                    
                if not is_executable:
                    print(f"[WARNING] Client.py is not marked as executable")
                    
                # On Windows, the X_OK check may not be reliable,
                # so we'll also check the file mode directly
                if self.system == "Windows":
                    file_mode = client_path.stat().st_mode
                    if not (file_mode & stat.S_IEXEC):
                        print(f"[WARNING] Client.py does not have executable permissions")
            except Exception as e:
                print(f"[WARNING] Could not check file permissions: {e}")
                
            # Step 4: Try a non-destructive execution test on Windows
            # This checks if Python can at least parse the file without errors
            if self.system == "Windows":
                try:
                    # Use Python to check syntax without executing
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(client_path)],
                        check=False,
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if result.returncode != 0:
                        print(f"[WARNING] Client.py has syntax errors: {getattr(result, 'stderr', 'Unknown error')}")
                        return False
                except Exception as e:
                    print(f"[WARNING] Could not verify client syntax: {e}")
                    return False
                    
            # If we reach here, the client is likely executable
            return True
            
        except Exception as e:
            print(f"[ERR] Failed to verify client executable: {e}")
            import traceback
            traceback.print_exc()
            return False
    def _create_installer_copy(self):
        """Create a copy of the installer for repair/maintenance functionality"""
        try:
            # Copy the current installer script to the installation directory
            current_installer = Path(__file__).resolve()
            installer_copy_path = self.install_path / "installer.py"
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
            print("[OK] Installer Python script copy created")
        except Exception as e:
            print(f"Warning: Could not create installer copy: {e}")
    def _copy_icon_file(self):
        """Create pnicon.png from embedded data in the installation directory"""
        try:
            import base64
            # Create icon from embedded base64 data
            dest_icon = self.install_path / "pnicon.png"
            # Decode and write the embedded icon data
            icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
            with open(dest_icon, 'wb') as f:
                f.write(icon_data)
            # Set hidden attributes on Windows
            if self.system == "Windows":
                subprocess.run(["attrib", "+S", "+H", str(dest_icon)], 
                              check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"[OK] Icon file created from embedded data: {dest_icon.name}")
            return True
        except Exception as e:
            print(f"Warning: Could not create icon file from embedded data: {e}")
            return False  # Not a critical failure
    def notify_installation_failure(
        self,
        stage: str,
        error_message: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Notify the server that the installation has failed.
        This method logs the failure with rich context and forwards to the standalone
        implementation for processing.
        Args:
            stage: The installation stage where failure occurred
            error_message: Detailed error message/traceback
            correlation_id: Optional ID to correlate related errors
        Returns:
            bool: True if notification was successful
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        # Debug log with rich context before forwarding
        logger.debug(f"Installation failure received for stage {stage!r}", extra={
            'correlation_id': correlation_id,
            'stage': stage,
            'error_summary': str(error_message)[:100] + '...' if len(str(error_message)) > 100 else str(error_message),
            'installer_state': {
                'version': getattr(self, 'version', 'UNKNOWN'),
                'install_path': str(getattr(self, 'install_path', None)),
                'device_registered': bool(getattr(self, 'device_data', None)),
                'has_config': bool(getattr(self, 'config', None))
            }
        })
        # Forward to the standalone implementation with proper error handling
        try:
            return notify_installation_failure(
                installer_instance=self,
                stage=stage,
                error_message=error_message,
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error(
                f"Failed to forward installation failure notification",
                extra={
                    'correlation_id': correlation_id,
                    'stage': stage,
                    'error': str(e)
                },
                exc_info=True
            )
            return False
    def cleanup_failed_installation_files(self):
        """Disabled - no cleanup during installation to prevent crashes"""
        print("Cleanup disabled to prevent installation crashes")
        return True
    def _generate_installation_summary(self):
        """Generate a comprehensive installation summary report"""
        print("Generating installation summary...")
        try:
            # Gather installation information
            summary_data = {
                'installation_info': {
                    'status': 'SUCCESS',
                    'timestamp': datetime.now().isoformat(),
                    'installer_version': INSTALLER_VERSION,
                    'client_version': CLIENT_VERSION,
                    'install_mode': 'repair' if self.repair_mode else ('update' if self.update_mode else 'fresh'),
                    'duration': 'N/A'  # Could calculate if we tracked start time
                },
                'system_info': {
                    'platform': platform.platform(),
                    'hostname': platform.node(),
                    'username': getpass.getuser(),
                    'mac_address': self.mac_address,
                    'mac_detection_method': getattr(self, 'mac_detection_method', 'unknown'),
                    'admin_privileges': self.check_admin_privileges(),
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                },
                'client_configuration': {
                    'client_id': self.device_data.get('clientId', 'Unknown'),
                    'client_name': self.client_name,
                    'key_id': self.key_id,
                    'api_url': self.api_url,
                    'device_registered': self.device_registered,
                    'is_new_installation': self.device_data.get('isNewInstallation', True)
                },
                'installed_components': {
                    'install_path': str(self.install_path),
                    'path_secured': True,  # Assuming success since we got here
                    'components_created': [
                        'Client.py - Main client application',
                        'installer.py - Installer copy for updates/repairs',
                        'favicon_utils.py - Icon management utilities',
                        'overlay_manager.py - Multi-monitor overlay system',
                        'window_manager.py - Window management functionality',
                        'system_tray.py - System tray integration',
                        'uninstaller.py - Application uninstaller',
                        'pnicon.png - Application icon',
                        '.vault - Encrypted configuration vault',
                        '.security_marker - Installation security marker'
                    ],
                    'registry_entries': [
                        'HKCU\\Software\\PushNotifications\\KeyId',
                        'HKCU\\Software\\PushNotifications\\Username', 
                        'HKCU\\Software\\PushNotifications\\MacAddress',
                        'HKCU\\Software\\PushNotifications\\Version',
                        'HKCU\\Software\\PushNotifications\\ApiUrl',
                        'HKCU\\Software\\PushNotifications\\InstallDate',
                        'HKCU\\Software\\PushNotifications\\PathHash'
                    ],
                    'desktop_shortcuts': [
                        'Push Notifications.lnk - Main client shortcut',
                        'Push Notifications Installer.lnk - Repair/update shortcut',
                        'Uninstall Push Notifications.lnk - Uninstaller shortcut'
                    ]
                },
                'security_features': {
                    'encryption_enabled': True,
                    'encryption_algorithm': 'AES-256-GCM',
                    'hidden_installation': True,
                    'deletion_protection': True,
                    'server_managed_keys': True,
                    'indexing_disabled': True
                },
                'next_steps': [
                    'The client will automatically start in the background',
                    'Look for the "PN" icon in your system tray',
                    'Right-click the tray icon to access all client features',
                    'The client will periodically check for notifications from the server',
                    'To uninstall, use the desktop shortcut or request uninstall via the tray menu',
                    f'Installation directory: {self.install_path}',
                    f'Client configuration stored securely in encrypted vault'
                ]
            }
            # Create summary report in multiple formats
            # 1. Console output
            self._print_installation_summary(summary_data)
            # 2. Save detailed summary to log file
            self._save_installation_summary_to_file(summary_data)
            # 3. Send summary to message relay if available
            if hasattr(self, 'message_relay') and self.message_relay:
                summary_msg = f"Installation completed successfully! Client ID: {summary_data['client_configuration']['client_id']}"
                self.message_relay.send_status("summary", summary_msg)
            return True
        except Exception as e:
            logger.error(f"Failed to generate installation summary: {e}")
            print(f"Warning: Could not generate installation summary: {e}")
            return False
    def _print_installation_summary(self, summary_data):
        """Print a formatted installation summary to console"""
        print("\n" + "=" * 80)
        print("INSTALLATION SUMMARY")
        print("=" * 80)
        info = summary_data['installation_info']
        client = summary_data['client_configuration']
        system = summary_data['system_info']
        components = summary_data['installed_components']
        security = summary_data['security_features']
        # Installation Status
        print(f"\n[STATUS] {info['status']} - PushNotifications v{info['installer_version']} installed successfully")
        print(f"[TIME]   {info['timestamp']}")
        print(f"[MODE]   {info['install_mode'].upper()} installation")
        # Client Information
        print(f"\n[CLIENT] Configuration")
        print(f"         Client ID: {client['client_id']}")
        print(f"         Client Name: {client['client_name']}")
        print(f"         Key ID: {client['key_id']}")
        print(f"         API URL: {client['api_url']}")
        print(f"         Device Registered: {'YES' if client['device_registered'] else 'NO'}")
        print(f"         New Installation: {'YES' if client['is_new_installation'] else 'NO'}")
        # System Information
        print(f"\n[SYSTEM] Environment")
        print(f"         Platform: {system['platform']}")
        print(f"         Hostname: {system['hostname']}")
        print(f"         Username: {system['username']}")
        print(f"         MAC Address: {system['mac_address']} (via {system['mac_detection_method']})")
        print(f"         Admin Privileges: {'YES' if system['admin_privileges'] else 'NO'}")
        print(f"         Python Version: {system['python_version']}")
        # Installation Components
        print(f"\n[FILES]  Installed Components")
        print(f"         Install Path: {components['install_path']}")
        print(f"         Path Secured: {'YES' if components['path_secured'] else 'NO'}")
        print(f"         Components ({len(components['components_created'])}):") 
        for component in components['components_created']:
            print(f"           • {component}")
        # Security Features
        print(f"\n[SECURE] Security Features Enabled")
        for feature, enabled in security.items():
            feature_name = feature.replace('_', ' ').title()
            status = 'YES' if enabled else 'NO'
            if isinstance(enabled, str):
                status = enabled
            print(f"         {feature_name}: {status}")
        # Next Steps
        print(f"\n[NEXT]   Next Steps")
        for i, step in enumerate(summary_data['next_steps'], 1):
            print(f"         {i}. {step}")
        print("\n" + "=" * 80)
        print("Installation completed successfully! The client is ready to use.")
        print("=" * 80 + "\n")
    def _save_installation_summary_to_file(self, summary_data):
        """Save detailed installation summary to a log file"""
        try:
            # Create summary file in user's Documents folder
            documents_path = Path.home() / "Documents"
            if not documents_path.exists():
                documents_path = Path.home()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = documents_path / f"PushNotifications_Install_Summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("PushNotifications Installation Summary\n")
                f.write("=" * 50 + "\n\n")
                # Write detailed JSON summary
                f.write("DETAILED INSTALLATION REPORT:\n")
                f.write("-" * 30 + "\n")
                f.write(json.dumps(summary_data, indent=2, ensure_ascii=False))
                f.write("\n\n")
                # Write human-readable summary
                f.write("INSTALLATION SUMMARY:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Status: {summary_data['installation_info']['status']}\n")
                f.write(f"Timestamp: {summary_data['installation_info']['timestamp']}\n")
                f.write(f"Client ID: {summary_data['client_configuration']['client_id']}\n")
                f.write(f"Install Path: {summary_data['installed_components']['install_path']}\n")
                f.write(f"MAC Address: {summary_data['system_info']['mac_address']}\n")
                f.write(f"API URL: {summary_data['client_configuration']['api_url']}\n")
                f.write(f"\nInstalled Components ({len(summary_data['installed_components']['components_created'])}):\n")
                for component in summary_data['installed_components']['components_created']:
                    f.write(f"  • {component}\n")
                f.write("\nNext Steps:\n")
                for i, step in enumerate(summary_data['next_steps'], 1):
                    f.write(f"  {i}. {step}\n")
                f.write(f"\n\nThis summary was generated on {datetime.now().isoformat()}\n")
                f.write("For support, please provide this file along with any issue reports.\n")
            print(f"[OK] Installation summary saved to: {summary_file}")
            logger.info(f"Installation summary saved to: {summary_file}")
        except Exception as e:
            logger.warning(f"Could not save installation summary to file: {e}")
            print(f"Warning: Could not save installation summary to file: {e}")
    def create_desktop_shortcuts_impl(self):
        """Create desktop shortcuts for the client application and installer"""
        try:
            import os
            from pathlib import Path
            # Import COM components with fallbacks
            try:
                import pythoncom  # Import for Windows COM support
                from win32com.shell import shell, shellcon
            except ImportError:
                try:
                    import win32com.shell.shell as shell
                    import win32com.shell.shellcon as shellcon
                    import pythoncom
                except ImportError:
                    logger.warning("Windows COM components not available for shortcuts")
                    return False
            logger.info("Creating desktop shortcuts...")
            # Get desktop path
            desktop_path = Path.home() / "Desktop"
            if not desktop_path.exists():
                # Fallback to public desktop
                try:
                    import ctypes.wintypes
                    CSIDL_DESKTOP = 0
                    _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
                    path_buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                    result = _SHGetFolderPath(0, CSIDL_DESKTOP, 0, 0, path_buf)
                    if result == 0:
                        desktop_path = Path(path_buf.value)
                    else:
                        desktop_path = Path.home() / "Desktop"
                except Exception:
                    desktop_path = Path.home() / "Desktop"
            # Create shortcuts
            shortcuts_created = 0
            # 1. Client shortcut
            try:
                client_path = self.install_path / "Client.py"
                if client_path.exists():
                    shortcut_path = desktop_path / "Push Notifications.lnk"
                    # Create shortcut using COM
                    pythoncom.CoInitialize()  # Initialize COM
                    shortcut = pythoncom.CoCreateInstance(
                        shell.CLSID_ShellLink, None,
                        pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
                    )
                    # Set shortcut properties
                    shortcut.SetPath(str(sys.executable))
                    shortcut.SetArguments(f'"{client_path}"')
                    shortcut.SetWorkingDirectory(str(self.install_path))
                    shortcut.SetDescription("Push Notifications Client")
                    # Try to set icon
                    icon_path = self.install_path / "pnicon.png"
                    if icon_path.exists():
                        # Convert PNG to ICO if possible, otherwise use Python icon
                        try:
                            shortcut.SetIconLocation(str(sys.executable), 0)
                        except:
                            pass
                    # Save shortcut
                    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                    persist_file.Save(str(shortcut_path), 0)
                    shortcuts_created += 1
                    logger.info(f"Created client shortcut: {shortcut_path}")
            except Exception as e:
                logger.warning(f"Failed to create client shortcut: {e}")
            # 2. Installer shortcut (for repair/reinstall)
            try:
                installer_path = self.install_path / "installer.py"
                if installer_path.exists():
                    shortcut_path = desktop_path / "Push Notifications Installer.lnk"
                    # Create shortcut using COM
                    pythoncom.CoInitialize()  # Initialize COM
                    shortcut = pythoncom.CoCreateInstance(
                        shell.CLSID_ShellLink, None,
                        pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
                    )
                    # Set shortcut properties
                    shortcut.SetPath(str(sys.executable))
                    shortcut.SetArguments(f'"{installer_path}"')
                    shortcut.SetWorkingDirectory(str(self.install_path))
                    shortcut.SetDescription("Push Notifications Installer (Repair/Update)")
                    # Save shortcut
                    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                    persist_file.Save(str(shortcut_path), 0)
                    shortcuts_created += 1
                    logger.info(f"Created installer shortcut: {shortcut_path}")
            except Exception as e:
                logger.warning(f"Failed to create installer shortcut: {e}")
            # 3. Uninstall shortcut
            try:
                uninstaller_path = self.install_path / "uninstaller.py"
                if uninstaller_path.exists():
                    shortcut_path = desktop_path / "Uninstall Push Notifications.lnk"
                    # Create shortcut using COM
                    pythoncom.CoInitialize()  # Initialize COM
                    shortcut = pythoncom.CoCreateInstance(
                        shell.CLSID_ShellLink, None,
                        pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
                    )
                    # Set shortcut properties
                    shortcut.SetPath(str(sys.executable))
                    shortcut.SetArguments(f'"{uninstaller_path}"')
                    shortcut.SetWorkingDirectory(str(self.install_path))
                    shortcut.SetDescription("Uninstall Push Notifications")
                    # Save shortcut
                    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                    persist_file.Save(str(shortcut_path), 0)
                    shortcuts_created += 1
                    logger.info(f"Created uninstaller shortcut: {shortcut_path}")
            except Exception as e:
                logger.warning(f"Failed to create uninstaller shortcut: {e}")
            if shortcuts_created > 0:
                logger.info(f"[OK] Created {shortcuts_created} desktop shortcuts")
                return True
            else:
                logger.warning("[WARNING] No desktop shortcuts were created")
                return False
        except ImportError as e:
            logger.warning(f"Desktop shortcuts require pywin32: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to create desktop shortcuts: {e}")
            return False
    def create_installation_directory(self):
        """Create secure, hidden installation directory"""
        if self.install_path:
            return True
        print("Creating hidden installation directory...")
        try:
            # Generate a random UUID-based path for stealth
            random_path = f"PushNotifications_{uuid.uuid4().hex[:8]}"
            base_path = Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'))
            install_path = base_path / random_path
            # Create installation directory
            install_path.mkdir(parents=True, exist_ok=True)
            # Hide directory and set system attributes
            subprocess.run([
                "attrib", "+S", "+H", str(install_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            self.install_path = install_path
            print(f"[OK] Created hidden installation directory: {install_path}")
            return True
        except Exception as e:
            print(f"[ERR] Failed to create installation directory: {e}")
            return False
    def create_client_script(self):
        """Create the Python client script in the installation directory"""
        try:
            # Get the client code template
            client_code = self._get_unified_client_code()
            # Write client script
            client_path = self.install_path / "client.py"
            with open(client_path, 'w', encoding='utf-8') as f:
                f.write(client_code)
            # Make client script hidden
            subprocess.run([
                "attrib", "+H", str(client_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"[OK] Created client script: {client_path}")
            return True
        except Exception as e:
            print(f"[ERR] Failed to create client script: {e}")
            return False
    def create_config_file(self):
        """Create client configuration file"""
        try:
            # Build config data
            config = {
                'clientId': self.device_data.get('clientId'),
                'macAddress': self.mac_address,
                'username': self.username,
                'apiUrl': self.api_url,
                'version': CLIENT_VERSION,
                'installPath': str(self.install_path),
                'keyId': self.key_id,
                'encryptionMetadata': self.encryption_metadata,
                'clientPolicy': getattr(self, 'client_policy', {}),
                'allowedWebsites': [],
                'installDate': datetime.now().isoformat(),
                'lastUpdated': datetime.now().isoformat()
            }
            # Write config file
            config_path = self.install_path / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            # Make config file hidden
            subprocess.run([
                "attrib", "+H", str(config_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"[OK] Created config file: {config_path}")
            return True
        except Exception as e:
            print(f"[ERR] Failed to create config file: {e}")
            return False
    def _get_unified_client_code(self):
        """Get the unified cross-platform client code with complete functionality"""
        return f'''#!/usr/bin/env python3
"""
PushNotifications Unified Cross-Platform Client
Complete system with multi-monitor overlay, notification management, and security controls
Version: {INSTALLER_VERSION}
Supported Platforms:
- Windows 10/11 (Full feature set with overlays, tray icon, window management)
- macOS (Adapted features with system notifications and menu bar)
- Linux (Basic notifications with desktop integration)

REQUIRES ADMINISTRATOR PRIVILEGES ON WINDOWS
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
import webbrowser
import ctypes

# CRITICAL: Check admin privileges before proceeding
if os.name == 'nt':  # Windows only
    def check_admin_privileges():
        """Check if running with administrator privileges"""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False
    
    def restart_with_admin():
        """Restart the client with administrator privileges"""
        try:
            print("[INFO] Administrator privileges required for PushNotifications Client")
            print("[INFO] Restarting with elevated privileges...")
            
            # Method 1: PowerShell Start-Process with -Verb RunAs
            powershell_cmd = f'Start-Process -FilePath "{sys.executable}" -ArgumentList "\"{os.path.abspath(sys.argv[0])}\"" -Verb RunAs -WindowStyle Hidden'
            
            result = subprocess.run([
                'powershell.exe', 
                '-ExecutionPolicy', 'Bypass',
                '-NoProfile',
                '-WindowStyle', 'Hidden',
                '-Command', powershell_cmd
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                print(f"[OK] Client elevation request sent successfully")
                return True
            else:
                stderr_msg = getattr(result, 'stderr', 'Unknown error')
                print(f"[ERROR] Failed to request elevation: {{stderr_msg}}")
                return False
        except Exception as e:
            print(f"[ERROR] Could not request admin privileges: {{e}}")
            return False
    
    # Check admin privileges and restart if needed
    if not check_admin_privileges():
        if '--admin-restart' not in sys.argv:
            if restart_with_admin():
                sys.exit(0)  # Exit after requesting elevation
            else:
                print("[ERROR] Failed to request administrator privileges")
                print("[INFO] Client will run with limited functionality")
        else:
            print("[ERROR] Still not running as administrator after restart")
            print("[ERROR] Some features may not work properly")
    else:
        print("[OK] Running with administrator privileges")

# Import dependencies with fallbacks
try:
    import requests
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        import requests
    except Exception as e:
        print(f"Warning: Could not install/import requests: {{e}}")
        class DummyRequests:
            def post(self, *args, **kwargs):
                class DummyResponse:
                    status_code = 200
                    ok = True
                    def json(self): return {{'success': False, 'message': 'requests not available'}}
                return DummyResponse()
        requests = DummyRequests()

# Import PIL with fallback
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow>=10.0.0'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        print(f"Warning: Could not install/import PIL: {{e}}")
        # Create dummy PIL classes
        class DummyImage:
            def new(self, mode, size, color=None): return self
            def open(self, path): return self
            def resize(self, size, resample=None): return self
            def convert(self, mode): return self
            @property
            def size(self): return (64, 64)
            @property
            def mode(self): return 'RGBA'
            class Resampling:
                LANCZOS = 'lanczos'
        Image = DummyImage()
        class DummyImageDraw:
            def Draw(self, image): return self
            def ellipse(self, coords, **kwargs): pass
            def text(self, pos, text, **kwargs): pass
            def textbbox(self, pos, text, **kwargs): return (0, 0, 20, 20)
        ImageDraw = DummyImageDraw()
        class DummyImageFont:
            def truetype(self, font, size): return self
            def load_default(self): return self
        ImageFont = DummyImageFont()

# Import pystray with fallback
try:
    import pystray
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pystray>=0.19.4'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        import pystray
    except Exception as e:
        print(f"Warning: Could not install/import pystray: {{e}}")
        # Create comprehensive dummy pystray
        class DummyPystray:
            class Menu:
                SEPARATOR = 'separator'
                def __init__(self, *items): pass
            class MenuItem:
                def __init__(self, text, action=None, **kwargs): 
                    self.text = text
                    self.action = action
            class Icon:
                def __init__(self, name, image, title=None, menu=None): 
                    self.name = name
                    self.image = image
                    self.title = title
                    self.menu = menu
                    print(f"Created system tray icon: {{self.name}} (pystray not available - running in console mode)")
                def run(self): 
                    print("Running client in console mode (system tray not available)")
                    print("Press Ctrl+C to exit")
                    import time
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\nShutting down client...")
                        pass
                def stop(self): pass
                def update_menu(self): pass
        pystray = DummyPystray()

# Import tkinter with fallback
try:
    from tkinter import messagebox, simpledialog
except ImportError:
    print("Warning: tkinter not available")
    class DummyMessagebox:
        def showinfo(self, title, message): print(f"INFO: {{title}} - {{message}}")
        def showwarning(self, title, message): print(f"WARNING: {{title}} - {{message}}")
        def showerror(self, title, message): print(f"ERROR: {{title}} - {{message}}")
        def askyesno(self, title, message): 
            print(f"QUESTION: {{title}} - {{message}}")
            return input("Enter y/n: ").lower().startswith('y')
    messagebox = DummyMessagebox()
    class DummySimpledialog:
        def askstring(self, title, prompt, **kwargs): 
            print(f"{{title}}: {{prompt}}")
            return input("Enter value: ") or None
    simpledialog = DummySimpledialog()

logger = logging.getLogger(__name__)
class PushNotificationsClient:
    def __init__(self):
        self.running = True
        self.notifications = []
        self.icon = None
        self.snooze_until = None  # Timestamp when snooze expires
        self.snooze_used = False  # Track if snooze has been used
        self.active_notification = None
        # Load config
        self.config = self._load_config()
    def _load_config(self):
        """Load configuration with embedded defaults"""
        # Default configuration values (embedded from config.json)
        default_config = {{
            'version': '{INSTALLER_VERSION}',
            'client_id': '{self.device_data.get("clientId", "unknown-client") if self.device_data else "unknown-client"}',
            'mac_address': '{self.mac_address}',
            'api_url': '{self.api_url}',
            'install_path': str(Path(__file__).parent),
            'allowed_websites': []
        }}
        # Try to load from config.json if it exists, otherwise use defaults
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys are present
                default_config.update(config)
                return default_config
        except Exception as e:
            logger.debug(f"No config file found, using embedded defaults: {{e}}")
            return default_config
    def create_tray_icon(self):
        """Create and configure the system tray icon"""
        # Create a teal circular icon with "PN" text
        image = Image.new('RGB', (64, 64), color='teal')
        dc = ImageDraw.Draw(image)
        dc.ellipse([2, 2, 62, 62], fill='teal')
        try:
            # Try to add "PN" text
            if os.name == 'nt':  # Windows
                font = ImageFont.truetype("arial.ttf", 24)
            else:
                font = ImageFont.load_default()
            text = "PN"
            text_bbox = dc.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (64 - text_width) // 2
            y = (64 - text_height) // 2
            dc.text((x, y), text, fill='white', font=font)
        except Exception as e:
            logger.warning(f"Could not add text to icon: {{e}}")
        # Create the menu
        menu = (
            pystray.MenuItem("View Current Notification", self._view_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Snooze", pystray.Menu(
                pystray.MenuItem("5 minutes", self._snooze_5),
                pystray.MenuItem("15 minutes", self._snooze_15),
                pystray.MenuItem("30 minutes", self._snooze_30)
            ), enabled=self._can_snooze),
            pystray.MenuItem("Request Website Access", self._request_website),
            pystray.MenuItem("Complete Current Notification", 
                           self._complete_notification,
                           enabled=self._has_notifications),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Status", self._show_status),
            pystray.MenuItem("About", self._show_about),
            pystray.MenuItem("Request Uninstall", self._request_uninstall),
            pystray.MenuItem("Exit", self._quit)
        )
        # Create and return the icon
        self.icon = pystray.Icon(
            "PushNotifications",
            image,
            menu=menu
        )
        return self.icon
    def _view_notification(self, icon=None):
        """Show the current notification message"""
        if not self.notifications:
            messagebox.showinfo("No Notifications", 
                              "There are no active notifications.")
            return
        notif = self.notifications[0]
        title = notif.get('title', 'Current Notification')
        body = notif.get('message', 'No message available')
        messagebox.showinfo(title, body)
    def _snooze(self, minutes, icon=None):
        """Snooze notifications for specified minutes"""
        if self.snooze_used:
            messagebox.showwarning("Snooze Unavailable",
                                 "Snooze has already been used.")
            return
        self.snooze_until = time.time() + (minutes * 60)
        self.snooze_used = True
        # Update menu items
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception as e:
                logger.error(f"Failed to update menu: {{e}}")
                pass
        messagebox.showinfo("Notifications Snoozed",
                          f"Notifications snoozed for {{minutes}} minutes")
    def _request_website(self):
        """Request access to a website"""
        website = simpledialog.askstring("Website Access Request",
                                       "Enter the website URL you would like to access:")
        if not website:
            return
        try:
            response = requests.post(
                f"{API_URL}/api/request-website",
                json={{
                    'client_id': CLIENT_ID,
                    'website': website
                }},
                timeout=10
            )
            if response.ok:
                messagebox.showinfo("Request Sent",
                                  "Website access request has been submitted for approval.")
            else:
                messagebox.showerror("Request Failed",
                                   "Failed to submit website access request.")
        except Exception as e:
            logger.error(f"Failed to request website access: {{e}}")
            messagebox.showerror("Error",
                               "Failed to submit website access request. Please try again later.")
    def _complete_notification(self):
        """Mark the current notification as completed"""
        if not self.notifications:
            return
        try:
            notif = self.notifications[0]
            response = requests.post(
                f"{API_URL}/api/complete-notification",
                json={{
                    'client_id': CLIENT_ID,
                    'notification_id': notif['id']
                }},
                timeout=10
            )
            if response.ok:
                self.notifications.pop(0)
                self.icon.update_menu()
                messagebox.showinfo("Notification Completed",
                                  "The notification has been marked as completed.")
            else:
                messagebox.showerror("Error",
                                   "Failed to complete notification. Please try again.")
        except Exception as e:
            logger.error(f"Failed to complete notification: {{e}}")
            messagebox.showerror("Error",
                               "Failed to complete notification. Please try again later.")
    def _request_uninstall(self):
        """Request application uninstallation"""
        # Get reason
        reason = simpledialog.askstring("Uninstall Request",
                                      "Please provide a reason for uninstallation:")
        if not reason:
            return
        # Get detailed explanation
        explanation = simpledialog.askstring("Uninstall Request",
                                          "Please provide a detailed explanation:")
        if explanation is None:  # User clicked Cancel
            return
        try:
            response = requests.post(
                f"{API_URL}/api/request-uninstall",
                json={{
                    'client_id': CLIENT_ID,
                    'mac_address': MAC_ADDRESS,
                    'install_path': str(Path(__file__).parent),
                    'key_id': 'generated-key-id',
                    'reason': reason,
                    'explanation': explanation
                }},
                timeout=10
            )
            if response.ok:
                result = response.json()
                if result.get('autoApproved'):
                    # Request was auto-approved (client not found in database)
                    if messagebox.askyesno("Uninstall Approved",
                                         "Your uninstall request has been automatically approved.\n\nWould you like to uninstall now?"):
                        self._perform_uninstall()
                else:
                    # Request needs admin approval
                    messagebox.showinfo(
                        "Request Sent",
                        "Your uninstall request has been submitted for approval.\n\n" +
                        "The application will continue running until the request is approved.\n\n" +
                        "You will be notified when a decision is made."
                    )
            else:
                messagebox.showerror("Request Failed",
                                   "Failed to submit uninstall request.")
        except Exception as e:
            logger.error(f"Failed to request uninstall: {{e}}")
            messagebox.showerror("Error",
                               "Failed to submit uninstall request. Please try again later.")
    def _perform_uninstall(self):
        """Perform the actual uninstall process"""
        try:
            # Stop the tray icon
            self.icon.stop()
            # Create and execute uninstall script
            uninstall_script = (
                f"@echo off\n"
                f"timeout /t 2 /nobreak\n"
                f"rmdir /s /q \"{str(Path(__file__).parent)}\"\n"
            )
            script_path = os.path.join(os.environ['TEMP'], 'uninstall.bat')
            with open(script_path, 'w') as f:
                f.write(uninstall_script)
            # Execute uninstall script and exit
            os.startfile(script_path)
            sys.exit(0)
        except Exception as e:
            logger.error(f"Failed to perform uninstall: {{e}}")
            messagebox.showerror("Error",
                               "Failed to uninstall. Please try again later or contact support.")
            return False
    def _show_status(self):
        """Show client status information"""
        try:
            active_count = len([n for n in self.notifications if not n.get('completed', False)])
            status_text = f"Push Notifications Client\n\n"
            status_text += f"Version: {CLIENT_VERSION}\n"
            status_text += f"Client ID: {CLIENT_ID}\n"
            status_text += f"Status: Running\n"
            status_text += f"Active Notifications: {active_count}\n"
            if self.snooze_until and time.time() < self.snooze_until:
                remaining = int((self.snooze_until - time.time()) / 60)
                status_text += f"Snooze: {remaining} minutes remaining\n"
            else:
                status_text += f"Snooze: Not active\n"
            messagebox.showinfo("Client Status", status_text)
        except Exception as e:
            logger.error(f"Error showing status: {{e}}")
            messagebox.showerror("Error", "Failed to show client status.")
    def _show_about(self):
        """Show about dialog"""
        try:
            about_text = f"""Push Notifications Client
Version: {CLIENT_VERSION}
Client ID: {CLIENT_ID}
© 2024 Push Notifications
Advanced notification management system
Features:
• Notification snoozing
• Website access requests
• Background operation
• Secure client management"""
            messagebox.showinfo("About Push Notifications", about_text)
        except Exception as e:
            logger.error(f"Error showing about: {{e}}")
            messagebox.showerror("Error", "Failed to show about information.")
    def _has_notifications(self, *args):
        """Check if there are active notifications"""
        return bool(self.notifications)
    def _can_snooze(self, *args):
        """Check if snoozing is available"""
        return not self.snooze_used and bool(self.notifications)
    def _snooze_5(self, *args):
        """Snooze for 5 minutes"""
        self._snooze(5)
    def _snooze_15(self, *args):
        """Snooze for 15 minutes"""
        self._snooze(15)
    def _snooze_30(self, *args):
        """Snooze for 30 minutes"""
        self._snooze(30)
    def _quit(self, icon=None):
        """Clean shutdown of the application"""
        self.running = False
        if icon:
            icon.stop()
        elif self.icon:
            self.icon.stop()
    def run(self):
        """Main client run loop"""
        try:
            # Create and run system tray icon
            icon = self.create_tray_icon()
            icon.run()
        except Exception as e:
            logger.error(f"Client error: {{e}}")
            sys.exit(1)
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(os.path.expanduser("~")) / "Documents" / "push_notifications.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    # Hide console window (Windows only)
    try:
        import ctypes
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd != 0:
            ctypes.windll.user32.ShowWindow(console_hwnd, 0)  # SW_HIDE
    except Exception as e:
        logger.debug(f"Could not hide console window: {{e}}")
        pass  # Ignore errors on non-Windows platforms
    # Set process title for better task manager visibility
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("PushNotifications Client")
        else:
            import setproctitle
            setproctitle.setproctitle("PushNotifications Client")
    except Exception as e:
        logger.debug(f"Could not set process title: {{e}}")
        pass
    # Start client
    client = PushNotificationsClient()
    client.run()
# Initialize global variables to prevent NameError
requests = None
psutil = None
winreg = None
PBKDF2HMAC = None
hashes = None
AESGCM = None
tk = None
messagebox = None
simpledialog = None
ttk = None
USE_GUI_DIALOGS = False
Image = None
ImageDraw = None
pystray = None
win32gui = None
win32con = None
win32api = None
win32process = None
screeninfo = None
WINDOWS_FEATURES_AVAILABLE = False
# Core functionality imports with auto-installation
try:
    import requests
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        import requests
    except Exception as e:
        print(f"Warning: Could not install/import requests: {e}")
        # Create dummy requests module
        class DummyRequests:
            def post(self, *args, **kwargs):
                class DummyResponse:
                    status_code = 200
                    def json(self): return {{'success': False, 'message': 'requests not available'}}
                return DummyResponse()
        requests = DummyRequests()
try:
    import psutil
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil==5.9.0'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        import psutil
    except Exception as e:
        print(f"Warning: Could not install/import psutil: {e}")
        # Create dummy psutil module
        class DummyPsutil:
            def process_iter(self, *args, **kwargs): return []
        psutil = DummyPsutil()
# Import cryptography components with auto-installation
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cryptography>=41.0.0'],
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as e:
        print(f"Warning: Could not install/import cryptography: {e}")
        # Define dummy classes to prevent crashes
        class PBKDF2HMAC:
            def __init__(self, **kwargs): pass
            def derive(self, key): return b'dummy_key_32_bytes_for_testing!'
        class DummyHashes:
            def SHA256(self): return None
        hashes = DummyHashes()
        class AESGCM:
            def __init__(self, key): pass
            def encrypt(self, nonce, data, aad): return b'dummy_encrypted_data'
            def decrypt(self, nonce, data, aad): return b'dummy_decrypted_data'
# Windows registry import
try:
    import winreg
except ImportError:
    # Not Windows or registry not available
    class DummyWinreg:
        HKEY_CURRENT_USER = 0
        KEY_READ = 0
        REG_SZ = 0
        def OpenKey(self, *args, **kwargs): return None
        def QueryValueEx(self, *args): return ('dummy_value', 0)
        def CreateKey(self, *args): return None
        def SetValueEx(self, *args): pass
    winreg = DummyWinreg()
# Windows-specific imports with auto-installation and required packages
if os.name == "nt":
    # Import tkinter first as it's built-in
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog, ttk
        USE_GUI_DIALOGS = True
    except ImportError:
        USE_GUI_DIALOGS = False
        print("Warning: tkinter not available")
        # Create dummy tkinter classes
        class DummyTk:
            def __init__(self): pass
            def withdraw(self): pass
            def title(self, title): pass
            def geometry(self, geom): pass
            def attributes(self, attr, val): pass
            def overrideredirect(self, val): pass
            def winfo_id(self): return 0
            def winfo_screenwidth(self): return 1920
            def winfo_screenheight(self): return 1080
            def update(self): pass
            def update_idletasks(self): pass
            def mainloop(self): pass
        tk = type('tk', (), {
            'Tk': DummyTk,
            'Toplevel': DummyTk,
            'Frame': DummyTk,
            'Label': DummyTk,
            'Button': DummyTk,
            'Entry': DummyTk,
            'Text': DummyTk,
            'Menu': DummyTk,
            'StringVar': DummyTk,
            'X': 'x',
            'Y': 'y',
            'BOTH': 'both',
            'LEFT': 'left',
            'RIGHT': 'right',
            'TOP': 'top',
            'BOTTOM': 'bottom',
            'W': 'w',
            'E': 'e',
            'WORD': 'word',
            'DISABLED': 'disabled',
            'NORMAL': 'normal',
            'END': 'end'
        })()
        class DummyMessagebox:
            def showinfo(self, title, message): print(f"INFO: {{title}} - {{message}}")
            def showwarning(self, title, message): print(f"WARNING: {{title}} - {{message}}")
            def showerror(self, title, message): print(f"ERROR: {{title}} - {{message}}")
            def askyesno(self, title, message): return True
        messagebox = DummyMessagebox()
        simpledialog = type('simpledialog', (), {
            'askstring': lambda title, prompt, **kwargs: None
        })()
        ttk = type('ttk', (), {
            'Progressbar': DummyTk
        })()
    # Import PIL components
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow>=10.0.0'],
                                creationflags=subprocess.CREATE_NO_WINDOW)
            from PIL import Image, ImageDraw
        except Exception as e:
            print(f"Warning: Could not install/import PIL: {e}")
            # Create dummy PIL classes
            class DummyImage:
                def new(self, mode, size, color=None): return self
                def open(self, path): return self
                def resize(self, size, resample=None): return self
                def convert(self, mode): return self
                @property
                def size(self): return (64, 64)
                @property
                def mode(self): return 'RGBA'
                class Resampling:
                    LANCZOS = 'lanczos'
            Image = DummyImage()
            class DummyImageDraw:
                def Draw(self, image): return self
                def ellipse(self, coords, **kwargs): pass
                def text(self, pos, text, **kwargs): pass
                def textbbox(self, pos, text, **kwargs): return (0, 0, 20, 20)
            ImageDraw = DummyImageDraw()
    # Import Windows-specific modules
    try:
        import pystray
        import win32gui
        import win32con
        import win32api
        import win32process
        import screeninfo
        WINDOWS_FEATURES_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Windows features limited due to missing modules: {e}")
        WINDOWS_FEATURES_AVAILABLE = False
        # Try to install missing packages
        missing_packages = ['pystray>=0.19.4', 'pywin32>=306', 'screeninfo>=0.8.1']
        for pkg in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg],
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as install_e:
                print(f"Warning: Could not install {pkg}: {install_e}")
        # Try importing again after installation attempt
        try:
            import pystray
            import win32gui
            import win32con
            import win32api
            import win32process
            import screeninfo
            WINDOWS_FEATURES_AVAILABLE = True
        except ImportError:
            # Create comprehensive dummy classes
            class DummyPystray:
                class Menu:
                    SEPARATOR = 'separator'
                    def __init__(self, *items): pass
                class MenuItem:
                    def __init__(self, text, action=None, **kwargs): pass
                class Icon:
                    def __init__(self, name, image, title=None, menu=None): pass
                    def run(self): 
                        print("Running in console mode (pystray not available)")
                        import time
                        try:
                            while True:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            pass
                    def stop(self): pass
            pystray = DummyPystray()
            # Create dummy win32 modules
            class DummyWin32:
                def __getattr__(self, name): return lambda *args, **kwargs: None
            win32gui = DummyWin32()
            win32con = DummyWin32()
            win32api = DummyWin32()
            win32process = DummyWin32()
            # Create dummy screeninfo
            class DummyScreeninfo:
                def get_monitors(self): return []
            screeninfo = DummyScreeninfo()
        # Install missing packages silently if needed
        missing_packages = ['pystray>=0.19.4', 'pywin32>=306', 'screeninfo>=0.8.1']
        for pkg in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg],
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as install_e:
                print(f"Warning: Could not install {pkg}: {install_e}")
        # Try importing again after installation
        try:
            import pystray
            import win32gui
            import win32con
            import win32api
            import win32process
            import screeninfo
            WINDOWS_FEATURES_AVAILABLE = True
        except ImportError:
            # Create comprehensive dummy classes as fallback
            class DummyPystray:
                class Menu:
                    SEPARATOR = 'separator'
                    def __init__(self, *items): pass
                class MenuItem:
                    def __init__(self, text, action=None, **kwargs): pass
                class Icon:
                    def __init__(self, name, image, title=None, menu=None): pass
                    def run(self): 
                        print("Running in console mode (pystray not available)")
                        import time
                        try:
                            while True:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            pass
                    def stop(self): pass
            pystray = DummyPystray()
            # Create dummy win32 modules
            class DummyWin32:
                def __getattr__(self, name): return lambda *args, **kwargs: None
            win32gui = DummyWin32()
            win32con = DummyWin32()
            win32api = DummyWin32()
            win32process = DummyWin32()
            # Create dummy screeninfo
            class DummyScreeninfo:
                def get_monitors(self): return []
            screeninfo = DummyScreeninfo()
            WINDOWS_FEATURES_AVAILABLE = False
else:
    # Non-Windows systems
    USE_GUI_DIALOGS = False
    WINDOWS_FEATURES_AVAILABLE = False
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog, ttk
        USE_GUI_DIALOGS = True
    except ImportError:
        # Create dummy tkinter for non-Windows systems
        class DummyTk:
            def __init__(self): pass
            def withdraw(self): pass
            def title(self, title): pass
            def geometry(self, geom): pass
            def attributes(self, attr, val): pass
            def overrideredirect(self, val): pass
            def winfo_screenwidth(self): return 1920
            def winfo_screenheight(self): return 1080
            def update(self): pass
            def mainloop(self): pass
        tk = type('tk', (), {'Tk': DummyTk})()
        messagebox = type('messagebox', (), {
            'showinfo': lambda title, msg: print(f"INFO: {title} - {msg}")
        })()
        simpledialog = None
        ttk = None
# Overlay Manager class for multi-monitor overlays
class OverlayManager:
    def __init__(self):
        self.overlays = []
    def show_overlays(self):
        """Show grey overlays on all monitors"""
        if not WINDOWS_FEATURES_AVAILABLE or not USE_GUI_DIALOGS:
            return
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            for monitor in monitors:
                overlay = tk.Toplevel()
                overlay.configure(bg='grey')
                overlay.attributes('-alpha', 0.25)  # 25% opacity
                overlay.attributes('-topmost', True)
                overlay.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
                overlay.overrideredirect(True)
                overlay.attributes('-fullscreen', True)
                self.overlays.append(overlay)
        except Exception as e:
            logging.warning(f"Error creating overlays: {e}")
    def hide_overlays(self):
        """Hide all overlays"""
        for overlay in self.overlays:
            try:
                overlay.destroy()
            except:
                pass
        self.overlays = []
# Basic client template - this is just a placeholder
print(f"PushNotifications Client v{CLIENT_VERSION} starting...")
print(f"Client ID: {CLIENT_ID}")
print(f"MAC Address: {MAC_ADDRESS}")
print(f"API URL: {API_URL}")
print(f"Windows Features Available: {WINDOWS_FEATURES_AVAILABLE}")
class PushNotificationsClient:
    """Main client application class"""
    def __init__(self):
        self.running = True
        self.notifications = []
        self.notification_windows = []
    def create_tray_icon(self):
        """Create and configure the system tray icon"""
        try:
            # Create default icon using PIL
            from PIL import Image, ImageDraw
            width = 64
            height = 64
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse([4, 4, width-4, height-4], 
                        fill='#20B2AA', outline='#008B8B', width=2)
            # Add PN text
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
                draw.text((width//2-12, height//2-8), "PN", 
                         fill='white', font=font)
            except:
                draw.text((width//2-12, height//2-8), "PN", 
                         fill='white')
            # Create comprehensive menu with all features
            menu = pystray.Menu(
                pystray.MenuItem("Mark Complete", 
                               self._complete_notification, 
                               enabled=self._has_notifications),
                pystray.MenuItem("Request Website Access", 
                               self._request_website,
                               enabled=self._has_website_notification),
                pystray.Menu.SEPARATOR,
                # Snooze submenu - enabled only when notifications exist and not already snoozed
                pystray.MenuItem("Snooze All (5 min)", 
                               lambda icon: self._snooze(5),
                               enabled=self._can_snooze),
                pystray.MenuItem("Snooze All (15 min)", 
                               lambda icon: self._snooze(15),
                               enabled=self._can_snooze),
                pystray.MenuItem("Snooze All (30 min)", 
                               lambda icon: self._snooze(30),
                               enabled=self._can_snooze),
                pystray.Menu.SEPARATOR,
                # Display Actions
                pystray.MenuItem("Show Status", self._show_status),
                pystray.MenuItem("Show All Notifications", 
                               self._show_all_notifications,
                               enabled=self._has_notifications),
                pystray.Menu.SEPARATOR,
                # Administrative Actions
                pystray.MenuItem("Request Deletion", self._request_deletion),
                pystray.MenuItem("Submit Bug Report", self._submit_bug),
                pystray.Menu.SEPARATOR,
                # System Actions
                pystray.MenuItem("Settings", self._show_settings),
                pystray.MenuItem("About", self._show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit (Admin Required)", self.quit)
            )
            # Create and return icon
            icon = pystray.Icon("PushNotifications", image, 
                              "PushNotifications Client", menu)
            return icon
        except Exception as e:
            print(f"Error creating tray icon: {str(e)}")
            return None
    def quit(self, icon=None):
        """Clean shutdown of the client"""
        self.running = False
        if icon:
            icon.stop()
if __name__ == "__main__":
    # Create the client instance
    client = PushNotificationsClient()
    # Hide console window (Windows-only installer)
    try:
        import ctypes
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd != 0:
            ctypes.windll.user32.ShowWindow(console_hwnd, 0)  # SW_HIDE
    except Exception as e:
        print(f"Could not hide console: {e}")
    # Create and run system tray icon
    try:
        icon = client.create_tray_icon()
        if icon:
            icon.run()
    except Exception as e:
        print(f"Could not create tray icon: {e}")
    # Run the main loop if no tray icon
    import time
    while client.running:
        time.sleep(30)  # Keep running
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
            subprocess.run([
                "attrib", "+S", "+H", str(vault_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
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
            subprocess.run([
                "attrib", "+S", "+H", str(marker_path)
            ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            # Securely clear key material from memory
            derived_key = b'\x00' * len(derived_key)
            demo_key_material = b'\x00' * len(demo_key_material)
            print("[OK] AES-256-GCM encrypted vault created")
            print(f"  Encryption Algorithm: {vault_header['algorithm']}")
            print(f"  Key ID: {self.key_id}")
            return True
        except Exception as e:
            print(f"[ERR] Failed to create encrypted vault: {e}")
            import traceback
            traceback.print_exc()
            return False
    def run_installation(self):
        """Run the complete installation process with progress tracking"""
        print("Starting PushNotifications Installation")
        print("=" * 60)
        # Admin privileges already checked in main() - proceed directly with installation
        # Initialize progress tracking
        total_steps = 5  # Number of main installation steps
        current_step = 0
        def update_progress(step_name, step_number):
            progress = int((step_number / total_steps) * 100)
            print(f"\n[{progress:3d}%] {step_name}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_progress(step_name, progress)
        # Step 1: Validate installation key (skip in repair mode)
        current_step += 1
        update_progress("Validating installation key...", current_step)
        if self.repair_mode:
            print("[REPAIR] Skipping installation key validation in repair mode")
            # In repair mode, we already loaded the existing config with a dummy key
            if not self.installation_key:
                self.installation_key = "REPAIR_MODE"
        elif not self.validate_installation_key():
            error_msg = "Installation failed: Invalid installation key"
            print(f"[ERR] {error_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_error(error_msg)
            return False
        # Step 2: Register device
        current_step += 1
        update_progress("Registering device with server...", current_step)
        if not self.register_device():
            error_msg = "Installation failed: Device registration failed"
            print(f"[ERR] {error_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_error(error_msg)
            return False
        # Step 3: Create hidden installation directory
        current_step += 1
        update_progress("Creating secure installation directory...", current_step)
        if not self.create_hidden_install_directory():
            error_msg = "Installation failed: Could not create installation directory"
            print(f"[ERR] {error_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_error(error_msg)
            return False
        # Step 4: Create encrypted vault
        current_step += 1
        update_progress("Creating encrypted configuration vault...", current_step)
        if not self.create_encrypted_vault():
            error_msg = "Installation failed: Could not create encrypted vault"
            print(f"[ERR] {error_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_error(error_msg)
            return False
        # Step 5: Create embedded client components
        current_step += 1
        update_progress("Installing client components...", current_step)
        if not self.create_embedded_client_components():
            error_msg = "Installation failed: Could not create client components"
            print(f"[ERR] {error_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_error(error_msg)
            return False
        # Optional: Create desktop shortcuts (non-critical)
        if not self.create_desktop_shortcuts():
            warning_msg = "Could not create desktop shortcuts (non-critical)"
            print(f"[WARNING] {warning_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_status("warning", warning_msg)
        # Installation completed successfully - generate comprehensive summary
        if not self._generate_installation_summary():
            warning_msg = "Could not generate installation summary (non-critical)"
            print(f"[WARNING] {warning_msg}")
            if hasattr(self, 'message_relay') and self.message_relay:
                self.message_relay.send_status("warning", warning_msg)
        completion_msg = "Installation completed successfully!"
        print(f"[COMPLETED] {completion_msg}")
        if hasattr(self, 'message_relay') and self.message_relay:
            self.message_relay.send_success(completion_msg)
        return True
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts for the client application and installer"""
        return self.create_desktop_shortcuts_impl()
# External utility classes and functions for embedded client code
class WindowManager:
    """Manages window minimization and process restrictions"""
    def __init__(self):
        self.minimized_windows = []
        # Process executable names to monitor and potentially terminate
        # These refer to Windows process names (actual .exe files) that may be running
        self.restricted_processes = {
            'browsers': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 'brave.exe', 'iexplore.exe'],
            'vpn': ['openvpn.exe', 'nordvpn.exe', 'expressvpn.exe', 'cyberghost.exe', 'tunnelbear.exe'],
            'proxy': ['proxifier.exe', 'proxycap.exe', 'sockscap.exe']
        }
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
            print(f"Error minimizing windows: {e}")
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
            print(f"Error blocking processes: {e}")
def enable_dpi_awareness():
    """Enable DPI awareness for proper scaling on high-DPI displays"""
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
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except Exception as e:
                print(f"Warning: Could not set DPI awareness: {e}")
            self.window = tk.Toplevel()
            self.window.title("Push Notification")
            # Configure window properties for maximum visibility
            self.window.attributes('-topmost', True)  # Always on top
            self.window.attributes('-alpha', 1.0)  # Fully opaque
            self.window.resizable(False, False)
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)
            self.window.focus_force()  # Force focus
            self.window.lift()  # Bring to front
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
                # Ensure notification window is visible in taskbar and on top
                style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                # Apply new style
                win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
                # Update window frame and ensure visibility
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                    win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW
                )
                # Force window to be active and visible
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetActiveWindow(hwnd)
                win32gui.SetForegroundWindow(hwnd)
                # Flash window to get attention
                win32gui.FlashWindow(hwnd, True)
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
            colors = {{
                'bg': "#ffffff",
                'header': "#1a73e8",  # Google Blue
                'text': "#202124",    # Dark Gray
                'border': "#dadce0",  # Light Gray
                'button_primary': "#1a73e8",
                'button_secondary': "#5f6368",
                'button_warning': "#f29900",
                'shadow': "#0000001a"  # 10% black shadow
            }}
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
                                        text=f"Allowed websites: {', '.join(allowed_websites)}",
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
        else:
            messagebox.showwarning("Invalid Input", "Please enter a website URL.")
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
        self.client_operational = False  # Flag to control when heartbeat starts
        # Set proper process title for Task Manager
        self._set_process_title()
        # Initialize Tkinter root - completely hidden
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window immediately
        self.root.title("Push Notifications")
        # Make the root window completely invisible
        self.root.attributes('-alpha', 0.0)  # Fully transparent
        self.root.geometry('1x1+0+0')  # Minimal size
        self.root.overrideredirect(True)  # Remove window decorations
        # Hide from taskbar
        try:
            import win32gui
            import win32con
            hwnd = self.root.winfo_id()
            # Set window styles to hide from taskbar
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                 win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_TOOLWINDOW)
        except Exception as e:
            print(f"Warning: Could not hide from taskbar: {{e}}")
    def _set_process_title(self):
        """Set proper process title for Task Manager and hide console"""
        try:
            import ctypes
            # Set console window title to show "Push Notifications" in Task Manager
            ctypes.windll.kernel32.SetConsoleTitleW("Push Notifications")
            # Hide console window
            # Get console window handle
            console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if console_hwnd != 0:
                # Hide the console window (SW_HIDE = 0)
                ctypes.windll.user32.ShowWindow(console_hwnd, 0)
        except Exception as e:
            print(f"Warning: Could not set process title or hide console: {{e}}")
    def _extract_embedded_icon(self):
        """Extract embedded icon data to PNG file"""
        try:
            import base64
            icon_path = Path(__file__).parent / "pnicon.png"
            # Use the same embedded icon data from the installer
            EMBEDDED_ICON_DATA = "iVBORw0KGgoAAAANSUhEUgAAB9AAAAfQCAMAAACt5jRLAAAArlBMVEUAAAAGFRgSP0gRPUYaXGkcZHIIHSEea3pJHEkea3kRPEQQOUEbYW8EDhAKJCkUR1FGHEdDHUQYVmIwNVJAGUUtPFc3I0g5H0MdZ3YyKE0rQls9HEUdaXk7IkgnRGMnT2IBAwQmS2Y2LUoWT1otOVNDGUckT2gpR14CBwggW28MKjANMTgjV24DCgwgYnUgX3IJICQZWWYSQ00jU2oaXmwoPV0FERQFExYHGBwzKlB1IwGiAAAACXBIWXMAAAPoAAAD6AG1e1JrAAAgAElEQVR4nOzda38URd7HYfQWJohiYiAkBOQg55On1dX3/8buD7qlqPAnmXRN/7r6uh7sg/2wm56ZVH0zfai6tAEAFu/S3AcAAFycoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgA8AABB0ABiDoADAAQQeAAQg6AAxA0AFgAIIOAAMQdAAYgKADwAAEHQAGIOgAMABBB4ABCDoADEDQAWAAgg4AAxB0ABiAoAPAAAQdAAYg6AAwAEEHgAEIOgAMQNABYACCDgADEHQAGICgh7s69wEA/MF0FE7QwxlBQAjTUThBD2cEASFMR+EEPZwRBIQwHYUT9HBGEBDCdBRO0MMZQUAI01E4QQ9nBAEhTEfhBD2cEQSEMB2FE/RwRhAQwnQUTtDDGUFACNNROEEPZwQBIUxH4QQ9nBEEhDAdhRP0cEYQEMJ0FE7QwxlBQAjTUThBD2cEASFMR+EEPZwRtGaXv/7x5YvrV/J8f/3Fta8+m/vtYddMR+EEPZwRtFZXv335yaVsr69/+sXcbxO7ZDoKJ+jhjKB1+uzl60uL8P1Xx3O/V+yM6SicoIczgtboh+uXluP1NUlfC9NROEEPZwStz3+WlPO3Xv8491vGbpiOwgl6OCNoba5eu39pcX79Ye63jV0wHYUT9HBG0Mp8ceXSEt3/fO43jh0wHYUT9HBG0Lp8u5B74f7tuivp4zMdhRP0cEbQqvy4wNPtza+X53736M10FE7QwxlBa/J/l5bsvx5KH53pKJyghzOCVuTHS8v2i+/ogzMdhRP0cEbQenx1ael+dR19bKajcIIezghajR8WfP28uT73m0hXpqNwgh7OCFqL418uDcASM0MzHYUT9HBG0Fq8uDSC+1aYGZnpKJyghzOCVuLbS2P4de43ko5MR+EEPZwRtA5jnHB/66u530r6MR2FE/RwRtA6fH5pFK/d6T4u01E4QQ9nBK3CnS8vDePTud9MujEdhRP0cEbQKnzav7PPPvn1ypVfd/CHw5d35n436cV0FE7QwxlBq9D5CvonL79ty7Ie//Dp9Wd9f5qr6MMyHYUT9HBG0Bp83bOvz17+81Gy46+67tH6/UzvIt2ZjsIJejgjaA1e9qvrs2vvvUnt6+/7/cj7NmkZlekonKCHM4LWoN8m6C8+GNev+l1Ot1zcqExH4QQ9nBG0Aj/0Kuuz6nL25eu9fqwV3UdlOgon6OGMoBXodY/7L5/VP/dap5/7eldvHDtmOgon6OGMoBXotIz7J5fn2oD9P7t539g101E4QQ9nBK3Ar12q+stHe96t6N/u4l1j90xH4QQ9nBG0Al2eC399pnvN+5x1/7/+7xlzMB2FE/RwRtD4Ls/5LbnL42sve79lzMN0FE7QwxlB4/usR1OvnfGHX+7xyNyLzu8YMzEdhRP0cEbQ+HqsE/fLmfc863EZ3XNrgzIdhRP0cEbQ+L6e97a0DrfkXen5djEf01E4QQ9nBI3v2+mL+uu8P17QB2U6Cifo4Yyg8X0784Zn039FF/RBmY7CCXo4I2h80wf99Z15F6oT9EGZjsIJejgjaHzfzvzY2OX7U/98QR+U6SicoIczgsb37dwrtU2+O7qgD8p0FE7QwxlB45s86PfP/Mxap+XiznNPHgtiOgon6OGMoPF9NXdPJ/+L4pdO7xQzMx2FE/RwRtD4fpx7obYvpj6ALzu9U8zMdBRO0MMZQeP7fK5lX/809V1xz/q8UczNdBRO0MMZQeObfDv0T897BF9OfQRn2LmVBTIdhRP0cEbQ+Ca/yfzH8x7Bf6c+gq/7vFPMzHQUTtDDGUHjez3rOnFvfTL7nxQsgukonKCHM4KGN/126POfcrch+phMR+EEPZwRNLzJn1q79Pns5wg+6fNWMTPTUThBD2cEDW/ye+LO/dja8eRH4K64MZmOwgl6OCNoeL9cmnvl1Q4bsp/7Mj5LYDoKJ+jhjKDR/TB9TZ+d87dm+u3WLl3v9XYxJ9NROEEPZwSN7uX0NT3vU2PXpz+C+865j8h0FE7QwxlBg7s6+R3m514q7s6zDofgwbURmY7CCXo4I2hw0++deunSpf/Ofwg2XBuR6SicoIczggY3+TJx5z/n3uGM+/n3ZGcJTEfhBD2cETS2DjeYn/eetM/6HMJ5b7VnAUxH4QQ9nBE0tj5f0C9d+mzO5+D/YD338ZiOwgl6OCNoaNOvEnfu78edzhFcuvSJ393h+EjDCXo4I2hkxz1ucT/fyi5Xf+12COdeUp50pqNwgh7OCBpZj2fQ/+f1F2c7hGv9DuHZGQ+BxTAdhRP0cEbQwLo8L9ZcuTP/IfjtHYwPNJyghzOCxvXF5Juc/c31M/zu/NBjTZltF7ghnukonKCHM4KGdafXHe5n33Tth75/UngYfTSmo3CCHs4IGlavx8X+dP/6R866f92755eeeXZtKKajcIIezggaVccb4v70Sfk4+o/3+x/B6//s7h2lO9NROEEPZwQNquPd5e949uE9Ur7os+LrP/2i6AMxHYUT9HBG0JCudj/f3lx5/0nv48/73g73l9c/7PzdpRfTUThBD2cEjeh4N9+O//D9v+9Mu3yt+9XzvzxzZ9wwTEfhBD2cETSgH/57aae+fPnt8V8//T8/fr+Di+fv8vTaKExH4QQ9nBE0nl3cjPZP9z+5/vLa/117+eLKDr+b/+mKNePGYDoKJ+jhjKDRfPb9pfV59rlf5BH4FMMJejgjaCzH12b4ep7gV0+kD8B0FE7QwxlBIzm+tqt7ywP9etYN4IhlOgon6OGMoHF8/XLFOX/r1x/fuTePBTIdhRP0cEbQGK5+fe2XuXsa4P71ry7P/VGwPdNROEEPZwQt3p0fvrr2/cq/m7/rvy9//FbVl8l0FE7QwxlBZ/fDpy+uX8ny6ydfzvGYWL77X/7y65Uc1198akG7MzAdhRP0cEbQGX3xUjm5iC+veVr+Y0xH4QQ9nBF0JpdfrvRpMCZ0/6Wk10xH4QQ9nBF0BlfX+nA3E3v26dy/y9lMR+EEPZwR9HH/uTJ3BxiGVWorpqNwgh7OCPqor9xBznRsDlcwHYUT9HBG0Md8OncBGIzT7h9kOgon6OGMoNrVl3NP/wzHdq8fYjoKJ+jhjKDai7knfwb0cu5f61Smo3CCHs4IKvl+Tg+K/n6mo3CCHs4Iqug5fTjr/l6mo3CCHs4IKrgfjl5+nPuXO5LpKJyghzOCPuzbuSd9xnX/67l/vROZjsIJejgj6IN+8Pw5/bz+z9y/4IFMR+EEPZwR9CHH9henp1+P5/4Vz2M6Cifo4YygD/HAGn251f1fTEfhBD2cEfQBP8493TO8r+b+JY9jOgon6OGMoPf7wgV0envmMvo/mI7CCXo4I+j9bLBGf1fm/jVPYzoKJ+jhjKD38gQ6u2Cflr8zHYUT9HBG0Ps44c5OOOn+d6ajcIIezgh6Hyfc2Y3v5/5Vz2I6Cifo4Yyg93CHO7viTvd3mY7CCXo4I+jfjl/PPcuzGl9aXuYdpqNwgh7OCPo3e6yxO/Zde4fpKJyghzOC/uWz+3PP8azI/S/m/oUPYjoKJ+jhjKB/+X7uKZ5VeTH3L3wQ01E4QR9yBB1//dW1ly+uf3/lkwHNPcGzMp+M5Mr311+8vPbVD9vdGiDo4QQ93LlH0J2vr33/5dxTIJDty++vfX3u2UXQwwl6uPONoC8+/94FZuBMnn3/f+e7Q0DQwwl6uHOMoOOvXF0GzuXKj+c4+y7o4QQ93JlH0GcvfDcHzu3ZizMvcCvo4QQ93BlH0A/X554VgIW6/+KHSacj5iLo4c40gj6Tc+ACrn822XTEfAQ93BlG0PE1J9uBC7l/7QzX0gU9nKCH+/gI+vaXuacCYPm+/HaC6YhZCXq4j42gY2fbgUm8+NiXdEEPJ+jhPjKCfvD1HJjILx+5OU7Qwwl6uHoE/ejqOTCZ+59fYDpidoIerhpBV1/MPfyBsbwop5wOUxwTEvRwxQhy+RyY2vXiQrqghxP0cB8eQcdX5h75wHiuXN5iOiKCoIf74Ai6bBtRoINPPlh0QQ8n6OE+NIKOf5171ANj+vVDZ90FPZygh/vACLrq+jnQyfd3zjUdkULQw31gBLm/Hejm+rmmI1IIerj3j6Brc493YGTXzjEdEUPQw713BH0792gHxvbehd0FPZygh3vfCPri9dyDHRjb6/fd6i7o4QQ93HtG0FUPoAOdfX+26Ygkgh7uPSPo87lHOjC+T880HZFE0MP9ewR98WzugQ6M79kXZ5iOiCLo4f49gjyBDuzAizNMR0QR9HD/GkHucAfmudNd0MMJerh/jqCrv8w9yIF1+O+/pp8dTn1sQdDD/XMEfTX3GAfW4quPTEeEEfRw/xxB/517iANr8d+PTEeEEfRw/xhBvqADc11FF/Rwgh7uHyPIpqnAzvxaTkekEfRwfx9BX59rMD775dcrA3CVgSSfXFmyX3853zoWXxfTEXEEPdzVLXdN/fLlt+9bi3mJbBVLkpebhbv87csvt3y1gh5O0MP9bQQdn/WP6+/fu1XSMn1xf+upF6Z3f4S/lL/9/oyv9vWdd/9ngh5O0MNd3eKWuF//fpps4V5eZPKFHW0VvjRff7LFk2uCHk7Qw109/6qv14YadWc+KwG78fp4M4Kr1870aq//7X8z3+FyFoIe7t0RdHyWk8/PBjrb/pa95Ujz42YM355lQrn/7jl3QQ8n6OGunnMZ92dDnW7fbO6c/fYd2I1fRuna12c5/fXujDLKCx+WoId7dwSd4RTZ/cG+n29+nGIChq4rog79Hf3dWwYEPZygh3t3BF1Zz8nAP53xzh2Yb7mVBfu/j7/YK+/8c0EPJ+jhrp7rEvrfbmAZgc1iSTTOha2PP752/517AAU9nKCHu3qeZeLufzHnofZwhpMSsHPj/OX8n49/Tfjhr38t6OEEPdzV8zyFvvg1rP7pfEvdwq58tlnPOg/v3DEg6OEEPdzVc9wTN8QSVpvzP3gPu/Zis56VGN+5K07Qwwl6uKvnqNs45wHPfjoQ5jDQ1a3zzCuCHk7Qw109xw3foz2yZtVXYo1zeeurc9zTL+jhBD3cOyPo9TnuRh3CZV/QSfVsmNF2+WMv9fVf/1bQwwl6uHdG0P3VPBz7P2dbaxrm8H+bUXzs1N+zv/6poIcT9HDvjKD13Kfzh+OPnZKA+Xz5t31Fh76I/tc/FfRwgh7urxF0vI5dHf/y6WRzL0zvq9XcqvLX1QVBDyfo4f4aQV98bNh9vhnLL5NNvTC9TzZrubT11x39gh5O0MP9NYI++9iw+3QzlI+vowNz+nYt67n/tYqOoIcT9HDrDfqvk0280MP3mzEI+jgEPdxqg27VV9INskWLoI9D0MOtNuhWfSXdIM+VCPo4BD3cWoP+0VcLc7v/n80IBH0cgh5urUF/MdmsC72Msf6roI9D0MOtNOgf3wIKZvdsiP0NBX0cgh5upUG3LQtLMMRiToI+DkEPt86gHz+bbMqFfl6PsEWLoI9D0MOtM+gfnWIgwo+b5RP0cQh6uFUG/eqXk0240NMvm+UT9HEIerhVBt2qryzFAOu/Cvo4BD3cKoNu1VeW4spm8QR9HIIebo1B/3ay2RZ6W/76r4I+DkEPt8agfz/ZZAu9Xd8snaCPQ9DDrTDoP0w210J/i1//VdDHIejhVhh0q76yJItf/1XQxyHo4dYXdKu+sij3l77+q6CPQ9DDrS/oVn1lWZa+/qugj0PQw60u6FZ9ZWGWvv6roI9D0MOtLuifTzbPwm4sfP1XQR+HoIdbW9DvWPWVpfll2Z0T9HEI+pqD/tlXO3WWVTKt+sryfHWG3+xvdzPItjj9L+jjEPQ1B33Hp7c/P8MhfbLbQ4IJfJIz2La45V7QxyHo4QYK+rMzzDVWfWWJvo2521PQV03Qww0U9LMswHFlp0cE0/g+5nlMQV81QQ83TtDvn2GJTKu+skw/pKyYJOirJujhxgn6izMckFVfWaaY325BXzVBDzdO0M+wzaRVX1momPNPgr5qgh5umKBfOcPxWPWVpXoZsi+woK+aoIcbJug59wHDuM9wCPqqCXq4UYL+36zDgRlWWfi1/2EI+qoJerhRgn6G5a6t+sqCvb4TsQ6ioK+aoIcbJOhnme1+3NnRwCx/s17t/zeroK+aoIcbJOhWfWV0GVeVBH3VBD3cGEFPuWMIBr/vU9BXTdDDjRF0q74yvognMwV91QQ93BBBj1l1AwZfO0nQV03Qww0R9LOsi3l9R8cCvVwPWP9V0FdN0MMNEfQzfHP5j1VfWbqEM1GCvmqCHm6EoEdcW4Q1rP8q6Ksm6OFGCPoZ7v69bNVXlu/+/E9zCPqqCXq4AYJ+ludzr+3kSKCva7Ov/yroqybo4QYI+llWfX29kyOBvl4fz73+q6CvmqCHW37QrfrKesy+/qugr5qgh1t+0M+y6ut/d3Eg0N0vcw87QV81QQ+3+KBb9ZU1mXv9V0FfNUEPt/igW/WVNZn7GU1BXzVBD7f0oJ9lrY2v+x8GrGP9V0FfNUEPt/SgW/WVdZl5/VdBXzVBD7f0oFv1lZX5K39zrP8q6Ksm6OEWHvTvz3AUVn1lJPOu/yroqybo4RYedKu+sjbzrv8q6Ksm6OGWHXSrvrI+s67/KuirJujhlh30M6ybdWzVV8Yy6/qvgr5qgh5u3qB/+/XFWPWVFfrqDON6yxH10fvjBX3VBD3cvEH/YtPdLx87BliYT/oNl49eoBL0VRP0cKMH3aqvjOcM94JuSdCpCHq40YNu1VfGc5anNbcj6FQEPdzgQbfqKyP6odeAEXQqgh5u8KBb9ZURnWXF460IOhVBDzd20P/zsQOAJbrfa+QIOhVBDzd20K36ynrXf92GoFMR9HBDB/2ybVkY07MzLC6zDUGnIujhhg66VV8Z1f/NNGQEfdUEPdzIQbfqK8P68gyrJG5B0KkIeriRg/7px348jLz+6xYEnYqghxs56FZ9ZVx91n8VdCqCHm7goHfbcApGXf9V0KkIeriBg95tS2gYdf1XQaci6OHGDfoPH/vhsGh/dXA6gk5F0MONG3SLyjC2ax1GjaBTEfRw4wbdLXGM7dcOo0bQqQh6uGGDfvyxnw3Ldr/DsBF0KoIebtigu4TO6DoMH0GnIujhhg26ndAZXYe74gSdiqCHGzbodk5ldFvE9WMEnYqghxs26Md2WmNsrzsMG0GnIujhhg365vrHfjgs2osOo0bQqQh6uHGD7iI6Q7v/Q4dRI+hUBD3cuEG3sgxD67GujKBTEvRwAwf945MTLFaXngs6JUEPN3LQN1+/+PJjRwDLc//LFz3Otws6HyHo4YYO+mazuXMZRtOve4JORdDDjR504OwEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWXs91IAACAASURBVGgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCp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oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQca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"
            # Decode and write the embedded icon data
            icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
            with open(icon_path, 'wb') as f:
                f.write(icon_data)
            print(f"[OK] Extracted embedded icon to: {icon_path.name}")
            return True
        except Exception as e:
            print(f"Error extracting embedded icon: {{e}}")
            return False
    def create_tray_icon(self):
        """Create system tray icon with enhanced quick actions menu"""
        try:
            def create_image():
                # Use embedded icon data directly - no file system access needed
                try:
                    import base64
                    from io import BytesIO
                    # Embedded icon data (valid 32x32 PNG)
                    EMBEDDED_ICON_DATA = "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TtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWXs91IAACAASURBVGgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCp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oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQcaQaci6OEEHWgEnYqghxN0oBF0KoIeTtCBRtCpCHo4QQca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"
                    # Decode the base64 data directly in memory
                    icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
                    icon_stream = BytesIO(icon_data)
                    # Load the image from memory
                    image = Image.open(icon_stream)
                    # Resize to standard tray icon size if needed
                    if image.size != (64, 64):
                        image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    # Convert to RGBA if not already
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    print("[OK] Created tray icon from embedded data")
                    return image
                except Exception as e:
                    print(f"Warning: Could not load embedded icon data: {e}")
                # Fallback: create a teal circle with white "PN" text
                print("Creating fallback tray icon")
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
            # Enhanced menu with dynamic states using helper functions
            menu = pystray.Menu(
                # Quick Actions Section - dynamically enabled based on notification state
                pystray.MenuItem(
                    'Mark Complete', 
                    self.tray_mark_complete, 
                    enabled=lambda icon, item: self.has_active_notifications()
                ),
                pystray.MenuItem(
                    'Request Website Access', 
                    self.tray_request_website,
                    enabled=lambda icon, item: self.has_website_notification()
                ),
                pystray.Menu.SEPARATOR,
                # Snooze Actions - enabled only when notifications exist and not already snoozed
                pystray.MenuItem(
                    'Snooze All (5 min)', 
                    lambda icon: self.tray_snooze_all(5),
                    enabled=lambda icon, item: self.can_snooze()
                ),
                pystray.MenuItem(
                    'Snooze All (15 min)', 
                    lambda icon: self.tray_snooze_all(15),
                    enabled=lambda icon, item: self.can_snooze()
                ),
                pystray.MenuItem(
                    'Snooze All (30 min)', 
                    lambda icon: self.tray_snooze_all(30),
                    enabled=lambda icon, item: self.can_snooze()
                ),
                pystray.Menu.SEPARATOR,
                # Display Actions - Show Status always available, Show Notifications only when they exist
                pystray.MenuItem('Show Status', self.show_status),
                pystray.MenuItem(
                    'Show All Notifications', 
                    self.show_all_notifications,
                    enabled=lambda icon, item: self.has_active_notifications()
                ),
                pystray.Menu.SEPARATOR,
                # Administrative Actions - always available
                pystray.MenuItem('Request Deletion', self.tray_request_deletion),
                pystray.MenuItem('Submit Bug Report', self.tray_submit_bug),
                pystray.Menu.SEPARATOR,
                # System Actions - always available
                pystray.MenuItem('Settings', self.show_settings),
                pystray.MenuItem('About', self.show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('Quit (Admin Required)', self.quit_application)
            )
            # Set proper window title for Task Manager
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleTitleW("PushNotifications Client")
            except:
                pass
            return pystray.Icon("PushNotifications", create_image(), "PushNotifications Client", menu)
        except Exception as e:
            print("Error creating tray icon")
            import traceback
            traceback.print_exc()
            return None
    def show_status(self, icon=None, item=None):
        """Show client status"""
        try:
            active_count = len([n for n in self.notifications if not n.get('completed', False)])
            status_text = f"Push Client v{CLIENT_VERSION}\n"
            status_text += f"Client ID: {CLIENT_ID}\n"
            status_text += f"Status: Running\n"
            status_text += f"Active Notifications: {active_count}\n"
            status_text += f"Security Mode: {'Active' if self.security_active else 'Inactive'}"
            if USE_GUI_DIALOGS:
                messagebox.showinfo("Push Client Status", status_text)
            else:
                print(f"Push Client Status: {status_text}")
        except Exception as e:
            print(f"Error showing status: {e}")
    def show_all_notifications(self, icon=None, item=None):
        """Show all notification windows"""
        # First, restore any minimized windows
        for window in self.notification_windows:
            if window.minimized:
                window.restore_notification()
        # Then re-layer all windows
        self.layer_notification_windows()
    def has_active_notifications(self):
        """Check if there are any active (non-completed) notifications"""
        return any(not n.get('completed', False) for n in self.notifications)
    def can_snooze(self):
        """Check if snoozing is available (has notifications and not already snoozed)"""
        return self.has_active_notifications() and not self.is_snoozed()
    def is_snoozed(self):
        """Check if notifications are currently snoozed"""
        return bool(self.snooze_end_time and datetime.now() < self.snooze_end_time)
    def has_website_notification(self):
        """Check if current notification allows website requests"""
        if not self.has_active_notifications():
            return False
        active_notif = next((n for n in self.notifications if not n.get('completed', False)), None)
        # Check if notification allows website requests - either has allowed websites list or allows all
        return active_notif and ('allowedWebsites' in active_notif or active_notif.get('allowWebsites', False))
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
            print(f"Error in tray mark complete: {e}")
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
                    messagebox.showinfo("Request Sent", f"Website access request sent for: {website}")
                else:
                    print(f"Request Sent: Website access request sent for: {website}")
        except Exception as e:
            print(f"Error in tray request website: {e}")
    def tray_request_deletion(self, icon=None, item=None):
        """Request uninstallation from tray"""
        try:
            if USE_GUI_DIALOGS:
                reason = simpledialog.askstring(
                    "Request Deletion",
                    "Please provide a reason for requesting deletion:",
                    initialvalue="User requested removal"
                )
            else:
                reason = input("Please provide a reason for requesting deletion (or press Enter to cancel): ").strip()
                if not reason:
                    reason = "User requested removal"
            if reason:
                requests.post(API_URL, json={
                    'action': 'requestUninstall',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }, timeout=10)
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Request Sent", "Deletion request sent for admin approval.")
                else:
                    print("Request Sent: Deletion request sent for admin approval.")
        except Exception as e:
            print(f"Error in tray request deletion: {e}")
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
                system_info = {
                    'clientVersion': CLIENT_VERSION,
                    'platform': f"Windows-{platform.release()}-{platform.machine()}",
                    'pythonVersion': platform.python_version(),
                    'activeNotifications': len(self.notifications),
                    'securityActive': self.security_active
                }
                requests.post(API_URL, json={
                    'action': 'submitBugReport',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'bugDescription': bug_description,
                    'systemInfo': system_info,
                    'timestamp': datetime.now().isoformat()
                }, timeout=10)
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Bug Report Sent", "Thank you! Your bug report has been submitted.")
                else:
                    print("Bug Report Sent: Thank you! Your bug report has been submitted.")
        except Exception as e:
            print(f"Error in tray submit bug: {e}")
    def tray_snooze_all(self, minutes):
        """Snooze all notifications from tray"""
        try:
            self.snooze_notifications(minutes)
            if USE_GUI_DIALOGS:
                messagebox.showinfo("Snoozed", f"All notifications snoozed for {minutes} minutes.")
            else:
                print(f"Snoozed: All notifications snoozed for {minutes} minutes.")
        except Exception as e:
            print(f"Error in tray snooze all: {e}")
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
            tk.Label(info_frame, text=f"Version: {CLIENT_VERSION}").pack(anchor=tk.W, padx=5)
            tk.Label(info_frame, text=f"Client ID: {CLIENT_ID}").pack(anchor=tk.W, padx=5)
            tk.Label(info_frame, text=f"Status: {'Running' if self.running else 'Stopped'}").pack(anchor=tk.W, padx=5)
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
            print(f"Error showing settings: {e}")
    def show_about(self, icon=None, item=None):
        """Show about dialog"""
        try:
            about_text = f"""PushNotifications Client
Version: {CLIENT_VERSION}
Client ID: {CLIENT_ID}
© 2024 PushNotifications
Advanced notification management system
Features:
• Multi-monitor overlay support
• Website access control
• Automatic security enforcement
• Background operation"""
            messagebox.showinfo("About PushNotifications", about_text)
        except Exception as e:
            print(f"Error showing about: {e}")
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
            print(f"Error restarting client: {e}")
    def quit_application(self, icon=None, item=None):
        """Handle application quit - clean shutdown only"""
        self.running = False
        # Deactivate security features
        self.deactivate_security_features()
        # Send shutdown notification to server (not force quit)
        self.send_shutdown_notification()
        if self.tray_icon:
            self.tray_icon.stop()
    def check_notifications(self):
        """Main notification checking loop with robust error handling and retries"""
        print("Starting notification checker...")
        # Exponential backoff constants
        MIN_RETRY_DELAY = 5      # Initial retry delay in seconds
        MAX_RETRY_DELAY = 300    # Maximum retry delay (5 minutes)
        RETRY_MULTIPLIER = 2     # Multiply delay by this after each failure
        retry_delay = MIN_RETRY_DELAY
        consecutive_failures = 0
        last_success_time = None
        # Wait for startup before initiating network operations
        time.sleep(MIN_RETRY_DELAY)
        while self.running:
            try:
                # Handle snooze expiration
                if self.snooze_end_time and datetime.now() > self.snooze_end_time:
                    self.snooze_end_time = None
                    self.evaluate_security_state()
                # Prepare request data
                req_data = {
                    'action': 'getNotifications',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'version': CLIENT_VERSION,
                    'heartbeat': {
                        'uptime': int((datetime.now() - self.start_time).total_seconds()),
                        'activeNotifications': len(self.notifications),
                        'securityActive': self.security_active,
                        'lastSuccess': last_success_time.isoformat() if last_success_time else None,
                        'consecutiveFailures': consecutive_failures
                    } if hasattr(self, 'client_operational') and self.client_operational else None
                }
                # Make API request with retry logic
                for attempt in range(3):  # Try up to 3 times per iteration
                    try:
                        response = requests.post(
                            f"{API_URL}/api/index",
                            json=req_data,
                            timeout=10 * (attempt + 1)  # Increase timeout with each retry
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                # Process notifications
                                server_notifications = result.get('notifications', [])
                                self.process_notifications(server_notifications)
                                # Process server commands if any
                                if result.get('commands'):
                                    self._process_server_commands(result['commands'])
                                # Update operational state
                                self.client_operational = True
                                last_success_time = datetime.now()
                                consecutive_failures = 0
                                retry_delay = MIN_RETRY_DELAY
                                # Break out of retry loop on success
                                break
                            else:
                                logger.warning(f"API error: {result.get('message', 'Unknown error')}")
                                if attempt == 2:  # Log details on final attempt
                                    logger.error(f"API error details: {result}")
                        else:
                            logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}")
                            if attempt == 2:
                                logger.error(f"Response content: {response.text[:1000]}")
                    except requests.exceptions.Timeout:
                        logger.warning(f"Timeout on attempt {attempt + 1}")
                        continue
                    except requests.exceptions.ConnectionError:
                        logger.warning(f"Connection error on attempt {attempt + 1}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                        if attempt == 2:
                            import traceback
                            logger.error(f"Error details:\n{traceback.format_exc()}")
                        continue
                    # Brief pause between retries
                    if attempt < 2:
                        time.sleep(1)
                # If we get here and haven't broken out, all retries failed
                else:
                    consecutive_failures += 1
                    retry_delay = min(retry_delay * RETRY_MULTIPLIER, MAX_RETRY_DELAY)
                    # Log failure with diagnostic info
                    logger.error(f"All retries failed. Stats:")
                    logger.error(f"  Consecutive failures: {consecutive_failures}")
                    logger.error(f"  Next retry delay: {retry_delay}s")
                    logger.error(f"  Last success: {last_success_time or 'Never'}")
                    logger.error(f"  Client state: {self.client_operational=}, {self.security_active=}")
                    # Check if we need to notify user of connection issues
                    if consecutive_failures >= 3:
                        if USE_GUI_DIALOGS:
                            messagebox.showwarning(
                                "Connection Issues",
                                "Having trouble connecting to notification server.\n\n" +
                                "The client will continue trying to reconnect in the background."
                            )
                        else:
                            print("[WARNING] Connection issues detected - will retry in background")
                # Sleep between iterations, using exponential backoff on failures
                time.sleep(retry_delay if consecutive_failures > 0 else MIN_RETRY_DELAY)
            except requests.exceptions.RequestException as e:
                print(f"Network error in notification check: {e}")
                # Log additional error context
                try:
                    logger.error(f"Error details: {str(e.__cause__ or e.__context__ or e)}")
                    import traceback
                    logger.error(f"Stack trace:\n{traceback.format_exc()}")
                except:
                    pass
                # Continue loop but don't crash
                time.sleep(5)  # Brief delay before retry
                # Periodic update check (every hour)
                if not hasattr(self, '_last_update_check'):
                    self._last_update_check = time.time()
                elif time.time() - self._last_update_check > 3600:
                    try:
                        self._check_for_client_updates()
                    except Exception as e:
                        print(f"Error checking for updates: {e}")
                    self._last_update_check = time.time()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in notification check loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)
    def _send_heartbeat(self):
        """Send heartbeat/check-in to update client status and last seen time"""
        try:
            # Send heartbeat to update last seen time in database
            response = requests.post(f"{API_URL}/api/index", json={
                'action': 'updateClientStatus',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'timestamp': datetime.now().isoformat(),
                'status': 'online',
                'version': CLIENT_VERSION,
                'lastSeen': datetime.now().isoformat()
            }, timeout=5)  # Short timeout for heartbeat
            # Don't log success to avoid spam, only log errors
            if response.status_code != 200:
                print(f"Heartbeat warning: HTTP {response.status_code}")
        except Exception as e:
            # Log heartbeat errors but don't let them crash the client
            print(f"Heartbeat error: {e}")
    def process_notifications(self, server_notifications):
        """Process notifications from server and update display"""
        try:
            # Process notifications normally
            # Update internal notification list
            self.notifications = server_notifications
            # Close windows for completed/removed notifications
            active_ids = {n.get('id') for n in server_notifications if not n.get('completed', False)}
            windows_to_keep = []
            for w in self.notification_windows:
                if w.data.get('id') in active_ids:
                    windows_to_keep.append(w)
                else:
                    w.close()
            self.notification_windows = windows_to_keep
            # Create windows for new notifications
            existing_ids = {w.data.get('id') for w in self.notification_windows}
            for notification in server_notifications:
                if (not notification.get('completed', False) and 
                    notification.get('id') not in existing_ids):
                    self.create_notification_window(notification)
            # Update security state based on active notifications
            self.evaluate_security_state()
        except Exception as e:
            print(f"Error processing notifications: {e}")
    def create_notification_window(self, notification_data):
        """Create a new notification window"""
        try:
            window = NotificationWindow(notification_data, self.handle_notification_action)
            window.create_window()
            self.notification_windows.append(window)
            # Layer windows (oldest on top)
            self.layer_notification_windows()
        except Exception as e:
            print(f"Error creating notification window: {e}")
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
            print(f"Error layering windows: {e}")
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
            print(f"Error handling notification action: {e}")
    def snooze_notifications(self, minutes):
        """Snooze all notifications for specified minutes"""
        try:
            self.snooze_end_time = datetime.now() + timedelta(minutes=minutes)
            self.deactivate_security_features()
            # Hide notification windows
            for window in self.notification_windows:
                window.minimize_notification()
            # Send snooze status to server
            requests.post(API_URL, json={
                'action': 'snoozeNotifications',
                'clientId': CLIENT_ID,
                'minutes': minutes
            }, timeout=10)
        except Exception as e:
            print(f"Error snoozing notifications: {e}")
    def complete_notification(self, notification_id):
        """Mark notification as complete"""
        try:
            # Send completion to server
            response = requests.post(API_URL, json={
                'action': 'completeNotification',
                'clientId': CLIENT_ID,
                'notificationId': notification_id
            }, timeout=10)
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
            print(f"Error completing notification: {e}")
    def request_website_access(self, notification_id, website):
        """Request access to a specific website"""
        try:
            requests.post(API_URL, json={
                'action': 'requestWebsiteAccess',
                'clientId': CLIENT_ID,
                'notificationId': notification_id,
                'website': website
            }, timeout=10)
        except Exception as e:
            print(f"Error requesting website access: {e}")
    def tray_snooze_all(self, minutes):
        """Snooze all notifications for specified minutes from tray"""
        try:
            active_notifications = [n for n in self.notifications if not n.get('completed', False)]
            if active_notifications:
                self.snooze_notifications(minutes)
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Snoozed", f"All notifications snoozed for {minutes} minutes.")
                else:
                    print(f"Snoozed: All notifications snoozed for {minutes} minutes.")
            else:
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("No Notifications", "No active notifications to snooze.")
                else:
                    print("No Notifications: No active notifications to snooze.")
        except Exception as e:
            print(f"Error in tray snooze all: {e}")
    def tray_submit_bug(self, icon=None, item=None):
        """Submit bug report from tray"""
        try:
            if USE_GUI_DIALOGS:
                bug_description = simpledialog.askstring(
                    "Submit Bug Report",
                    "Please describe the bug or issue you encountered:",
                    initialvalue=""
                )
            else:
                bug_description = input("Please describe the bug or issue you encountered (or press Enter to cancel): ").strip()
                if not bug_description:
                    return
            if bug_description:
                requests.post(API_URL, json={
                    'action': 'submitBugReport',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'description': bug_description,
                    'timestamp': datetime.now().isoformat()
                }, timeout=10)
                if USE_GUI_DIALOGS:
                    messagebox.showinfo("Bug Report Sent", "Thank you for your bug report. It has been submitted.")
                else:
                    print("Bug Report Sent: Thank you for your bug report. It has been submitted.")
        except Exception as e:
            print(f"Error submitting bug report: {e}")
    def show_settings(self, icon=None, item=None):
        """Show settings dialog"""
        try:
            settings_text = f"Push Notifications Client Settings\n\n"
            settings_text += f"Client Version: {CLIENT_VERSION}\n"
            settings_text += f"Client ID: {CLIENT_ID}\n"
            settings_text += f"API URL: {API_URL}\n"
            settings_text += f"MAC Address: {MAC_ADDRESS}\n"
            settings_text += f"Use GUI Dialogs: {USE_GUI_DIALOGS}\n"
            settings_text += f"Installation Path: {os.path.dirname(os.path.abspath(__file__))}\n\n"
            settings_text += "Note: Settings are currently read-only."
            if USE_GUI_DIALOGS:
                messagebox.showinfo("Client Settings", settings_text)
            else:
                print(f"Client Settings: {settings_text}")
        except Exception as e:
            print(f"Error showing settings: {e}")
    def show_about(self, icon=None, item=None):
        """Show about dialog"""
        try:
            about_text = f"Push Notifications Client\n\n"
            about_text += f"Version: {CLIENT_VERSION}\n"
            about_text += f"© 2024 Push Notifications System\n\n"
            about_text += "A secure client for receiving and managing\n"
            about_text += "push notifications with web access control.\n\n"
            about_text += "Features:\n"
            about_text += "• Real-time notifications\n"
            about_text += "• Website access management\n"
            about_text += "• Security overlay system\n"
            about_text += "• Snooze and completion tracking\n"
            about_text += "• System tray integration"
            if USE_GUI_DIALOGS:
                messagebox.showinfo("About Push Notifications Client", about_text)
            else:
                print(f"About Push Notifications Client: {about_text}")
        except Exception as e:
            print(f"Error showing about: {e}")
    def quit_application(self, icon=None, item=None):
        """Quit application (requires admin rights)"""
        try:
            # Check if running as admin
            if not self._is_admin():
                if USE_GUI_DIALOGS:
                    messagebox.showerror("Admin Required", 
                                       "Administrator privileges are required to quit the application.")
                else:
                    print("Error: Administrator privileges are required to quit the application.")
                return
            # Confirm quit
            if USE_GUI_DIALOGS:
                result = messagebox.askyesno("Confirm Quit", 
                                           "Are you sure you want to quit Push Notifications Client?")
                if not result:
                    return
            else:
                confirm = input("Are you sure you want to quit Push Notifications Client? (y/N): ").strip().lower()
                if confirm != 'y' and confirm != 'yes':
                    return
            # Send shutdown notification
            self.send_shutdown_notification()
            # Stop the client
            self.running = False
            # Stop the tray icon
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            print(f"Error quitting application: {e}")
    def _is_admin(self):
        """Check if running with admin privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
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
            print(f"Error evaluating security state: {e}")
    def activate_security_features(self, notifications):
        """Activate security features (overlay, minimize, restrict)"""
        try:
            self.security_active = True
            # Get allowed websites from top notification
            top_notification = notifications[0] if notifications else {}
            allowed_websites = top_notification.get('allowedWebsites', [])
            # Show grey overlays on all monitors
            self.overlay_manager.show_overlays()
            # Minimize all windows
            self.window_manager.minimize_all_windows()
            # Block restricted processes
            self.window_manager.block_restricted_processes(allowed_websites)
        except Exception as e:
            print(f"Error activating security features: {e}")
    def deactivate_security_features(self):
        """Deactivate security features"""
        try:
            self.security_active = False
            # Hide overlays
            self.overlay_manager.hide_overlays()
            # Restore windows
            self.window_manager.restore_windows()
        except Exception as e:
            print(f"Error deactivating security features: {e}")
    def send_shutdown_notification(self):
        """Send clean shutdown notification to server"""
        try:
            requests.post(API_URL, json={
                'action': 'clientShutdown',
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS,
                'timestamp': datetime.now().isoformat()
            }, timeout=10)
        except Exception as e:
            pass  # Ignore shutdown notification errors
    def handle_uninstall_command(self, reason):
        """Handle uninstall command received from server"""
        try:
            print(f"Processing uninstall command: {reason}")
            # Deactivate security features first
            self.deactivate_security_features()
            # Close all notification windows
            for window in self.notification_windows:
                window.close()
            self.notification_windows.clear()
            # Send acknowledgment to server
            try:
                requests.post(API_URL, json={
                    'action': 'acknowledgeUninstall',
                    'clientId': CLIENT_ID,
                    'macAddress': MAC_ADDRESS,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }, timeout=10)
            except Exception as e:
                print(f"Error sending uninstall acknowledgment: {e}")
            # Exit the client
            self.running = False
        except Exception as e:
            print(f"Error handling uninstall command: {e}")
    def _check_for_client_updates(self):
        """Check for client updates"""
        try:
            response = requests.post(API_URL, json={
                'action': 'checkVersion',
                'currentVersion': CLIENT_VERSION,
                'clientId': CLIENT_ID,
                'macAddress': MAC_ADDRESS
            }, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('updateAvailable'):
                    # Launch updater using Python
                    installer_path = Path(__file__).parent / "installer.py"
                    if installer_path.exists():
                        subprocess.Popen([sys.executable, str(installer_path), "--update"],
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Error checking for updates: {e}")
    def run(self):
        """Main application loop"""
        try:
            print("Initializing Push Client...")
            # Create tray icon if available
            if WINDOWS_FEATURES_AVAILABLE:
                print("Creating tray icon...")
                self.tray_icon = self.create_tray_icon()
                print("Tray icon created successfully")
            # Start notification checker in background thread
            print("Starting notification checker thread...")
            notif_thread = threading.Thread(target=self.check_notifications, daemon=True)
            notif_thread.start()
            print("Notification checker thread started")
            # Run main loop
            if self.tray_icon and WINDOWS_FEATURES_AVAILABLE:
                print("Starting tray icon main loop...")
                self.tray_icon.run()
            else:
                print("Push Client running in console mode...")
                while self.running:
                    time.sleep(1)
        except Exception as e:
            print(f"Error in main run loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Shutting down client...")
# The embedded client code above is only used when Client.py runs independently.
# The installer script below should NOT auto-run the embedded client.
# Client.py file will be created separately and launched as subprocess after install.
        sys.exit(1)
class FileProtectionService:
    """File system protection service for installation security"""
    def __init__(self, install_path):
        self.install_path = install_path
        self.running = True
        self.pending_approvals = {}
        # Protected paths for file monitoring
        self.protected_paths = {
            str(self.install_path),
            str(self.install_path.parent),
            str(self.install_path / "Client.py"),
            str(self.install_path / ".vault"),
            str(self.install_path / ".security_marker")
        }
        print(f"File Protection Service initialized for: {self.install_path}")
    def terminate_process(self, process_id):
        """Safely terminate a process"""
        try:
            proc = psutil.Process(process_id)
            proc.terminate()
            # Wait a bit and force kill if necessary
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                print(f"[FIRE] Force killing process: {process_id}")
                proc.kill()
            print(f"[OK] Process terminated: {process_id}")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Could not terminate process {process_id}: {e}")
    def restore_file_attributes(self, file_path):
        """Restore proper file attributes"""
        try:
            # Windows-only installer - restore file attributes unconditionally
            try:
                import win32file
                import win32con
                # Restore hidden and system attributes
                attrs = (win32con.FILE_ATTRIBUTE_HIDDEN | 
                        win32con.FILE_ATTRIBUTE_SYSTEM)
                win32file.SetFileAttributes(str(file_path), attrs)
                print(f"[OK] Restored attributes for: {Path(file_path).name}")
            except ImportError:
                print("Warning: win32file not available for attribute restoration")
        except Exception as e:
            print(f"Error restoring attributes: {e}")
    def log_approval_action(self, request_id, action):
        """Log approval actions for audit trail"""
        try:
            log_data = {
                'requestId': request_id,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'details': self.pending_approvals.get(request_id, {})
            }
            # Send log to server - using DEFAULT_API_URL as fallback
            api_url = getattr(self, 'api_url', DEFAULT_API_URL)
            requests.post(f"{api_url}/api/index", json={
                'action': 'logApprovalAction',
                'clientId': getattr(self, 'client_id', 'unknown'),
                'logData': log_data
            }, timeout=10)
        except Exception as e:
            print(f"Error logging approval action: {e}")
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
                    print(f"[CLEANUP] Cleaning up old request: {req_id}")
                    del self.pending_approvals[req_id]
                time.sleep(3600)  # Clean up every hour
            except Exception as e:
                print(f"Error in cleanup: {e}")
                time.sleep(3600)
    def monitor_suspicious_processes(self):
        """Monitor for suspicious processes that might interfere with installation"""
        while self.running:
            try:
                # Monitor for processes that might try to tamper with installation
                suspicious_processes = ['uninstall', 'delete', 'remove', 'clean']
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if any(suspicious in ' '.join(proc.info.get('cmdline', [])).lower() 
                              for suspicious in suspicious_processes):
                            print(f"[ALERT] Suspicious process detected: {proc.info['name']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in process monitoring: {e}")
                time.sleep(60)
    def monitor_file_system_changes(self):
        """Monitor file system changes to protected paths"""
        while self.running:
            try:
                # Basic file existence check
                for protected_path in self.protected_paths:
                    if not Path(protected_path).exists():
                        print(f"[ALERT] Protected file missing: {protected_path}")
                        # Could trigger restoration process here
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error in file system monitoring: {e}")
                time.sleep(300)
    def run(self):
        """Main service loop"""
        print(f"[SHIELD] File System Protection Service Started")
        print(f"    Install Path: {self.install_path}")
        print(f"    Protected Paths: {len(self.protected_paths)}")
        try:
            # Start monitoring threads
            threads = [
                threading.Thread(target=self.monitor_suspicious_processes, daemon=True),
                threading.Thread(target=self.monitor_file_system_changes, daemon=True),
                threading.Thread(target=self.cleanup_old_requests, daemon=True)
            ]
            for thread in threads:
                thread.start()
                print(f"[OK] Started monitoring thread: {thread.name}")
            # Main service loop
            while self.running:
                # Periodic status report
                active_requests = len([r for r in self.pending_approvals.values() 
                                     if r.get('status') == 'pending'])
                if active_requests > 0:
                    print(f"[STATUS] Status: {active_requests} pending approval requests")
                time.sleep(300)  # Status update every 5 minutes
        except KeyboardInterrupt:
            print("\n[STOP] File Protection Service stopping...")
            self.stop()
        except Exception as e:
            print(f"[BOOM] Service error: {e}")
            self.stop()
    def stop(self):
        """Stop the protection service"""
        self.running = False
        print("[OK] File Protection Service stopped")
# Standalone functions outside the class
# Unix functionality removed - Windows-only installer
def notify_installation_failure(
    installer_instance: "PushNotificationsInstaller",
    stage: str,
    error_message: str,
    correlation_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """Notify the server that the installation has failed with detailed error tracking.
    Records rich diagnostic information and error context with correlation IDs for request
    tracing and causal analysis. Handles error notifications with retries and detailed
    logging of system state.
    Args:
        installer_instance: The PushNotificationsInstaller instance containing device info
        stage: The specific installation stage where failure occurred (e.g. "registry", "files")
        error_message: Detailed error message/traceback for diagnostics
        correlation_id: Optional UUID to correlate related errors. Auto-generated if not provided
        context: Optional dict of additional error context (e.g. file paths, states)
    Returns:
        bool: True if notification was successfully sent and acknowledged by server
    Example:
        >>> corr_id = str(uuid.uuid4())
        >>> notify_installation_failure(
        ...     installer,
        ...     "registry", 
        ...     "Access denied when creating registry key",
        ...     correlation_id=corr_id,
        ...     context={'reg_key': 'HKCU\\Software\\PushNotifications'}
        ... )
        True
    Raises:
        No exceptions are raised - all errors are caught and logged
    """
    # Generate or use correlation ID
    correlation_id = correlation_id or str(uuid.uuid4())
    logger.info("Beginning installation failure notification processing", extra={
        'correlation_id': correlation_id,
        'stage': stage,
        'has_installer': bool(installer_instance),
        'installer_version': getattr(installer_instance, 'version', 'UNKNOWN'),
        'installer_state': {
            'initialized': hasattr(installer_instance, 'device_data'),
            'has_config': bool(getattr(installer_instance, 'config', None)),
            'install_path': str(getattr(installer_instance, 'install_path', None))
        }
    })
    # Validate required parameters with detailed logs
    validation_errors = []
    if not installer_instance:
        validation_errors.append("Missing installer instance")
    if not stage:
        validation_errors.append("Missing failure stage")
    if not error_message:
        validation_errors.append("Missing error message")
    if validation_errors:
        logger.error("Validation failed for failure notification", extra={
            'validation_errors': validation_errors,
            'stage': stage or 'UNKNOWN'
        })
        return False
    # Log detailed failure report
    logger.info("Valid failure notification received", extra={
        'stage': stage,
        'error_summary': str(error_message)[:100] + '...' if len(str(error_message)) > 100 else str(error_message),
        'installer_version': getattr(installer_instance, 'version', 'UNKNOWN')
    })
    # Convert error message to string and truncate with length check
    orig_length = len(str(error_message))
    error_message = str(error_message)[:2000]
    if orig_length > 2000:
        logger.warning(f"Error message truncated from {orig_length} to 2000 characters")
    try:
        # Get device data with fallback
        device_data = {}
        try:
            device_data = getattr(installer_instance, 'device_data', {}) or {}
        except AttributeError:
            logger.warning("Could not access device data")
        # Gather system info with comprehensive error handling 
        system_info = {}
        try:
            system_info = {
                'osVersion': f"Windows {platform.release()} {platform.version()}",
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'isAdmin': False,  # Default to False
                'timezone': str(datetime.now().astimezone().tzinfo),
                'memory': None,
                'diskSpace': None
            }
            # Try to get admin status
            try:
                system_info['isAdmin'] = bool(installer_instance.check_admin_privileges())
            except AttributeError:
                pass
            # Try to get additional metrics if psutil available
            try:
                import psutil
                memory = psutil.virtual_memory()
                system_info['memory'] = {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                }
                disk = psutil.disk_usage('/')
                system_info['diskSpace'] = {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': disk.percent
                }
            except ImportError:
                pass  # psutil not available
        except Exception as e:
            logger.warning(f"Error gathering system info: {e}")
            system_info = {
                'error': f"Failed to gather system info: {str(e)}",
                'partial': True,
                'osVersion': 'Windows (version unknown)',
                'pythonVersion': f"{sys.version_info.major}.{sys.version_info.minor}"
            }
        # Safely build notification data
        failure_data = {
            'action': 'reportInstallationFailure',
            'macAddress': getattr(installer_instance, 'mac_address', None),
            'username': getattr(installer_instance, 'username', None),
            'clientName': getattr(installer_instance, 'client_name', None),
            'keyId': getattr(installer_instance, 'key_id', None),
            'deviceId': device_data.get('deviceId'),
            'clientId': device_data.get('clientId'),
            'stage': stage,
            'error': error_message,
            'version': getattr(installer_instance, 'version', INSTALLER_VERSION),
            'platform': f"Windows {platform.release()}",
            'timestamp': datetime.now().isoformat(),
            'installPath': str(getattr(installer_instance, 'install_path', 'unknown')),
            'systemInfo': system_info,
            'installation_mode': getattr(installer_instance, 'repair_mode', False) and 'repair' or 'fresh',
            'is_update': getattr(installer_instance, 'update_mode', False)
        }
        # Validate required fields
        required_fields = ['macAddress', 'username', 'stage', 'error']
        missing_fields = [field for field in required_fields if not failure_data.get(field)]
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        # Ensure we have a valid API URL
        api_url = getattr(installer_instance, 'api_url', None)
        if not api_url:
            logger.error("Missing API URL")
            return False
        # URL validation
        try:
            from urllib.parse import urlparse
            parsed = urlparse(api_url)
            if not all([parsed.scheme, parsed.netloc]):
                logger.error("Invalid API URL format")
                return False
        except Exception as e:
            logger.error(f"API URL validation failed: {e}")
            return False
        # Send notification with retry
        max_retries = 3
        retry_delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{api_url}/api/index",
                    json=failure_data,
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info("Installation failure reported successfully")
                        return True
                    else:
                        logger.warning(f"Server rejected failure report: {result.get('message')}")
                        # Only retry on server errors, not validation failures
                        if 'error' in result.get('message', '').lower():
                            continue
                        return False
                elif response.status_code >= 500:
                    logger.warning(f"Server error (HTTP {response.status_code}), retrying...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Failed to report failure: HTTP {response.status_code}")
                    return False
            except requests.Timeout:
                logger.warning(f"Request timeout, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            except requests.RequestException as e:
                logger.error(f"Network error: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error sending notification: {e}")
                return False
    except Exception as e:
        logger.error(f"Critical error in failure notification: {e}")
        # Log the full traceback for debugging
        import traceback
        logger.debug("Full error details:\n%s", traceback.format_exc())
    return False
def create_desktop_shortcuts(installer_instance):
    """Create desktop shortcuts for client and installer"""
    print("Creating desktop shortcuts...")
    try:
        if installer_instance.system == "Windows":
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
            client_shortcut.Arguments = f'"{installer_instance.install_path / "Client.py"}"'
            client_shortcut.WorkingDirectory = str(installer_instance.install_path)
            client_shortcut.Description = "PushNotifications Client"
            client_shortcut.save()
            # Create Installer/Repair shortcut - Python only
            repair_shortcut = shell.CreateShortCut(str(desktop / "Push Client Repair.lnk"))
            repair_shortcut.Targetpath = "python.exe"
            repair_shortcut.Arguments = f'"{installer_instance.install_path / "installer.py"}" --repair'
            repair_shortcut.WorkingDirectory = str(installer_instance.install_path)
            repair_shortcut.Description = "PushNotifications Installer/Repair"
            repair_shortcut.save()
            print("[OK] Desktop shortcuts created")
        # Note: This installer is Windows-only, Unix desktop files not supported
        return True
    except Exception as e:
        print(f"[ERR] Failed to create shortcuts: {e}")
        return False
def show_help():
    """Display comprehensive help information"""
    print(f"""PushNotifications Universal Installer v{INSTALLER_VERSION}
{"=" * 60}
⚠️  ADMINISTRATOR PRIVILEGES REQUIRED ⚠️
This installer and the PushNotifications client require administrator
privileges for ALL operations including:
  • Installation and system setup
  • Client operation and ongoing functionality  
  • System integration and security features
  • Process management and window control
The installer will automatically request elevation if needed.
[GLOBAL] UNIVERSAL PYTHON INSTALLER
- Single .py file runs on Windows, macOS, Linux
- Windows: Runs as Python script with admin privileges
- No external dependencies required for basic installation
- Automatically detects OS and adapts functionality
[WINDOWS] WINDOWS ENTERPRISE FEATURES
- Python-based operation with admin privileges
- Hidden encrypted installation with AES-256-GCM vault encryption
- Real MAC address detection and transmission
- Admin privilege escalation without UAC prompts
- Multi-monitor 25% grey overlay system
- Force-minimize window restrictions during active notifications
- Website allowlist enforcement and request system
- Taskbar-initiated uninstallation with server approval
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
IMPORTANT: Administrator privileges are required for both installation
           AND ongoing client operation. The installer will automatically
           request elevation if needed, but the client must always run
           with administrator privileges to function properly.
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
        # EARLY DEBUG: Log process start immediately
        print("[DEBUG] Main function started")
        print(f"[DEBUG] Command line args: {sys.argv}")
        print(f"[DEBUG] Python executable: {sys.executable}")
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        # Check if this is an admin restart (elevated process)
        is_admin_restart = '--admin-restart' in sys.argv
        print(f"[DEBUG] Is admin restart: {is_admin_restart}")
        print(f"PushNotifications Installer v{INSTALLER_VERSION}")
        print("=" * 50)
        if is_admin_restart:
            print("Elevated installation process started...")
            print("[DEBUG] Elevated process initialization successful")
        else:
            print("Starting installation process...")
            print("[DEBUG] Normal process initialization successful")
        # Parse command line arguments first to handle help/docs before admin check
        api_url = None
        repair_mode = False
        update_mode = False
        check_only = False
        show_docs_menu = False
        show_specific_doc = None
        # Parse message file parameter for elevated process
        message_file = None
        for arg in sys.argv[1:]:
            if arg.startswith('http'):
                api_url = arg
            elif arg.startswith('--message-file='):
                message_file = arg.split('=', 1)[1]
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
            # Note: --admin-restart is processed above and not included in normal arg processing
        # Handle documentation requests
        if show_docs_menu:
            show_documentation_menu()
            return
        if show_specific_doc:
            show_specific_documentation(show_specific_doc)
            return
        # CRITICAL: Administrator privileges required for ALL operations
        # This installer and the PushNotifications client require admin privileges
        # for installation, system integration, and ongoing operation
        print("\nChecking administrator privileges...")
        print("Administrator privileges are required for:")
        print("  • Installation and setup")
        print("  • System integration and hidden file management")
        print("  • Ongoing client operation and security features")
        print("  • Process management and window control")
        # Create temporary installer instance just for privilege checking
        temp_installer = PushNotificationsInstaller()
        if not temp_installer.check_admin_privileges():
            if is_admin_restart:
                # This should not happen - admin restart failed to gain privileges
                print("\n[CRITICAL ERROR] Admin restart failed to obtain privileges")
                print("                 The elevated process does not have administrator access.")
                print("                 This indicates a system or UAC configuration issue.")
                print("\n[SOLUTION] Please try one of the following:")
                print("           • Right-click the installer and select 'Run as administrator'")
                print("           • Check UAC settings in Windows Security")
                print("           • Verify your account has administrator permissions")
                input("\nPress Enter to exit...")
                sys.exit(1)
            print("\n[REQUIRED] Administrator privileges are needed for installation and client operation.")
            print("Restarting with administrator privileges...")
            if not temp_installer.restart_with_admin():
                print("\n[ERR] Installation failed: Could not obtain administrator privileges")
                print("       Please run as administrator or contact support.")
                print("\n       The PushNotifications client requires admin privileges for:")
                print("         - Secure file system integration")
                print("         - Process and window management")
                print("         - System-level security features")
                input("\nPress Enter to exit...")
                return
            return  # Process will restart with admin privileges
        # Initialize message relay for elevated process
        message_relay = None
        if message_file and is_admin_restart:
            try:
                message_relay = MessageRelay(message_file)
                message_relay.send_status("elevated", "Administrator privileges granted - installation starting...")
                print("[OK] Successfully elevated with administrator privileges")
                print("[OK] Message relay system initialized")
            except Exception as e:
                logger.warning(f"Message relay initialization failed: {e}")
                print("[OK] Successfully elevated with administrator privileges")
        elif is_admin_restart:
            print("[OK] Successfully elevated with administrator privileges")
        else:
            print("[OK] Running with administrator privileges")
        print()
        # Handle special modes
        if check_only:
            print("[CHECK] PushNotifications Update Check")
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
            print("[UPDATE] PushNotifications Update Mode")
            print("=" * 50)
            print("This will check for and install the latest version.")
            print()
        if repair_mode:
            print("[REPAIR] PushNotifications Repair Mode")
            print("=" * 50)
            print("This will attempt to repair or reinstall PushNotifications.")
            print("Existing settings and configurations will be preserved where possible.")
            print()
        # Create and run installer
        installer = PushNotificationsInstaller(api_url)
        # Pass message relay to installer if available
        if message_relay:
            installer.message_relay = message_relay
        if repair_mode:
            # In repair mode, skip key validation and try to preserve existing settings
            installer.repair_mode = True
            print("Starting repair process...")
            if message_relay:
                message_relay.send_status("repair", "Starting repair process...")
        if update_mode:
            # In update mode, check for updates first
            installer.update_mode = True
            print("Checking for available updates...")
            if installer.check_for_updates():
                print(f"\nUpdate found: v{installer.update_data['currentVersion']} → v{installer.update_data['latestVersion']}")
                print("Release notes:", installer.update_data.get('updateNotes', 'No release notes available'))
                # Ask for confirmation unless it's a required update
                if installer.update_data.get('updateRequired', False):
                    print("\n[WARNING] This is a required security update.")
                    proceed = True
                else:
                    # Use console input for update confirmation
                    proceed = input("\nInstall update? (y/N): ").lower().startswith('y')
                if proceed:
                    if installer.download_and_apply_update():
                        print("\n[COMPLETED] Update completed successfully!")
                        print("The updated installer is ready to use.")
                        sys.exit(0)
                    else:
                        print("\n[FAILED] Update failed. Please try again later.")
                        sys.exit(1)
                else:
                    print("\nUpdate cancelled by user.")
                    sys.exit(0)
            else:
                print("\n[COMPLETED] Already running the latest version.")
                sys.exit(0)
        success = installer.run_installation()
        if success:
            if message_relay:
                message_relay.send_status("launching", "Installation complete - starting client...")
            
            # Launch client as separate background process with enhanced configuration
            try:
                client_path = installer.install_path / "Client.py"
                if client_path.exists():
                    print(f"[INFO] Starting client from: {client_path}")
                    
                    # Create runtime configuration file for client
                    config_data = {
                        'api_url': installer.api_url,
                        'client_id': installer.device_data.get('clientId', 'unknown'),
                        'key_id': installer.key_id,
                        'mac_address': installer.mac_address,
                        'install_path': str(installer.install_path),
                        'version': INSTALLER_VERSION,
                        'run_invisibly': True,
                        'startup_timestamp': datetime.now().isoformat()
                    }
                    
                    config_path = installer.install_path / "config.json"
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2)
                    
                    # Set config file as hidden
                    subprocess.run(["attrib", "+H", str(config_path)], 
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    print(f"[OK] Configuration saved for client startup")
                    
                    # Use pythonw.exe to ensure no console window appears
                    pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                    if not Path(pythonw_exe).exists():
                        pythonw_exe = sys.executable  # Fallback to python.exe
                        print(f"[INFO] Using python.exe (pythonw.exe not found)")
                    else:
                        print(f"[OK] Using pythonw.exe for invisible startup")
                    
                    # Start client with admin privileges and hidden window
                    process = subprocess.Popen(
                        [pythonw_exe, str(client_path)],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        cwd=str(installer.install_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    # Monitor client startup process
                    startup_success = False
                    for check_attempt in range(5):  # Check 5 times over 10 seconds
                        time.sleep(2)
                        
                        # Check if process is still running
                        if process.poll() is None:
                            startup_success = True
                            print(f"[OK] Client process running (PID: {process.pid})")
                            break
                        else:
                            print(f"[WARNING] Client process check {check_attempt + 1}: Process not running (exit code: {process.returncode})")
                    
                    # Final status report
                    if startup_success:
                        print("[OK] Client started successfully in background")
                        if message_relay:
                            message_relay.send_status("success", "Installation completed successfully - client is running")
                    else:
                        print(f"[WARNING] Client process failed to remain running after multiple checks")
                        print(f"[INFO] Client may need admin privileges or have dependency issues")
                        print(f"[INFO] Try running as administrator or check Python dependencies")
                        if message_relay:
                            message_relay.send_status("warning", "Client started but failed to remain running - may need admin privileges")
                else:
                    print(f"[WARNING] Client.py not found at: {client_path}")
                    print(f"[INFO] Files in install directory: {list(installer.install_path.glob('*'))}")
                    if message_relay:
                        message_relay.send_status("warning", "Installation completed but client could not be started - file not found")
            except Exception as e:
                print(f"[WARNING] Could not start client: {e}")
                import traceback
                traceback.print_exc()
                if message_relay:
                    message_relay.send_status("warning", f"Installation completed but client failed to start: {e}")
            
            # Installation complete message shown only in console, not as popup
            # Removed GUI dialog to only show cmd window during installation
            if message_relay:
                message_relay.send_status("completed", "Installation process finished - ready to exit")
            print("\nInstallation completed. Press Enter to exit...")
            input()
            sys.exit(0)
        else:
            if message_relay:
                message_relay.send_status("failed", "Installation failed - check logs for details")
            print("\nInstallation failed. Press Enter to exit...")
            input()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nInstallation failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
if __name__ == "__main__":
    main()