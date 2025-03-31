import psutil
import time
import subprocess
import os
from datetime import datetime
import win32gui
import win32process
import win32con
import win32api
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import ImageGrab
import pyautogui
from flask import current_app

def capture_screenshot():
    # Capture the entire screen
    screenshot = ImageGrab.grab()
    # Convert to bytes
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_active_window_info():
    try:
        # Get the handle of the active window
        hwnd = win32gui.GetForegroundWindow()
        # Get the process ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        # Get the process name
        process = psutil.Process(pid)
        return {
            'window_title': win32gui.GetWindowText(hwnd),
            'process_name': process.name(),
            'pid': pid,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting window info: {str(e)}")
        return None

def launch_security_app():
    # Launch the React application
    subprocess.Popen(['npm', 'start'], cwd='../frontend')
    print("Security app launched")

def main():
    print("Starting application monitor...")
    last_check = time.time()
    
    while True:
        try:
            # Check for new applications every 5 seconds
            if time.time() - last_check >= 5:
                window_info = get_active_window_info()
                if window_info:
                    print(f"Active window: {window_info['window_title']}")
                    print(f"Process: {window_info['process_name']}")
                    
                    # Launch security app if it's not already running
                    launch_security_app()
                    
                    # Capture screenshot
                    screenshot_data = capture_screenshot()
                    print("Screenshot captured")
                    
                    # Here you would typically send this information to your backend
                    # for processing and storage
                    
                last_check = time.time()
            
            time.sleep(1)  # Reduce CPU usage
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(5)  # Wait before retrying

class AppMonitor:
    def __init__(self):
        self.screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            return {
                'window_title': win32gui.GetWindowText(hwnd),
                'process_name': process.name(),
                'process_id': pid,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            current_app.logger.error(f"Error getting active window info: {str(e)}")
            return None

    def take_screenshot(self, window_info):
        """Take a screenshot of the current window"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return {
                'filename': filename,
                'filepath': filepath,
                'window_info': window_info
            }
        except Exception as e:
            current_app.logger.error(f"Error taking screenshot: {str(e)}")
            return None

    def monitor_application(self, process_name):
        """Monitor a specific application and take screenshots when it's active"""
        try:
            window_info = self.get_active_window_info()
            if window_info and window_info['process_name'].lower() == process_name.lower():
                return self.take_screenshot(window_info)
            return None
        except Exception as e:
            current_app.logger.error(f"Error monitoring application: {str(e)}")
            return None

if __name__ == "__main__":
    main() 