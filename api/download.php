<?php
// File download endpoint for PushNotifications

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$file = $_GET['file'] ?? '';

switch ($file) {
    case 'client':
        header('Content-Type: text/plain');
        header('Content-Disposition: attachment; filename="pushnotifications.py"');
        echo getPythonClientCode();
        break;
        
    case 'requirements':
        header('Content-Type: text/plain');
        header('Content-Disposition: attachment; filename="requirements.txt"');
        echo getRequirementsContent();
        break;
        
    case 'readme':
        header('Content-Type: text/plain');
        header('Content-Disposition: attachment; filename="README.md"');
        echo getReadmeContent();
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'File not found']);
        break;
}

function getPythonClientCode() {
    $serverUrl = $_ENV['VERCEL_URL'] ?? $_SERVER['HTTP_HOST'] ?? 'your-project.vercel.app';
    if (!str_starts_with($serverUrl, 'http')) {
        $serverUrl = 'https://' . $serverUrl;
    }
    
    return '#!/usr/bin/env python3
"""
PushNotifications Desktop Client
Vercel + MongoDB Version

This client connects to the Vercel-hosted API and MongoDB backend
to receive push notifications and manage system interactions.
"""

import requests
import time
import json
import sys
import os
import uuid
import platform
import subprocess
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import webbrowser
from urllib.parse import urlparse
import tempfile
import shutil

class PushNotificationsClient:
    def __init__(self):
        self.server_url = "' . $serverUrl . '"
        self.client_id = self.get_or_create_client_id()
        self.client_name = f"{platform.node()}-{self.client_id[:8]}"
        self.computer_name = platform.node()
        self.version = "2.1.0"
        self.running = False
        self.check_interval = 30  # seconds
        
    def get_or_create_client_id(self):
        """Get existing client ID or create a new one"""
        config_file = os.path.expanduser("~/.pushnotifications_client_id")
        try:
            with open(config_file, \'r\') as f:
                return f.read().strip()
        except FileNotFoundError:
            client_id = str(uuid.uuid4())
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, \'w\') as f:
                f.write(client_id)
            return client_id
    
    def api_call(self, action, data=None):
        """Make API call to the server"""
        try:
            url = f"{self.server_url}/api/index.php"
            
            if data is None:
                data = {}
            data[\'action\'] = action
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            return {\'success\': False, \'message\': str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {\'success\': False, \'message\': \'Invalid server response\'}
    
    def register_client(self):
        """Register this client with the server"""
        result = self.api_call(\'registerClient\', {
            \'clientId\': self.client_id,
            \'clientName\': self.client_name,
            \'computerName\': self.computer_name
        })
        
        if result.get(\'success\'):
            print(f"Client registered: {result.get(\'message\', \'\')}")
        else:
            print(f"Client registration failed: {result.get(\'message\', \'Unknown error\')}")
        
        return result.get(\'success\', False)
    
    def check_for_updates(self):
        """Check if client needs to be updated"""
        result = self.api_call(\'get_version\')
        
        if not result.get(\'success\'):
            return False
            
        server_version = result.get(\'latestVersion\', self.version)
        force_update = result.get(\'forceUpdate\', False)
        
        if server_version != self.version:
            print(f"Update available: {self.version} -> {server_version}")
            
            if force_update:
                print("Forced update required. Updating...")
                return self.perform_update()
            else:
                # Optional update - ask user
                root = tk.Tk()
                root.withdraw()
                
                update = messagebox.askyesno(
                    "Update Available",
                    f"A new version is available ({server_version}).\\nWould you like to update now?"
                )
                
                root.destroy()
                
                if update:
                    return self.perform_update()
        
        return True
    
    def perform_update(self):
        """Download and install update"""
        try:
            print("Downloading update...")
            
            # Download new version
            response = requests.get(f"{self.server_url}/api/download.php?file=client", timeout=60)
            response.raise_for_status()
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(mode=\'w\', suffix=\'.py\', delete=False)
            temp_file.write(response.text)
            temp_file.close()
            
            # Replace current file
            current_file = sys.argv[0]
            shutil.move(temp_file.name, current_file)
            
            print("Update completed. Restarting...")
            
            # Restart the application
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def get_notifications(self):
        """Get notifications for this client"""
        result = self.api_call(\'getClientNotifications\', {
            \'clientId\': self.client_id
        })
        
        if result.get(\'success\'):
            return result.get(\'data\', [])
        else:
            print(f"Failed to get notifications: {result.get(\'message\', \'Unknown error\')}")
            return []
    
    def show_notification(self, notification):
        """Display notification to user"""
        root = tk.Tk()
        root.title("PushNotifications")
        root.geometry("400x300")
        root.resizable(False, False)
        
        # Make window stay on top
        root.attributes(\'-topmost\', True)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (400 // 2)
        y = (root.winfo_screenheight() // 2) - (300 // 2)
        root.geometry(f"+{x}+{y}")
        
        # Message content
        message_frame = tk.Frame(root, padx=20, pady=20)
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(message_frame, text="New Notification", 
                              font=(\'Arial\', 14, \'bold\'))
        title_label.pack(pady=(0, 10))
        
        message_label = tk.Label(message_frame, text=notification[\'message\'], 
                                font=(\'Arial\', 12), wraplength=350, justify=tk.LEFT)
        message_label.pack(pady=(0, 20))
        
        # Priority indicator
        priority = notification.get(\'priority\', 1)
        priority_text = [\'Low\', \'Normal\', \'High\', \'Urgent\'][min(priority, 3)]
        priority_label = tk.Label(message_frame, text=f"Priority: {priority_text}", 
                                 font=(\'Arial\', 10))
        priority_label.pack()
        
        # Browser usage info
        if notification.get(\'allowBrowserUsage\'):
            browser_label = tk.Label(message_frame, text="Browser usage allowed", 
                                   fg=\'green\', font=(\'Arial\', 10))
            browser_label.pack()
            
            websites = notification.get(\'allowedWebsites\', [])
            if websites:
                sites_text = "Allowed sites: " + ", ".join(websites[:3])
                if len(websites) > 3:
                    sites_text += f" (+{len(websites)-3} more)"
                sites_label = tk.Label(message_frame, text=sites_text, 
                                     font=(\'Arial\', 9), wraplength=350)
                sites_label.pack()
        else:
            browser_label = tk.Label(message_frame, text="Browser usage blocked", 
                                   fg=\'red\', font=(\'Arial\', 10))
            browser_label.pack()
        
        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))
        
        def acknowledge():
            root.destroy()
            self.acknowledge_notification(notification[\'id\'])
        
        def snooze():
            root.destroy()
            self.snooze_notification(notification[\'id\'])
        
        ack_button = tk.Button(button_frame, text="Got it!", command=acknowledge, 
                              bg=\'#4CAF50\', fg=\'white\', font=(\'Arial\', 12, \'bold\'))
        ack_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        snooze_button = tk.Button(button_frame, text="Snooze 15m", command=snooze,
                                 bg=\'#FF9800\', fg=\'white\', font=(\'Arial\', 12))
        snooze_button.pack(side=tk.RIGHT)
        
        # Handle window close
        def on_closing():
            # Don\'t allow closing without action for high priority notifications
            if priority >= 3:
                messagebox.showwarning("Action Required", 
                                     "This is a high priority notification that requires acknowledgment.")
            else:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Show the window
        root.mainloop()
    
    def acknowledge_notification(self, notification_id):
        """Mark notification as completed"""
        result = self.api_call(\'updateNotificationStatus\', {
            \'notificationId\': notification_id,
            \'status\': \'Completed\'
        })
        
        if result.get(\'success\'):
            print(f"Notification {notification_id} acknowledged")
        else:
            print(f"Failed to acknowledge notification: {result.get(\'message\', \'Unknown error\')}")
    
    def snooze_notification(self, notification_id, minutes=15):
        """Snooze notification for specified minutes"""
        result = self.api_call(\'updateNotificationStatus\', {
            \'notificationId\': notification_id,
            \'status\': \'Snoozed\',
            \'snoozeMinutes\': minutes
        })
        
        if result.get(\'success\'):
            print(f"Notification {notification_id} snoozed for {minutes} minutes")
        else:
            print(f"Failed to snooze notification: {result.get(\'message\', \'Unknown error\')}")
    
    def run(self):
        """Main client loop"""
        print(f"Starting PushNotifications Client v{self.version}")
        print(f"Client ID: {self.client_id}")
        print(f"Server: {self.server_url}")
        
        # Register client
        if not self.register_client():
            print("Failed to register client. Retrying in 60 seconds...")
            time.sleep(60)
        
        # Check for updates
        if not self.check_for_updates():
            print("Update check failed, continuing with current version...")
        
        self.running = True
        
        try:
            while self.running:
                try:
                    # Get notifications
                    notifications = self.get_notifications()
                    
                    # Show each notification
                    for notification in notifications:
                        print(f"Showing notification: {notification[\'message\'][:50]}...")
                        self.show_notification(notification)
                    
                    # Wait before next check
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    print("\\nShutdown requested...")
                    self.running = False
                except Exception as e:
                    print(f"Error in main loop: {e}")
                    time.sleep(self.check_interval)
                    
        except Exception as e:
            print(f"Fatal error: {e}")
        
        print("Client stopped.")

def main():
    """Main entry point"""
    try:
        client = PushNotificationsClient()
        client.run()
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
';
}

function getRequirementsContent() {
    return 'requests>=2.25.0
tkinter
';
}

function getReadmeContent() {
    return '# PushNotifications Desktop Client

## Installation

1. Install Python 3.7 or later
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the client:
   ```
   python pushnotifications.py
   ```

## Features

- Automatic client registration
- Real-time notification display
- Browser usage control
- Website filtering
- Automatic updates (forced when configured)
- Snooze functionality
- Priority-based notifications

## Configuration

The client automatically configures itself and connects to the server.
No manual configuration is required.

## Troubleshooting

- Ensure you have an internet connection
- Check that Python and required packages are installed
- Contact your administrator if you encounter persistent issues
';
}

?>
