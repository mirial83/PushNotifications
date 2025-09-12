const fs = require('fs');
const path = require('path');

// CORS handler
function setCORSHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

// Updated Python client code for Vercel/MongoDB
function getDesktopClientCode() {
  return `#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PushNotifications Desktop Client - Vercel/MongoDB Version

A cross-platform desktop client for receiving push notifications
via Vercel API backend with MongoDB database.

Features:
- Real-time notification display with web form styling
- Gradient flash effects on screen sides (50% opacity)
- Work mode with website blocking  
- System tray integration
- Emergency shutdown mechanisms
- Consistent font and color scheme with web interface

Colors (matching web form):
- Background: #1e6b7a (teal)
- Header gradient: #1e6b7a to #4a1a4a (teal to purple)
- Font: Arial 16pt
- Button colors: #4a1a4a (purple)

Usage:
    python3 pushnotifications.py [options]

Options:
    --system-integration    Enable system tray and advanced features
    --setup-autostart      Configure automatic startup
    --install              Run installation wizard
    --help                 Show help message

Installation:
    1. Download this file
    2. Run: python3 pushnotifications.py --install
    3. Follow the setup prompts
    4. Configure your Vercel API URL
"""

import sys
import os
import platform
import json
import uuid
import threading
import time
import logging
import argparse
from datetime import datetime, timedelta
from urllib.parse import urlparse

# GUI imports
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: tkinter not available. GUI features disabled.")

# HTTP requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Error: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# Version information
VERSION = "2.1.0"
BUILD_DATE = "2024-09-12"

# Web form matching colors and styling
WEB_FORM_COLORS = {
    'background': '#1e6b7a',  # Main teal background
    'header_start': '#1e6b7a',  # Gradient start (teal)
    'header_end': '#4a1a4a',    # Gradient end (purple)
    'button_bg': '#4a1a4a',     # Button background (purple)
    'button_hover': '#3d1538',  # Button hover (darker purple)
    'white': '#ffffff',         # White for text and containers
    'input_bg': '#f0f0f0',      # Input field background
    'border': '#cccccc',        # Border colors
    'text_dark': '#333333',     # Dark text
    'text_light': '#666666',    # Light text
}

WEB_FORM_FONTS = {
    'family': 'Arial',
    'size': 16,              # 16pt font size
    'size_small': 14,        # Small text
    'size_header': 18,       # Header text
}

class NotificationClient:
    def __init__(self):
        self.version = VERSION
        self.client_id = self.get_or_create_client_id()
        self.client_name = self.get_client_name()
        self.computer_name = platform.node()
        self.api_base_url = None
        self.running = False
        
        # Initialize logging
        self.setup_logging()
        
        print(f"PushNotifications Desktop Client v{VERSION}")
        print(f"Client ID: {self.client_id[:8]}...")
        print(f"Client Name: {self.client_name}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print()
        
        # Load configuration if exists
        self.load_config()
        
    def setup_logging(self):
        """Configure logging system"""
        log_dir = os.path.expanduser("~/.pushnotifications")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "pushnotifications.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def get_or_create_client_id(self):
        """Get or create unique client identifier"""
        config_dir = os.path.expanduser("~/.pushnotifications")
        os.makedirs(config_dir, exist_ok=True)
        id_file = os.path.join(config_dir, "client_id")
        
        if os.path.exists(id_file):
            with open(id_file, 'r') as f:
                return f.read().strip()
        else:
            client_id = str(uuid.uuid4())
            with open(id_file, 'w') as f:
                f.write(client_id)
            return client_id
            
    def get_client_name(self):
        """Get or create client friendly name"""
        config_dir = os.path.expanduser("~/.pushnotifications")
        name_file = os.path.join(config_dir, "client_name")
        
        if os.path.exists(name_file):
            with open(name_file, 'r') as f:
                return f.read().strip()
        else:
            import getpass
            default_name = f"{getpass.getuser()}@{platform.node()}"
            
            if GUI_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                name = simpledialog.askstring(
                    "Client Setup",
                    f"Enter a friendly name for this client:\\n\\nDefault: {default_name}",
                    initialvalue=default_name
                )
                root.destroy()
                
                if name:
                    with open(name_file, 'w') as f:
                        f.write(name)
                    return name
            
            return default_name
    
    def load_config(self):
        """Load configuration from file"""
        config_dir = os.path.expanduser("~/.pushnotifications")
        config_file = os.path.join(config_dir, "config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.api_base_url = config.get('api_base_url')
                    print(f"✅ Configuration loaded from: {config_file}")
            except Exception as e:
                print(f"❌ Error loading config: {e}")
        else:
            print("⚠️ No configuration found. Please run --install first.")
    
    def run_installation(self):
        """Run the installation wizard"""
        print("🚀 Starting PushNotifications Installation...")
        print()
        
        # Check requirements
        if not self.check_requirements():
            return False
            
        # Show styled installation window if GUI available
        if GUI_AVAILABLE:
            self.show_installation_gui()
        else:
            # Fallback to console installation
            api_url = input("Enter your Vercel API URL (e.g., https://yourapp.vercel.app): ")
            if api_url:
                self.save_config(api_url)
            
        print("✅ Installation completed successfully!")
        print(f"Configuration saved to: ~/.pushnotifications/")
        print()
        print("You can now run the client with:")
        print("  python3 pushnotifications.py")
        print()
        return True
    
    def show_installation_gui(self):
        """Show installation GUI with web form styling"""
        window = tk.Tk()
        window.title("PushNotifications Setup")
        window.geometry("500x350")
        window.configure(bg=WEB_FORM_COLORS['background'])
        
        # Header
        header_frame = tk.Frame(window, bg=WEB_FORM_COLORS['header_end'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text="PushNotifications Setup",
            font=(WEB_FORM_FONTS['family'], WEB_FORM_FONTS['size_header'], 'bold'),
            bg=WEB_FORM_COLORS['header_end'],
            fg=WEB_FORM_COLORS['white']
        )
        header_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(window, bg=WEB_FORM_COLORS['white'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Instructions
        instructions = tk.Label(
            content_frame,
            text="Enter your Vercel API URL below:\\n(e.g., https://yourapp.vercel.app)",
            font=(WEB_FORM_FONTS['family'], WEB_FORM_FONTS['size']),
            bg=WEB_FORM_COLORS['white'],
            fg=WEB_FORM_COLORS['text_dark']
        )
        instructions.pack(pady=(0, 20))
        
        # URL entry
        url_var = tk.StringVar()
        url_entry = tk.Entry(
            content_frame,
            textvariable=url_var,
            font=(WEB_FORM_FONTS['family'], WEB_FORM_FONTS['size']),
            bg=WEB_FORM_COLORS['input_bg'],
            width=50
        )
        url_entry.pack(pady=10, ipady=5)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg=WEB_FORM_COLORS['white'])
        button_frame.pack(pady=20)
        
        def save_and_close():
            url = url_var.get().strip()
            if url:
                self.save_config(url)
                window.quit()
                window.destroy()
            else:
                messagebox.showerror("Error", "Please enter a valid URL")
        
        save_btn = tk.Button(
            button_frame,
            text="Save Configuration",
            font=(WEB_FORM_FONTS['family'], WEB_FORM_FONTS['size'], 'bold'),
            bg=WEB_FORM_COLORS['button_bg'],
            fg=WEB_FORM_COLORS['white'],
            activebackground=WEB_FORM_COLORS['button_hover'],
            border=0,
            padx=20,
            pady=10,
            command=save_and_close
        )
        save_btn.pack()
        
        window.mainloop()
        
    def save_config(self, api_base_url):
        """Save configuration to file"""
        config_dir = os.path.expanduser("~/.pushnotifications")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")
        
        # Ensure URL doesn't end with slash
        if api_base_url.endswith('/'):
            api_base_url = api_base_url[:-1]
        
        config = {
            "api_base_url": api_base_url,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "version": VERSION
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.api_base_url = api_base_url
        print(f"✅ Configuration saved")
        
    def check_requirements(self):
        """Check system requirements"""
        print("Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 7):
            print("❌ Python 3.7 or higher is required")
            return False
        print(f"✅ Python {sys.version}")
        
        return True
    
    def check_for_updates(self, silent=False):
        """Check for updates from the Vercel API"""
        if not silent:
            print("🔄 Checking for updates...")
            
        if not self.api_base_url:
            if not silent:
                print("❌ No configuration found. Cannot check for updates.")
            return False
            
        try:
            response = requests.get(
                f"{self.api_base_url}/api",
                params={'action': 'get_version'},
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    version_info = response.json()
                    
                    if version_info.get('success'):
                        server_version = version_info.get('latestVersion', VERSION)
                        update_available = version_info.get('updateAvailable', False)
                        force_update = version_info.get('forceUpdate', False)
                        
                        if not silent:
                            print(f"Current version: {VERSION}")
                            print(f"Server version: {server_version}")
                            if version_info.get('releaseNotes'):
                                print(f"Release notes: {version_info.get('releaseNotes')}")
                        
                        needs_update = update_available or force_update or self.is_newer_version(server_version, VERSION)
                        
                        if needs_update:
                            if not silent:
                                print(f"✅ Update available: {server_version}")
                                if force_update:
                                    print("⚠️ This is a forced update - installation required")
                            return self.download_and_install_update(silent, force_update)
                        else:
                            if not silent:
                                print("✅ Client is up to date")
                            return False
                        
                except json.JSONDecodeError:
                    if not silent:
                        print("❌ Invalid response from server")
                    return False
            else:
                if not silent:
                    print(f"❌ Server responded with status {response.status_code}")
                return False
                
        except Exception as e:
            if not silent:
                print(f"❌ Error checking for updates: {e}")
            return False
    
    def is_newer_version(self, version_a, version_b):
        """Check if version_a is newer than version_b"""
        def parse_version(version):
            return [int(x) for x in version.split('.')]
        
        try:
            a = parse_version(version_a)
            b = parse_version(version_b)
            
            # Pad shorter version with zeros
            max_len = max(len(a), len(b))
            a += [0] * (max_len - len(a))
            b += [0] * (max_len - len(b))
            
            # Compare each component
            for i in range(max_len):
                if a[i] > b[i]:
                    return True
                elif a[i] < b[i]:
                    return False
            
            return False  # Versions are equal
        except (ValueError, AttributeError):
            # Fallback to string comparison if parsing fails
            return version_a > version_b
    
    def download_and_install_update(self, silent=False, force_update=False):
        """Download and install the latest version"""
        if not silent:
            update_type = "forced update" if force_update else "update"
            print(f"📥 Downloading {update_type}...")
            
        try:
            # Download the latest client code
            response = requests.get(
                f"{self.api_base_url}/api/download",
                params={'file': 'client'},
                timeout=60
            )
            
            if response.status_code == 200:
                # Get current script path
                current_script = os.path.abspath(__file__)
                backup_script = current_script + '.backup'
                
                # Create backup of current version
                import shutil
                shutil.copy2(current_script, backup_script)
                
                # Write new version
                with open(current_script, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                if not silent:
                    print("✅ Update installed successfully!")
                    print("🔄 Restarting client...")
                
                # Always restart with the new version (even in silent mode)
                os.execv(sys.executable, [sys.executable] + sys.argv)
                return True
            else:
                if not silent:
                    print(f"❌ Failed to download update: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            if not silent:
                print(f"❌ Error installing update: {e}")
            return False
    
    def start_client(self):
        """Start the notification client"""
        print("🚀 Starting PushNotifications client...")
        
        if not self.api_base_url:
            print("❌ No configuration found. Please run --install first.")
            return False
            
        self.running = True
        
        # Check for updates on startup
        self.check_for_updates(silent=True)
        
        # Register client
        try:
            response = requests.get(
                f"{self.api_base_url}/api",
                params={
                    'action': 'registerClient',
                    'clientId': self.client_id,
                    'clientName': self.client_name,
                    'computerName': self.computer_name
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Client registered successfully")
                else:
                    print(f"⚠️ Registration warning: {result.get('message', 'Unknown error')}")
            else:
                print(f"⚠️ Registration failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Registration error: {e}")
        
        print("✅ Client started successfully!")
        print(f"Monitoring notifications from: {self.api_base_url}")
        print("Press Ctrl+C to stop")
        
        try:
            # Main client loop
            while self.running:
                self.check_notifications()
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\\n⏹️ Client stopped by user")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            self.running = False
            
        return True
    
    def check_notifications(self):
        """Check for new notifications"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api",
                params={
                    'action': 'getClientNotifications',
                    'clientId': self.client_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    notifications = result.get('data', [])
                    for notification in notifications:
                        self.show_notification(notification)
                        
        except Exception as e:
            print(f"Error checking notifications: {e}")
    
    def show_notification(self, notification):
        """Show a notification to the user"""
        print(f"📢 Notification: {notification.get('message', 'No message')}")
        # In a full implementation, you would show a GUI notification here
        # For now, just print to console


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PushNotifications Desktop Client - Vercel/MongoDB Version')
    parser.add_argument('--install', action='store_true', help='Run installation wizard')
    parser.add_argument('--uninstall', action='store_true', help='Run uninstallation process (requires approval)')
    parser.add_argument('--system-integration', action='store_true', help='Enable system integration features')
    parser.add_argument('--setup-autostart', action='store_true', help='Setup automatic startup')
    parser.add_argument('--check-updates', action='store_true', help='Check for updates and install if available')
    parser.add_argument('--version', action='store_true', help='Show version information')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"PushNotifications Desktop Client v{VERSION} (Build: {BUILD_DATE})")
        print("Vercel/MongoDB Version")
        return
        
    client = NotificationClient()
    
    if args.install:
        client.run_installation()
    elif args.check_updates:
        client.check_for_updates(silent=False)
    else:
        # Start normal client operation
        client.start_client()

if __name__ == "__main__":
    main()
`;
}

