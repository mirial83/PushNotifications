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
        """Load client configuration from config.json"""
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
            
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
            pystray.MenuItem("View Current Notification", self._view_notification),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Snooze", pystray.Menu(
                pystray.MenuItem("5 minutes", lambda: self._snooze(5)),
                pystray.MenuItem("15 minutes", lambda: self._snooze(15)),
                pystray.MenuItem("30 minutes", lambda: self._snooze(30))
            ), enabled=lambda: not self.snooze_used and bool(self.notifications)),
            pystray.MenuItem("Request Website Access", self._request_website),
            pystray.MenuItem("Complete Current Notification", 
                           self._complete_notification,
                           enabled=lambda: bool(self.notifications)),
            pystray.Menu.SEPARATOR,
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

    def _view_notification(self):
        """Show the current notification message"""
        if not self.notifications:
            messagebox.showinfo("No Notifications", 
                              "There are no active notifications.")
            return
            
        notif = self.notifications[0]
        messagebox.showinfo("Current Notification",
                          notif.get('message', 'No message available'))

    def _snooze(self, minutes):
        """Snooze notifications for specified minutes"""
        if self.snooze_used:
            messagebox.showwarning("Snooze Unavailable",
                                 "Snooze has already been used.")
            return
            
        self.snooze_until = time.time() + (minutes * 60)
        self.snooze_used = True
        
        # Update menu items
        self.icon.update_menu()
        
        messagebox.showinfo("Notifications Snoozed",
                          f"Notifications snoozed for {minutes} minutes")

    def _request_website(self):
        """Request access to a website"""
        website = simpledialog.askstring("Website Access Request",
                                       "Enter the website URL you would like to access:")
        if not website:
            return
            
        try:
            response = requests.post(
                f"{self.config['api_url']}/api/request-website",
                json={
                    'client_id': self.config['client_id'],
                    'website': website
                },
                timeout=10
            )
            
            if response.ok:
                messagebox.showinfo("Request Sent",
                                  "Website access request has been submitted for approval.")
            else:
                messagebox.showerror("Request Failed",
                                   "Failed to submit website access request.")
                                   
        except Exception as e:
            logger.error(f"Failed to request website access: {e}")
            messagebox.showerror("Error",
                               "Failed to submit website access request. Please try again later.")

    def _complete_notification(self):
        """Mark the current notification as completed"""
        if not self.notifications:
            return
            
        try:
            notif = self.notifications[0]
            response = requests.post(
                f"{self.config['api_url']}/api/complete-notification",
                json={
                    'client_id': self.config['client_id'],
                    'notification_id': notif['id']
                },
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
            logger.error(f"Failed to complete notification: {e}")
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
                f"{self.config['api_url']}/api/request-uninstall",
                json={
                    'client_id': self.config['client_id'],
                    'mac_address': self.config.get('mac_address', ''),
                    'install_path': self.config.get('install_path', ''),
                    'key_id': self.config.get('key_id', ''),
                    'reason': reason,
                    'explanation': explanation
                },
                timeout=10
            )
            
            if response.ok:
                result = response.json()
                if result.get('autoApproved'):
                    # Request was auto-approved (client not found in database)
                    if messagebox.askyesno("Uninstall Approved",
                                         "Your uninstall request has been automatically approved. \n\nWould you like to uninstall now?"):
                        self._perform_uninstall()
                else:
                    # Request needs admin approval
                    messagebox.showinfo(
                        "Request Sent",
                        "Your uninstall request has been submitted for approval.\n\n" 
                        "The application will continue running until the request is approved.\n\n" 
                        "You will be notified when a decision is made."
                    )
            else:
                messagebox.showerror("Request Failed",
                                   "Failed to submit uninstall request.")
                                   
        except Exception as e:
            logger.error(f"Failed to request uninstall: {e}")
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
                f"rmdir /s /q \"{self.config.get('install_path', '')}\"\n"
            )
            
            script_path = os.path.join(os.environ['TEMP'], 'uninstall.bat')
            with open(script_path, 'w') as f:
                f.write(uninstall_script)
                
            # Execute uninstall script and exit
            os.startfile(script_path)
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Failed to perform uninstall: {e}")
            messagebox.showerror("Error",
                               "Failed to uninstall. Please try again later or contact support.")
            return False

    def _quit(self):
        """Clean shutdown of the application"""
        self.running = False
        self.icon.stop()

    def run(self):
        """Main client run loop"""
        try:
            # Create and run system tray icon
            icon = self.create_tray_icon()
            icon.run()
        except Exception as e:
            logger.error(f"Client error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start client
    client = PushNotificationsClient()
    client.run()
