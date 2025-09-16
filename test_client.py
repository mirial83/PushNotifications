#!/usr/bin/env python3
"""
Test client to diagnose system tray and process issues
"""

import os
import sys
import time
import threading
from pathlib import Path

print("Starting test client...")

# Hide console window on Windows
if os.name == 'nt':
    try:
        import ctypes
        # Hide the console window
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        # Set proper process title
        ctypes.windll.kernel32.SetConsoleTitleW("PushNotifications Test Client")
    except Exception as e:
        print(f"Warning: Could not hide console: {e}")

# Install required packages
required_packages = ['pystray', 'Pillow', 'requests']

print("Installing required packages...")
for package in required_packages:
    try:
        __import__(package if package != 'Pillow' else 'PIL')
        print(f"✓ {package} already installed")
    except ImportError:
        print(f"Installing {package}...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode == 0:
                print(f"✓ {package} installed successfully")
            else:
                print(f"✗ Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"✗ Installation error for {package}: {e}")

# Now try to create tray icon
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    import tkinter as tk
    from tkinter import messagebox
    
    class TestClient:
        def __init__(self):
            self.running = True
            
        def create_tray_icon(self):
            """Create a simple test tray icon"""
            def create_image():
                # Create a simple blue circle icon
                width = height = 64
                image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
                dc = ImageDraw.Draw(image)
                dc.ellipse([8, 8, width-8, height-8], fill='#007bff', outline='#0056b3', width=2)
                dc.text((width//2-10, height//2-8), "TC", fill='white')  # Test Client
                return image
            
            def show_status(icon, item):
                """Show status message"""
                try:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo("Test Client", "Test client is running successfully!")
                    root.destroy()
                except Exception as e:
                    print(f"Error showing status: {e}")
            
            def quit_app(icon, item):
                """Quit the application"""
                print("Quitting test client...")
                self.running = False
                icon.stop()
            
            # Create menu
            menu = pystray.Menu(
                item('Show Status', show_status),
                item('Quit', quit_app)
            )
            
            # Create and return icon
            return pystray.Icon("TestClient", create_image(), "Test Client", menu)
        
        def run(self):
            """Main application loop"""
            print("Creating system tray icon...")
            
            try:
                tray_icon = self.create_tray_icon()
                print("✓ Tray icon created successfully")
                
                # Start background thread to keep app running
                def background_thread():
                    while self.running:
                        time.sleep(1)
                
                bg_thread = threading.Thread(target=background_thread, daemon=True)
                bg_thread.start()
                
                print("✓ Starting tray icon (should appear in system tray)")
                print("✓ Process should now be visible in Task Manager as 'PushNotifications Test Client'")
                
                # This blocks until quit is called
                tray_icon.run()
                
            except Exception as e:
                print(f"✗ Error running tray icon: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback: console mode
                print("Running in console mode instead...")
                while self.running:
                    time.sleep(1)
    
    # Run the test client
    client = TestClient()
    client.run()
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Required packages not available - running in basic mode")
    
    # Basic console mode
    print("Test client running in console mode...")
    print("This should NOT show two terminals!")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Test client stopped")

except Exception as e:
    print(f"✗ Fatal error: {e}")
    import traceback
    traceback.print_exc()

print("Test client finished.")
