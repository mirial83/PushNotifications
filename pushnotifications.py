#!/usr/bin/env python3
"""
PushNotifications Client with MAC Address Authentication
Runs invisibly in the background and authenticates using MAC address
"""

import json
import time
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import os
import sys
import uuid
import platform
import subprocess
import webbrowser
import ctypes
from urllib.parse import urlparse
import tempfile
import shutil
import socket
import getpass
import re

# Windows-specific imports for system tray
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    HAS_SYSTRAY = True
except ImportError:
    HAS_SYSTRAY = False
    print("Warning: pystray and PIL not available. System tray functionality disabled.")

# Global variables
VERSION = "2.1.0"
CLIENT_ID = None
CLIENT_NAME = None
MAC_ADDRESS = None
USERNAME = None
API_URL = None
CONFIG_FILE = "pushnotifications_config.json"
running = False
tray_icon = None
root = None

def get_mac_address():
    """Get the MAC address of the primary network interface"""
    try:
        # Get MAC address using uuid.getnode()
        mac_num = uuid.getnode()
        mac_hex = ':'.join(f'{(mac_num >> i) & 0xff:02x}' for i in range(0, 48, 8))
        return mac_hex
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return None

def is_admin():
    """Check if running with administrator privileges on Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def restart_as_admin():
    """Restart the script with administrator privileges"""
    if not is_admin():
        print("Restarting with administrator privileges.")
        try:
            # Re-run the current script with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
        except Exception as e:
            print(f"Failed to restart as administrator: {e}")
            return False
    return True

def install_dependencies():
    """Install required PIL and pystray libraries"""
    try:
        import pip
        pip.main(['install', 'pillow', 'pystray'])
        print("Dependencies installed successfully.")
        return True
    except Exception as e:
        try:
            # Try alternative pip installation
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pillow', 'pystray'])
            print("Dependencies installed successfully.")
            return True
        except Exception as e2:
            print(f"Failed to install dependencies: {e2}")
            return False

def load_config():
    """Load configuration from file"""
    global API_URL
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            API_URL = config.get('api_url', '')
        except Exception as e:
            print(f"Error loading config: {e}")
    return config

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_system_info():
    """Get system information"""
    try:
        hostname = socket.gethostname()
        install_path = os.path.abspath(sys.argv[0])
        platform_info = f"{platform.system()} {platform.release()}"
        return hostname, install_path, platform_info
    except Exception as e:
        print(f"Error getting system info: {e}")
        return "unknown", "unknown", "unknown"

def authenticate_with_server():
    """Authenticate with server using MAC address"""
    global CLIENT_ID, CLIENT_NAME, MAC_ADDRESS, USERNAME
    
    if not API_URL:
        return False
    
    try:
        hostname, install_path, platform_info = get_system_info()
        
        # Get username
        if not USERNAME:
            USERNAME = getpass.getuser()
        
        # Authenticate using MAC address
        auth_data = {
            'action': 'authenticateClientByMac',
            'macAddress': MAC_ADDRESS,
            'username': USERNAME,
            'installPath': install_path,
            'platform': platform_info,
            'version': VERSION
        }
        
        response = requests.post(API_URL, json=auth_data, timeout=30)
        result = response.json()
        
        if result.get('success'):
            CLIENT_ID = result.get('clientId')
            CLIENT_NAME = result.get('clientName')
            
            print(f"Authenticated successfully as {CLIENT_NAME} (ID: {CLIENT_ID})")
            
            if result.get('isNewInstallation'):
                print("New installation registered. Previous installations on this MAC address have been deactivated.")
            
            # Update config with authentication details
            config = load_config()
            config.update({
                'client_id': CLIENT_ID,
                'client_name': CLIENT_NAME,
                'mac_address': MAC_ADDRESS,
                'username': USERNAME,
                'last_auth': time.time()
            })
            save_config(config)
            
            return True
        else:
            print(f"Authentication failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def check_for_notifications():
    """Check for notifications from server"""
    if not CLIENT_ID or not API_URL:
        return
    
    try:
        # Update checkin
        checkin_data = {
            'action': 'updateClientMacCheckin',
            'clientId': CLIENT_ID,
            'version': VERSION
        }
        requests.post(API_URL, json=checkin_data, timeout=10)
        
        # Get notifications
        notif_data = {
            'action': 'getClientNotifications',
            'clientId': CLIENT_ID
        }
        
        response = requests.post(API_URL, json=notif_data, timeout=10)
        result = response.json()
        
        if result.get('success'):
            notifications = result.get('data', [])
            for notification in notifications:
                show_notification(notification)
                
    except Exception as e:
        print(f"Error checking notifications: {e}")

def show_notification(notification):
    """Display notification to user"""
    message = notification.get('message', '')
    allow_browser = notification.get('allowBrowserUsage', False)
    allowed_websites = notification.get('allowedWebsites', [])
    
    if not message:
        return
    
    def show_message():
        if root:
            # Show notification window
            notif_window = tk.Toplevel(root)
            notif_window.title("Push Notification")
            notif_window.geometry("400x300")
            notif_window.attributes('-topmost', True)
            
            # Center window
            notif_window.update_idletasks()
            x = (notif_window.winfo_screenwidth() - notif_window.winfo_width()) // 2
            y = (notif_window.winfo_screenheight() - notif_window.winfo_height()) // 2
            notif_window.geometry(f"+{x}+{y}")
            
            # Message label
            msg_label = tk.Label(notif_window, text=message, wraplength=350, justify=tk.LEFT, font=('Arial', 12))
            msg_label.pack(pady=20, padx=20)
            
            # Browser control if applicable
            if allow_browser and allowed_websites:
                browser_frame = tk.Frame(notif_window)
                browser_frame.pack(pady=10)
                
                tk.Label(browser_frame, text="Allowed websites:", font=('Arial', 10, 'bold')).pack()
                
                for website in allowed_websites:
                    website_btn = tk.Button(browser_frame, text=website, 
                                          command=lambda w=website: open_website(w))
                    website_btn.pack(pady=2)
                
                # Request access button
                request_btn = tk.Button(browser_frame, text="Request Website Access", 
                                      command=request_website_access)
                request_btn.pack(pady=10)
            
            # Close button
            close_btn = tk.Button(notif_window, text="Acknowledge", 
                                command=notif_window.destroy, font=('Arial', 10, 'bold'))
            close_btn.pack(pady=20)
            
            # Auto-close after 30 seconds
            notif_window.after(30000, notif_window.destroy)
        else:
            # Fallback to system notification or print
            print(f"Notification: {message}")
    
    if root:
        root.after(0, show_message)
    else:
        print(f"Notification: {message}")

def open_website(website):
    """Open allowed website in default browser"""
    try:
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        webbrowser.open(website)
    except Exception as e:
        print(f"Error opening website: {e}")

def request_website_access():
    """Request access to a new website"""
    if not root:
        return
    
    # Get copied URL from clipboard
    try:
        copied_url = root.clipboard_get()
        if not copied_url or not urlparse(copied_url).netloc:
            copied_url = ""
    except:
        copied_url = ""
    
    # Ask user for website URL
    url = simpledialog.askstring("Website Access Request", 
                                f"Enter website URL to request access to:\n\nCopied URL: {copied_url}",
                                initialvalue=copied_url)
    
    if url:
        print(f"Website access requested for: {url}")
        # Here you would typically send the request to the web form
        messagebox.showinfo("Request Submitted", 
                          f"Access request submitted for:\n{url}\n\nThe administrator will review your request.")

def create_system_tray():
    """Create system tray icon"""
    if not HAS_SYSTRAY:
        return None
    
    # Create tray icon image
    def create_icon_image():
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a simple notification icon
        dc.ellipse([10, 10, width-10, height-10], fill=(0, 120, 200, 255), outline=(0, 80, 160, 255), width=2)
        dc.text((width//2-5, height//2-8), "P", fill=(255, 255, 255, 255))
        
        return image
    
    def on_quit(icon, item):
        global running
        running = False
        icon.stop()
        if root:
            root.quit()
    
    def on_show_status(icon, item):
        status_msg = f"Push Notifications Client\n"
        status_msg += f"Version: {VERSION}\n"
        status_msg += f"Client Name: {CLIENT_NAME or 'Not authenticated'}\n"
        status_msg += f"MAC Address: {MAC_ADDRESS}\n"
        status_msg += f"Status: {'Connected' if CLIENT_ID else 'Disconnected'}"
        
        if root:
            root.after(0, lambda: messagebox.showinfo("Status", status_msg))
    
    menu = pystray.Menu(
        item('Status', on_show_status),
        item('Quit', on_quit)
    )
    
    icon = pystray.Icon("pushnotifications", create_icon_image(), "Push Notifications", menu)
    return icon

def notification_loop():
    """Main notification checking loop"""
    global running
    
    while running:
        try:
            check_for_notifications()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in notification loop: {e}")
            time.sleep(60)  # Wait longer on error

def setup_gui():
    """Setup the GUI (hidden window)"""
    global root
    
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.title("Push Notifications Client")
    
    # Keep the window hidden but available for dialogs
    return root

def get_api_url():
    """Get API URL from user if not configured"""
    global API_URL
    
    if not API_URL:
        # Try to get from command line args or environment
        if len(sys.argv) > 1:
            API_URL = sys.argv[1]
        elif 'PUSHNOTIFICATIONS_API_URL' in os.environ:
            API_URL = os.environ['PUSHNOTIFICATIONS_API_URL']
        else:
            # Default URL from rules
            API_URL = "https://script.google.com/macros/s/AKfycbxz_tUH78XlNqLpdQKqy9SrD6dK6Y0azFIXCM0kUpo3kEfAD6jWoMsngxO710KxTrA/exec"
            print(f"Using default API URL: {API_URL}")
    
    # Save URL for next time
    config = load_config()
    config['api_url'] = API_URL
    save_config(config)

def check_and_install_dependencies():
    """Check and install required dependencies"""
    global HAS_SYSTRAY
    
    if not HAS_SYSTRAY:
        print("Installing required dependencies (PIL and pystray)...")
        if install_dependencies():
            print("Please restart the application to use system tray features.")
        else:
            print("Running without system tray functionality.")

def main():
    """Main function"""
    global running, MAC_ADDRESS, USERNAME, tray_icon
    
    print(f"Starting Push Notifications Client v{VERSION}")
    
    # Check for administrator privileges and restart if needed
    if not restart_as_admin():
        return
    
    # Install dependencies if needed
    check_and_install_dependencies()
    
    # Get MAC address
    MAC_ADDRESS = get_mac_address()
    if not MAC_ADDRESS:
        print("Error: Could not determine MAC address")
        return
    
    print(f"MAC Address: {MAC_ADDRESS}")
    
    # Load configuration
    config = load_config()
    USERNAME = config.get('username', getpass.getuser())
    
    # Get API URL
    get_api_url()
    
    # Setup GUI (hidden)
    if not os.environ.get('NO_GUI'):
        try:
            setup_gui()
        except Exception as e:
            print(f"GUI setup failed: {e}")
    
    # Authenticate with server
    if not authenticate_with_server():
        print("Authentication failed. Exiting.")
        return
    
    # Create system tray icon
    if HAS_SYSTRAY:
        try:
            tray_icon = create_system_tray()
        except Exception as e:
            print(f"System tray setup failed: {e}")
    
    # Start notification loop
    running = True
    
    if tray_icon:
        # Run in system tray mode
        notif_thread = threading.Thread(target=notification_loop, daemon=True)
        notif_thread.start()
        
        print("Running in system tray...")
        tray_icon.run()  # This blocks
    else:
        # Run in console mode
        print("Running in console mode...")
        try:
            notification_loop()
        except KeyboardInterrupt:
            print("\nShutting down...")
            running = False
    
    # Cleanup
    running = False
    print("Client stopped.")

if __name__ == "__main__":
    main()
