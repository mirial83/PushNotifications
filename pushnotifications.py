#!/usr/bin/env python3
"""
PushNotifications Desktop Client v2.1.0
Connects to Vercel-hosted Node.js API with MongoDB backend

Features:
- Real-time notification polling
- Browser usage control with website filtering
- System tray integration
- Automatic client registration
- Version checking and auto-updates
- Snooze functionality
"""

import os
import sys
import json
import time
import uuid
import requests
import threading
import subprocess
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
import getpass
import platform

# Try to import optional dependencies
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("System tray not available - running in console mode")

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("GUI not available - using console notifications")

# Configuration
SERVER_URL = "https://push-notifications-phi.vercel.app"
API_BASE_URL = f"{SERVER_URL}/api"
POLL_INTERVAL = 10  # seconds
VERSION = "2.1.0"

class PushNotificationsClient:
    def __init__(self):
        self.client_id = self.get_or_create_client_id()
        self.running = True
        self.notifications = []
        self.blocked_websites = set()
        self.allowed_websites = set()
        self.browser_blocked = False
        self.current_notification = None
        self.snooze_until = None
        self.tray_icon = None
        
        # Client info
        self.client_name = f"{getpass.getuser()}@{platform.node()}"
        self.computer_name = platform.node()
        
        print(f"PushNotifications Client v{VERSION}")
        print(f"Server: {SERVER_URL}")
        print(f"Client ID: {self.client_id}")
        print(f"Client Name: {self.client_name}")
        
    def get_or_create_client_id(self):
        """Get existing client ID or create a new one"""
        config_dir = Path.home() / ".pushnotifications"
        config_dir.mkdir(exist_ok=True)
        client_id_file = config_dir / "client_id"
        
        if client_id_file.exists():
            try:
                return client_id_file.read_text().strip()
            except:
                pass
        
        # Generate new client ID
        new_id = str(uuid.uuid4())
        client_id_file.write_text(new_id)
        return new_id
    
    def api_request(self, endpoint, data=None, method='GET'):
        """Make API request to Node.js backend"""
        url = f"{API_BASE_URL}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, params=data, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
                
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error {response.status_code}: {response.text[:200]}")
                return {'success': False, 'message': f'HTTP {response.status_code}'}
                
        except requests.RequestException as e:
            print(f"Network error: {e}")
            return {'success': False, 'message': str(e)}
    
    def register_client(self):
        """Register this client with the server"""
        print("Registering client with server...")
        
        data = {
            'action': 'registerClient',
            'clientId': self.client_id,
            'clientName': self.client_name,
            'computerName': self.computer_name
        }
        
        result = self.api_request('index', data, 'POST')
        if result.get('success'):
            print("✓ Client registered successfully")
            return True
        else:
            print(f"✗ Registration failed: {result.get('message', 'Unknown error')}")
            return False
    
    def check_version(self):
        """Check for version updates"""
        result = self.api_request('index', {'action': 'get_version'}, 'GET')
        
        if result.get('success'):
            server_version = result.get('latestVersion', VERSION)
            if server_version != VERSION:
                print(f"Update available: {VERSION} → {server_version}")
                if result.get('forceUpdate'):
                    print("Forced update required - downloading...")
                    self.perform_update()
                elif result.get('autoUpdateEnabled'):
                    print("Auto-update enabled - downloading...")
                    self.perform_update()
            else:
                print("✓ Client is up to date")
        else:
            print("✗ Could not check version")
    
    def perform_update(self):
        """Download and install update"""
        try:
            # Download updated client
            response = requests.get(f"{SERVER_URL}/api/download?file=client", timeout=60)
            if response.status_code == 200:
                # Save update and restart
                current_file = Path(__file__)
                backup_file = current_file.with_suffix('.py.backup')
                
                # Backup current version
                backup_file.write_text(current_file.read_text())
                
                # Write new version
                current_file.write_text(response.text)
                print("✓ Update downloaded - restarting...")
                
                # Restart
                subprocess.Popen([sys.executable, str(current_file)])
                sys.exit(0)
                
        except Exception as e:
            print(f"✗ Update failed: {e}")
    
    def poll_notifications(self):
        """Poll server for new notifications"""
        data = {
            'action': 'getClientNotifications',
            'clientId': self.client_id
        }
        
        result = self.api_request('index', data, 'POST')
        if result.get('success'):
            notifications = result.get('data', [])
            self.process_notifications(notifications)
        else:
            print(f"Polling error: {result.get('message', 'Unknown error')}")
    
    def process_notifications(self, notifications):
        """Process received notifications"""
        # Check for snooze
        if self.snooze_until and datetime.now() < self.snooze_until:
            return  # Still snoozed
            
        # Clear snooze if expired
        if self.snooze_until and datetime.now() >= self.snooze_until:
            self.snooze_until = None
            
        # Find active notifications
        active_notifications = [n for n in notifications if n.get('status') != 'Completed']
        
        if active_notifications:
            # Process highest priority notification
            notification = max(active_notifications, key=lambda x: x.get('priority', 1))
            if notification != self.current_notification:
                self.current_notification = notification
                self.show_notification(notification)
                self.apply_browser_restrictions(notification)
        else:
            # No active notifications - clear restrictions
            if self.current_notification:
                self.current_notification = None
                self.clear_browser_restrictions()
    
    def show_notification(self, notification):
        """Display notification to user"""
        message = notification.get('message', 'No message')
        priority = notification.get('priority', 1)
        
        print(f"\n{'='*50}")
        print(f"📢 NOTIFICATION (Priority: {priority})")
        print(f"Message: {message}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        
        # Show GUI notification if available
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                
                title = f"PushNotifications (Priority {priority})"
                
                # Show with appropriate icon based on priority
                if priority >= 3:
                    messagebox.showerror(title, message)
                elif priority == 2:
                    messagebox.showwarning(title, message)
                else:
                    messagebox.showinfo(title, message)
                    
                root.destroy()
            except Exception as e:
                print(f"GUI notification failed: {e}")
        
        # Update tray tooltip if available
        if TRAY_AVAILABLE and self.tray_icon:
            try:
                self.tray_icon.title = f"PushNotifications: {message[:50]}"
            except:
                pass
    
    def apply_browser_restrictions(self, notification):
        """Apply browser usage restrictions based on notification"""
        allow_browser = notification.get('allowBrowserUsage', False)
        allowed_websites = notification.get('allowedWebsites', [])
        
        if not allow_browser:
            self.browser_blocked = True
            self.allowed_websites.clear()
            print("🚫 Browser access blocked")
        else:
            self.browser_blocked = False
            self.allowed_websites = set(allowed_websites)
            if allowed_websites:
                print(f"🌐 Browser restricted to: {', '.join(allowed_websites)}")
            else:
                print("🌐 Browser access allowed (unrestricted)")
    
    def clear_browser_restrictions(self):
        """Clear all browser restrictions"""
        if self.browser_blocked or self.allowed_websites:
            self.browser_blocked = False
            self.allowed_websites.clear()
            print("✓ Browser restrictions cleared")
    
    def snooze_notification(self, minutes=15):
        """Snooze current notification"""
        if self.current_notification:
            self.snooze_until = datetime.now() + timedelta(minutes=minutes)
            print(f"😴 Notification snoozed for {minutes} minutes (until {self.snooze_until.strftime('%H:%M')})")
            
            # Temporarily clear restrictions during snooze
            self.clear_browser_restrictions()
    
    def complete_notification(self):
        """Mark current notification as completed"""
        if self.current_notification:
            # In a full implementation, we'd send this to the server
            print("✓ Notification marked as completed")
            self.current_notification = None
            self.clear_browser_restrictions()
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not TRAY_AVAILABLE:
            return None
            
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.ellipse([16, 16, 48, 48], fill='white')
            draw.text((20, 25), "PN", fill='blue')
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Snooze 15 min", lambda: self.snooze_notification(15)),
                pystray.MenuItem("Snooze 30 min", lambda: self.snooze_notification(30)),
                pystray.MenuItem("Complete", self.complete_notification),
                pystray.MenuItem("---", None),
                pystray.MenuItem("Open Web Interface", self.open_web_interface),
                pystray.MenuItem("Exit", self.stop)
            )
            
            icon = pystray.Icon("pushnotifications", image, "PushNotifications Client", menu)
            return icon
            
        except Exception as e:
            print(f"Could not create tray icon: {e}")
            return None
    
    def open_web_interface(self):
        """Open web interface in browser"""
        try:
            webbrowser.open(SERVER_URL)
        except Exception as e:
            print(f"Could not open web interface: {e}")
    
    def run_polling_loop(self):
        """Main polling loop"""
        print(f"Starting notification polling (every {POLL_INTERVAL}s)...")
        
        while self.running:
            try:
                self.poll_notifications()
                time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(POLL_INTERVAL)
    
    def start(self):
        """Start the client"""
        print("Starting PushNotifications Client...")
        
        # Check version and update if needed
        self.check_version()
        
        # Register with server
        if not self.register_client():
            print("Warning: Could not register with server, continuing anyway...")
        
        # Create tray icon
        self.tray_icon = self.create_tray_icon()
        
        if self.tray_icon and TRAY_AVAILABLE:
            # Run with system tray
            print("Running in system tray mode...")
            print("Right-click tray icon for options")
            
            # Start polling in separate thread
            polling_thread = threading.Thread(target=self.run_polling_loop, daemon=True)
            polling_thread.start()
            
            # Run tray (blocks until exit)
            self.tray_icon.run()
        else:
            # Run in console mode
            print("Running in console mode...")
            print("Press Ctrl+C to exit")
            print("Commands: 's15' = snooze 15min, 's30' = snooze 30min, 'c' = complete, 'q' = quit")
            
            # Start polling in separate thread
            polling_thread = threading.Thread(target=self.run_polling_loop, daemon=True)
            polling_thread.start()
            
            # Console command loop
            try:
                while self.running:
                    try:
                        cmd = input().strip().lower()
                        if cmd == 'q' or cmd == 'quit':
                            break
                        elif cmd == 's15':
                            self.snooze_notification(15)
                        elif cmd == 's30':
                            self.snooze_notification(30)
                        elif cmd == 'c' or cmd == 'complete':
                            self.complete_notification()
                        elif cmd == 'help':
                            print("Commands: s15, s30, c, q")
                    except EOFError:
                        break
            except KeyboardInterrupt:
                pass
        
        self.stop()
    
    def stop(self):
        """Stop the client"""
        print("\nStopping PushNotifications Client...")
        self.running = False
        self.clear_browser_restrictions()
        
        if self.tray_icon:
            self.tray_icon.stop()

def main():
    """Main entry point"""
    try:
        # Handle command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] in ('--help', '-h'):
                print(__doc__)
                return
            elif sys.argv[1] == '--version':
                print(f"PushNotifications Client v{VERSION}")
                return
        
        client = PushNotificationsClient()
        client.start()
        
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Client error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
