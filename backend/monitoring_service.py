import threading
import time
from app_monitor import AppMonitor
from flask import current_app
from datetime import datetime
import json
import os

class MonitoringService:
    def __init__(self):
        self.app_monitor = AppMonitor()
        self.monitoring_thread = None
        self.is_running = False
        self.monitored_apps = set()
        self.screenshot_log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshot_log.json')

    def start_monitoring(self, process_names):
        """Start monitoring specified applications"""
        if not self.is_running:
            self.monitored_apps = set(process_names)
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            current_app.logger.info(f"Started monitoring applications: {process_names}")

    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        current_app.logger.info("Stopped monitoring service")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            for process_name in self.monitored_apps:
                try:
                    screenshot_info = self.app_monitor.monitor_application(process_name)
                    if screenshot_info:
                        self._log_screenshot(screenshot_info)
                except Exception as e:
                    current_app.logger.error(f"Error monitoring {process_name}: {str(e)}")
            time.sleep(1)  # Check every second

    def _log_screenshot(self, screenshot_info):
        """Log screenshot information to a JSON file"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'filename': screenshot_info['filename'],
                'window_info': screenshot_info['window_info']
            }

            # Read existing log
            if os.path.exists(self.screenshot_log_file):
                with open(self.screenshot_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new log
            logs.append(log_data)

            # Write updated log
            with open(self.screenshot_log_file, 'w') as f:
                json.dump(logs, f, indent=2)

            current_app.logger.info(f"Screenshot taken: {screenshot_info['filename']}")
        except Exception as e:
            current_app.logger.error(f"Error logging screenshot: {str(e)}")

    def get_screenshot_logs(self):
        """Retrieve screenshot logs"""
        try:
            if os.path.exists(self.screenshot_log_file):
                with open(self.screenshot_log_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            current_app.logger.error(f"Error reading screenshot logs: {str(e)}")
            return [] 