function getRequirementsContent() {
  return `# PushNotifications Desktop Client Requirements - Vercel/MongoDB Version
requests>=2.31.0

# GUI support (usually included with Python)
# tkinter (built into Python on most systems)

# Optional: For better system integration  
pystray>=0.19.4
pillow>=10.0.0
`;
}

function getReadmeContent() {
  return `# PushNotifications Desktop Client - Vercel/MongoDB Version

A cross-platform desktop notification client that receives push notifications via Vercel API backend with MongoDB database.

## Features

- 🔔 Real-time push notifications with web form styling
- ⚡ Gradient flash effects on screen sides (50% opacity)
- 🎨 Consistent colors and fonts matching the web interface
- 🖥️ Cross-platform support (Windows, macOS, Linux)
- 🔒 Professional notification windows with interactive buttons
- ⚙️ Easy installation and configuration
- 🌐 Vercel API integration with MongoDB backend

## Quick Installation

1. **Download pushnotifications.py** from the PushNotifications web interface
2. **Install Python dependencies:**
   \`\`\`bash
   pip install requests
   \`\`\`
3. **Run installation:**
   \`\`\`bash
   python pushnotifications.py --install
   \`\`\`
4. **Enter your Vercel API URL** when prompted (e.g., https://yourapp.vercel.app)

## Usage

\`\`\`bash
# Run installation wizard
python pushnotifications.py --install

# Start the client
python pushnotifications.py

# Check for updates
python pushnotifications.py --check-updates

# Show version
python pushnotifications.py --version
\`\`\`

## System Requirements

- **Python:** 3.7 or higher
- **Operating System:** Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Internet:** Required for notifications
- **GUI:** tkinter (usually included with Python)

## Configuration

Configuration files are stored in \`~/.pushnotifications/\`:
- \`client_id\` - Unique identifier
- \`client_name\` - Friendly name
- \`config.json\` - Main configuration including Vercel API URL
- \`pushnotifications.log\` - Activity log

## API Integration

The client communicates with your Vercel deployment at:
- Main API: \`https://yourapp.vercel.app/api\`
- Downloads: \`https://yourapp.vercel.app/api/download\`

## License

MIT License - see project repository for details.
`;
}

module.exports = async (req, res) => {
  setCORSHeaders(res);
  
  // Handle OPTIONS preflight request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { file } = req.query;
    let content = '';
    let filename = '';
    let mimeType = 'text/plain';
    
    switch(file) {
      case 'client':
        content = getDesktopClientCode();
        filename = 'pushnotifications.py';
        mimeType = 'text/x-python';
        break;
        
      case 'requirements':
        content = getRequirementsContent();
        filename = 'requirements.txt';
        mimeType = 'text/plain';
        break;
        
      case 'readme':
        content = getReadmeContent();
        filename = 'README.md';
        mimeType = 'text/markdown';
        break;
        
      default:
        return res.status(404).json({
          success: false,
          message: 'File not found'
        });
    }
    
    // Set headers for file download
    res.setHeader('Content-Type', mimeType);
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    return res.send(content);
    
  } catch (error) {
    console.error('Download Error:', error);
    res.status(500).json({
      success: false,
      message: 'Error generating file: ' + error.message
    });
  }
};
