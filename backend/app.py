from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import hdbcli.dbapi
from dotenv import load_dotenv
import os
import cv2
import numpy as np
from datetime import datetime
import base64
import json
from io import BytesIO
import pyautogui
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from monitoring_service import MonitoringService
import requests
import win32gui
import win32process
import psutil
import subprocess
import time
from threading import Thread
import threading
from models import db, Notification, SecurityAlert

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize monitoring service
monitoring_service = MonitoringService()

# Security Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAX_LOGIN_ATTEMPTS'] = int(os.getenv('MAX_LOGIN_ATTEMPTS', 3))

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

# JWT Configuration
jwt = JWTManager(app)

# Database Configuration
DB_CONFIG = {
    'address': os.getenv('DB_ADDRESS'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_db_connection():
    try:
        conn = hdbcli.dbapi.connect(
            address=os.getenv('DB_ADDRESS'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        print("Successfully connected to HANA database")
        return conn
    except Exception as e:
        print(f"HANA Database connection error: {str(e)}")
        return None

def test_db_connection():
    """Test database connection and table structure"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Check if USERS table exists and its structure using HANA system views
            cursor.execute("SELECT COLUMN_NAME, DATA_TYPE_NAME FROM TABLE_COLUMNS WHERE TABLE_NAME = 'USERS' AND SCHEMA_NAME = CURRENT_SCHEMA")
            columns = cursor.fetchall()
            print("\nUSERS table structure:")
            if columns:
                for col in columns:
                    print(f"Column: {col[0]}, Type: {col[1]}")
            else:
                print("No columns found. Creating USERS table...")
                # Create USERS table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE USERS (
                        USERNAME NVARCHAR(100) PRIMARY KEY,
                        PASSWORD NVARCHAR(100) NOT NULL,
                        EMAIL NVARCHAR(100) NOT NULL
                    )
                """)
                conn.commit()
                print("USERS table created successfully")
            
            # Check existing users
            cursor.execute("SELECT USERNAME, EMAIL FROM USERS")
            users = cursor.fetchall()
            print("\nExisting users:")
            for user in users:
                print(f"Username: {user[0]}, Email: {user[1]}")
            
            return True
        except Exception as e:
            print(f"Database test error: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def init_db():
    with app.app_context():
        try:
            # Test database connection and create tables if needed
            if test_db_connection():
                print("Database initialization successful")
                # Create LOGIN_ATTEMPTS table if it doesn't exist
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        # First check if table exists
                        cursor.execute("""
                            SELECT COUNT(*) FROM TABLES 
                            WHERE TABLE_NAME = 'LOGIN_ATTEMPTS'
                        """)
                        table_exists = cursor.fetchone()[0] > 0

                        if not table_exists:
                            cursor.execute("""
                                CREATE TABLE LOGIN_ATTEMPTS (
                                    ID INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                                    USERNAME NVARCHAR(100) NOT NULL,
                                    SUCCESS BOOLEAN NOT NULL,
                                    IP_ADDRESS NVARCHAR(45),
                                    TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            """)
                            conn.commit()
                            print("LOGIN_ATTEMPTS table created successfully")
                    except Exception as e:
                        print(f"Error creating LOGIN_ATTEMPTS table: {str(e)}")
                    finally:
                        cursor.close()
                        conn.close()
            else:
                print("Database initialization failed")
        except Exception as e:
            print(f"Database initialization error: {str(e)}")

@app.route('/api/login', methods=['POST', 'OPTIONS'])
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    print(f"\nLogin attempt:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    
    if not all([username, password]):
        print("Missing credentials")
        return jsonify({'error': 'Missing credentials'}), 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Get user from database
            cursor.execute('SELECT USERNAME, PASSWORD, EMAIL FROM USERS WHERE USERNAME = ?', (username,))
            user = cursor.fetchone()
            
            if user:
                stored_username = user[0]
                stored_password = user[1]
                stored_email = user[2]
                
                print("Credential comparison:")
                print(f"Stored username: {stored_username}")
                print(f"Input username: {username}")
                print(f"Stored password: {stored_password}")
                print(f"Input password: {password}")
                
                if stored_password == password:
                    print("Login successful - Passwords match")
                    access_token = create_access_token(identity=username)
                    response = jsonify({
                        'token': access_token,
                        'email': stored_email,
                        'message': 'Login successful'
                    })
                    return response, 200
                else:
                    print("Login failed - Password mismatch")
                    # Get failed attempts count
                    cursor.execute('SELECT COUNT(*) FROM LOGIN_ATTEMPTS WHERE USERNAME = ? AND SUCCESS = FALSE', (username,))
                    failed_attempts = cursor.fetchone()[0]
                    remaining_attempts = 3 - failed_attempts
                    
                    # Record failed attempt
                    cursor.execute('INSERT INTO LOGIN_ATTEMPTS (USERNAME, SUCCESS, IP_ADDRESS) VALUES (?, FALSE, ?)',
                                 (username, request.remote_addr))
                    conn.commit()
                    
                    if remaining_attempts <= 0:
                        # Send security alert
                        send_security_alert(username, request.remote_addr, capture_screenshot())
                        return jsonify({
                            'error': 'Account locked due to too many failed attempts',
                            'message': 'Account locked. A security alert has been sent.',
                            'remaining_attempts': 0
                        }), 429
                    
                    return jsonify({
                        'error': 'Invalid credentials',
                        'message': 'Password is incorrect',
                        'remaining_attempts': remaining_attempts,
                        'is_last_attempt': remaining_attempts == 1
                    }), 401
            else:
                print(f"Login failed - No user found with username: {username}")
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Username not found'
                }), 401
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    print(f"\nRegistration attempt:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    
    if not all([username, password, email]):
        print("Missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Check if username exists
            cursor.execute('SELECT USERNAME FROM USERS WHERE USERNAME = ?', (username,))
            if cursor.fetchone():
                print(f"Username already exists: {username}")
                return jsonify({'error': 'Username already exists'}), 400
            
            # Insert new user
            cursor.execute(
                'INSERT INTO USERS (USERNAME, PASSWORD, EMAIL) VALUES (?, ?, ?)',
                (username, password, email)
            )
            conn.commit()
            print(f"Registration successful for user: {username}")
            print(f"Stored credentials - Username: {username}, Password: {password}")
            return jsonify({'message': 'Registration successful'}), 201
        except Exception as e:
            print(f"Registration error: {str(e)}")
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

def capture_screenshot():
    try:
        # Take full screen screenshot
        screenshot = pyautogui.screenshot(region=(0, 0, pyautogui.size().width, pyautogui.size().height))
        # Convert to bytes
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG", quality=95)  # Increased quality
        screenshot_bytes = buffered.getvalue()
        return base64.b64encode(screenshot_bytes).decode()
    except Exception as e:
        print(f"Screenshot error: {str(e)}")
        return None

def capture_camera_image():
    try:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return None

        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not capture frame")
            return None

        # Release camera
        cap.release()

        # Convert frame to bytes
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode()
    except Exception as e:
        print(f"Camera capture error: {str(e)}")
        return None

def get_ip_location(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        data = response.json()
        if data['status'] == 'success':
            return {
                'city': data.get('city', 'Unknown'),
                'state': data.get('regionName', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'isp': data.get('isp', 'Unknown')
            }
    except Exception as e:
        print(f"Error getting IP location: {str(e)}")
    return None

def send_security_alert(username, app_name, ip_address, location, screenshot_data=None, camera_image=None):
    """Send security alert email with all collected data"""
    try:
        # Get current user's email from database
        current_user = get_jwt_identity()
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT EMAIL FROM USERS WHERE USERNAME = ?', (current_user,))
            result = cursor.fetchone()
            user_email = result[0] if result else None
            cursor.close()
            conn.close()

            if user_email:
                print(f"Preparing to send security alert to {user_email}")
                msg = Message(
                    subject='Security Alert: Unauthorized Access Attempt',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user_email]
                )

                # Create HTML email body with more detailed information
                msg.html = f"""
                <h2>Security Alert: Unauthorized Access Attempt</h2>
                <p>Multiple failed login attempts have been detected for a monitored application.</p>
                <ul>
                    <li><strong>Application:</strong> {app_name}</li>
                    <li><strong>IP Address:</strong> {ip_address}</li>
                    <li><strong>Location:</strong> {location['city']}, {location['region']}, {location['country']}</li>
                    <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({location['timezone']})</li>
                </ul>
                <p style="color: red;"><strong>Action Required:</strong> Please review your application's security settings and take appropriate action.</p>
                <p>If this was not you, someone may be attempting to access your applications without authorization.</p>
                """

                # Attach screenshot if available
                if screenshot_data:
                    try:
                        # Convert base64 to image
                        if ',' in screenshot_data:
                            screenshot_data = screenshot_data.split(',')[1]  # Remove data URL prefix
                        screenshot_bytes = base64.b64decode(screenshot_data)
                        msg.attach('screenshot.png', 'image/png', screenshot_bytes)
                        print("Screenshot attached to email")
                    except Exception as e:
                        print(f"Error attaching screenshot: {str(e)}")

                # Attach camera image if available
                if camera_image:
                    try:
                        # Convert base64 to image
                        if ',' in camera_image:
                            camera_data = camera_image.split(',')[1]  # Remove data URL prefix
                        camera_bytes = base64.b64decode(camera_data)
                        msg.attach('intruder.jpg', 'image/jpeg', camera_bytes)
                        print("Camera image attached to email")
                    except Exception as e:
                        print(f"Error attaching camera image: {str(e)}")

                # Send email
                with app.app_context():
                    mail.send(msg)
                print(f"Security alert successfully sent to {user_email}")
                return True
            else:
                print(f"No email found for user")
                return False

    except Exception as e:
        print(f"Error sending security alert: {str(e)}")
        return False

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello {current_user}! This is a protected route.'})

@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    try:
        data = request.get_json()
        process_names = data.get('process_names', [])
        
        if not process_names:
            return jsonify({'error': 'No process names provided'}), 400
            
        monitoring_service.start_monitoring(process_names)
        return jsonify({'message': 'Monitoring started successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitoring():
    try:
        monitoring_service.stop_monitoring()
        return jsonify({'message': 'Monitoring stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/logs', methods=['GET'])
def get_monitoring_logs():
    try:
        logs = monitoring_service.get_screenshot_logs()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

class WindowsAppMonitor:
    def __init__(self):
        self.monitored_apps = []
        self.monitoring_thread = None
        self.should_stop = False
        self.max_login_attempts = 3
        self.login_attempts = {}
        self.lock = threading.Lock()
        self.redirect_url = "http://localhost:3000/login"
        self.blocked_pids = set()
        self.is_running = False
        self.suspended_processes = {}
        self.initial_processes = set()
        self.successfully_logged_in = set()
        self.notification_sent = set()
        self.app_login_states = {}

    def _monitor_loop(self):
        """Main monitoring loop"""
        self.is_running = True
        print("Monitoring loop started")
        
        # Store initial processes when monitoring starts
        self.initial_processes = {proc.pid for proc in psutil.process_iter(['pid'])}
        
        while not self.should_stop:
            try:
                with self.lock:
                    for app in self.monitored_apps:
                        process_name = app['process_name']
                        # Check if any process with this name is running
                        for proc in psutil.process_iter(['name', 'pid', 'ppid', 'create_time']):
                            try:
                                if proc.info['name'].lower() == process_name:
                                    # Get parent process ID
                                    parent_pid = proc.info['ppid']
                                    
                                    # Skip if parent process is already authenticated
                                    if parent_pid in self.successfully_logged_in:
                                        if proc.pid not in self.successfully_logged_in:
                                            print(f"Automatically authenticating child process {proc.pid} of {process_name}")
                                            self.successfully_logged_in.add(proc.pid)
                                        continue
                                    
                                    # Skip if this process is already authenticated
                                    if proc.pid in self.successfully_logged_in:
                                        continue
                                        
                                    # Only handle new processes that weren't running when monitoring started
                                    # and haven't been handled yet
                                    if (proc.pid not in self.initial_processes and 
                                        proc.pid not in app['running_pids'] and 
                                        proc.pid not in self.blocked_pids and
                                        proc.pid not in self.successfully_logged_in and
                                        proc.pid not in self.notification_sent):
                                        
                                        # Get process creation time
                                        create_time = datetime.fromtimestamp(proc.info['create_time'])
                                        current_time = datetime.now()
                                        time_diff = (current_time - create_time).total_seconds()
                                        
                                        # Only handle processes created within the last 2 seconds
                                        if time_diff <= 2:
                                            print(f"New instance of {app['app_name']} detected (PID: {proc.pid})")
                                            
                                            # Block the process immediately
                                            try:
                                                # Suspend the process
                                                proc.suspend()
                                                self.blocked_pids.add(proc.pid)
                                                self.suspended_processes[proc.pid] = {
                                                    'app_name': app['app_name'],
                                                    'process': proc,
                                                    'login_attempts': 0,
                                                    'start_time': current_time
                                                }
                                                print(f"Blocked new instance of {app['app_name']} (PID: {proc.pid})")
                                                
                                                # Send notification to frontend about app launch
                                                self._handle_app_launch(app['app_name'], process_name)
                                                
                                                # Add to running pids and notification sent to prevent duplicate handling
                                                app['running_pids'].add(proc.pid)
                                                self.notification_sent.add(proc.pid)
                                            except Exception as e:
                                                print(f"Error handling process {proc.pid}: {str(e)}")
                                                try:
                                                    proc.terminate()
                                                except:
                                                    pass
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                            
                            # Clean up terminated processes
                            app['running_pids'] = {pid for pid in app['running_pids'] 
                                                 if psutil.pid_exists(pid)}
                            self.blocked_pids = {pid for pid in self.blocked_pids 
                                               if psutil.pid_exists(pid)}
                            self.successfully_logged_in = {pid for pid in self.successfully_logged_in 
                                                         if psutil.pid_exists(pid)}
                            self.notification_sent = {pid for pid in self.notification_sent 
                                               if psutil.pid_exists(pid)}
                            
                            # Clean up suspended processes
                            self.suspended_processes = {
                                pid: data for pid, data in self.suspended_processes.items() 
                                if psutil.pid_exists(pid)
                            }
            except Exception as e:
                print(f"Error in monitor loop: {str(e)}")
            time.sleep(0.1)  # Check very frequently

    def handle_login_attempt(self, app_name, username, password):
        """Handle login attempt with user credentials"""
        with self.lock:
            # Find the suspended process for this app
            for pid, data in list(self.suspended_processes.items()):
                if data['app_name'].lower() == app_name.lower():
                    # Get current logged in user's email
                    current_user = get_jwt_identity()
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            # Get current logged in user's email
                            cursor.execute('SELECT EMAIL FROM USERS WHERE USERNAME = ?', (current_user,))
                            current_user_result = cursor.fetchone()
                            current_user_email = current_user_result[0] if current_user_result else None

                            # Query the USERS table in HANA for login validation
                            cursor.execute('SELECT PASSWORD FROM USERS WHERE USERNAME = ?', (username,))
                            result = cursor.fetchone()

                            if result and result[0] == password:  # In production, use proper password hashing
                                try:
                                    # Resume the process
                                    data['process'].resume()
                                    print(f"Resumed {app_name} after successful login")
                                    # Add to successfully logged in processes
                                    self.successfully_logged_in.add(pid)
                                    # Remove from suspended processes
                                    del self.suspended_processes[pid]
                                    self.blocked_pids.remove(pid)
                                    # Remove from notification sent
                                    self.notification_sent.discard(pid)
                                    return True, "Login successful"
                                except Exception as e:
                                    print(f"Error resuming process: {str(e)}")
                                    return False, "Error resuming process"
                            else:
                                data['login_attempts'] += 1
                                print(f"Login attempt {data['login_attempts']} failed for {app_name}")
                                
                                if data['login_attempts'] >= self.max_login_attempts:
                                    try:
                                        # Terminate the process
                                        data['process'].terminate()
                                        print(f"Terminated {app_name} due to max login attempts")
                                        # Remove from suspended processes
                                        del self.suspended_processes[pid]
                                        self.blocked_pids.remove(pid)
                                        # Remove from notification sent
                                        self.notification_sent.discard(pid)
                                        # Send security alert to current logged in user's email
                                        if current_user_email:
                                            print(f"Sending security alert to logged in user: {current_user} ({current_user_email})")
                                            self._send_security_alert(app_name, data['process'].info['name'], current_user_email)
                                        else:
                                            print("No logged in user email found for security alert")
                                        return False, "Max login attempts exceeded"
                                    except Exception as e:
                                        print(f"Error terminating process: {str(e)}")
                                        return False, "Error terminating process"
                                return False, f"Invalid credentials. Attempts remaining: {self.max_login_attempts - data['login_attempts']}"
                        except Exception as e:
                            print(f"Error verifying credentials: {str(e)}")
                            return False, "Error verifying credentials"
                        finally:
                            cursor.close()
                            conn.close()
                    return False, "Database connection failed"
            return False, "No suspended process found for this app"

    def add_app(self, app_name, process_name):
        """Add an application to monitor"""
        try:
            # Normalize process name to lowercase
            process_name = process_name.lower()
            
            # Check if process exists
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name:
                    with self.lock:
                        self.monitored_apps.append({
                            'app_name': app_name,
                            'process_name': process_name,
                            'login_attempts': 0,
                            'running_pids': set()
                        })
                        # Initialize login state for this app
                        self.app_login_states[app_name] = False
                    print(f"Added {app_name} ({process_name}) to monitoring")
                    return True
            print(f"Process {process_name} not found")
            return False
        except Exception as e:
            print(f"Error adding app: {str(e)}")
            return False

    def remove_app(self, app_name):
        """Remove an application from monitoring"""
        with self.lock:
            initial_count = len(self.monitored_apps)
            self.monitored_apps = [app for app in self.monitored_apps 
                                 if app['app_name'].lower() != app_name.lower()]
            # Remove login state for this app
            self.app_login_states.pop(app_name, None)
            removed = len(self.monitored_apps) < initial_count
            print(f"Removed {app_name} from monitoring: {removed}")
            return removed

    def _handle_app_launch(self, app_name, process_name):
        """Handle application launch by redirecting to login"""
        try:
            # Send notification to frontend about app launch
            with app.app_context():
                # Check if there's already an unhandled notification for this app
                existing_notification = Notification.query.filter_by(
                    type='login_required',
                    handled=False,
                    data={'app_name': app_name}
                ).first()
                
                if not existing_notification:
                    notification = Notification(
                        title="Application Launch Detected",
                        message=f"{app_name} was launched. Please login to continue.",
                        type="login_required",
                        data={
                            'app_name': app_name,
                            'process_name': process_name,
                            'redirect_url': self.redirect_url
                        }
                    )
                    db.session.add(notification)
                    db.session.commit()
                    print(f"Created login notification for {app_name}")
        except Exception as e:
            print(f"Error handling app launch: {str(e)}")

    def _send_security_alert(self, app_name, process_name, user_email):
        """Send security alert for failed login attempts"""
        try:
            print(f"Preparing security alert for {app_name} to {user_email}")
            # Get screenshot
            screenshot_data = capture_screenshot()
            
            # Get camera image
            camera_data = capture_camera_image()
            
            # Get IP address
            ip_address = request.remote_addr if request.remote_addr != '127.0.0.1' else requests.get('https://api.ipify.org?format=json').json()['ip']
            
            # Send the alert using the main send_security_alert function
            send_security_alert(
                username=None,  # We don't need username as we have direct email
                app_name=app_name,
                ip_address=ip_address,
                location=get_location(ip_address),
                screenshot_data=screenshot_data,
                camera_image=camera_data
            )
            
            print(f"Security alert sent successfully to {user_email}")
            
        except Exception as e:
            print(f"Error sending security alert: {str(e)}")

    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.is_running:
            self.should_stop = False
            # Reset initial processes when starting monitoring
            self.initial_processes = {proc.pid for proc in psutil.process_iter(['pid'])}
            self.monitoring_thread = threading.Thread(target=self._monitor_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            print("Windows app monitoring started")
            return True
        return False

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        print("Attempting to stop monitoring...")
        self.should_stop = True
        self.is_running = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join()
            print("Windows app monitoring stopped")
            return True
        return False

    def get_monitored_apps(self):
        """Get list of monitored applications"""
        with self.lock:
            return [{'app_name': app['app_name'], 'process_name': app['process_name']} 
                   for app in self.monitored_apps]

# Initialize Windows app monitor
windows_monitor = WindowsAppMonitor()

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        # Get the most recent unhandled notification
        notification = Notification.query.filter_by(
            type='login_required',
            handled=False
        ).first()
        
        if notification:
            # Mark notification as handled immediately
            notification.handled = True
            db.session.commit()
            
            return jsonify([{
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'data': notification.data,
                'created_at': notification.created_at.isoformat()
            }])
        
        # If no notifications, return empty list with cache control headers
        response = jsonify([])
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/start', methods=['POST', 'OPTIONS'])
@jwt_required()
def start_windows_monitoring():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        if windows_monitor.start_monitoring():
            return jsonify({'message': 'Windows app monitoring started'})
        return jsonify({'message': 'Monitoring already running'})
    except Exception as e:
        print(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/stop', methods=['POST', 'OPTIONS'])
@jwt_required()
def stop_windows_monitoring():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        if windows_monitor.stop_monitoring():
            return jsonify({'message': 'Windows app monitoring stopped'})
        return jsonify({'message': 'Monitoring already stopped'})
    except Exception as e:
        print(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps', methods=['GET'])
@jwt_required()
def get_monitored_windows_apps():
    try:
        apps = windows_monitor.get_monitored_apps()
        print(f"Currently monitored apps: {apps}")
        return jsonify(apps)
    except Exception as e:
        print(f"Error getting monitored apps: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/login-success', methods=['POST', 'OPTIONS'])
@jwt_required()
def handle_login_success():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()
        app_name = data.get('app_name')
        if not app_name:
            return jsonify({'error': 'Missing app name'}), 400

        # Find and resume the suspended process
        with windows_monitor.lock:
            for pid, proc_data in windows_monitor.suspended_processes.items():
                if proc_data['app_name'].lower() == app_name.lower():
                    try:
                        # Resume the process
                        proc_data['process'].resume()
                        print(f"Resumed {app_name} process (PID: {pid})")
                        
                        # Add to successfully logged-in processes
                        windows_monitor.successfully_logged_in.add(pid)
                        
                        # Remove from suspended processes
                        del windows_monitor.suspended_processes[pid]
                        windows_monitor.blocked_pids.remove(pid)
                        
                        # Remove from notification sent
                        windows_monitor.notification_sent.discard(pid)
                        
                        return jsonify({'message': f'Successfully resumed {app_name}'})
                    except Exception as e:
                        print(f"Error resuming process: {str(e)}")
                        return jsonify({'error': f'Error resuming process: {str(e)}'}), 500

            return jsonify({'message': f'No suspended process found for {app_name}'}), 404
    except Exception as e:
        print(f"Error handling login success: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/login-failed', methods=['POST', 'OPTIONS'])
@jwt_required()
def handle_login_failed():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()
        app_name = data.get('app_name')
        screenshot = data.get('screenshot')
        camera_image = data.get('camera_image')
        max_attempts_reached = data.get('max_attempts_reached', False)

        if not app_name:
            return jsonify({'error': 'Missing app name'}), 400

        if max_attempts_reached:
            # Get current logged in user's email
            current_user = get_jwt_identity()
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT EMAIL FROM USERS WHERE USERNAME = ?', (current_user,))
                    result = cursor.fetchone()
                    if result:
                        user_email = result[0]
                        print(f"Sending security alert to logged in user: {current_user} ({user_email})")
                        
                        # Get IP address
                        ip_address = request.remote_addr if request.remote_addr != '127.0.0.1' else requests.get('https://api.ipify.org?format=json').json()['ip']
                        
                        # Send security alert
                        send_security_alert(
                            username=current_user,  # Pass the logged in username
                            app_name=app_name,
                            ip_address=ip_address,
                            location=get_location(ip_address),
                            screenshot_data=screenshot,
                            camera_image=camera_image
                        )
                        
                        return jsonify({
                            'message': 'Security alert sent',
                            'details': 'Account locked due to multiple failed attempts'
                        })
                    else:
                        print(f"No email found for logged in user: {current_user}")
                        return jsonify({'error': 'Could not find user email'}), 500
                finally:
                    cursor.close()
                    conn.close()
            else:
                return jsonify({'error': 'Database connection failed'}), 500
            
        return jsonify({'message': f'Login failure recorded for {app_name}'})
    except Exception as e:
        print(f"Error handling login failure: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_public_ip():
    """Get public IP address when running locally"""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except:
        return '127.0.0.1'

def get_location(ip_address):
    """Get location information from IP address"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown')
            }
    except:
        pass
    return {'city': 'Unknown', 'country': 'Unknown', 'region': 'Unknown', 'timezone': 'Unknown'}

@app.route('/api/monitor/running-apps', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_running_apps():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response

    try:
        running_apps = []
        # Get all running processes
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                process_name = proc.info['name'].lower()
                # Filter out system processes and common background processes
                if not any(x in process_name for x in ['system', 'svchost', 'runtime', 'service', 'dllhost', 'conhost', 'background']):
                    # Get the process name without .exe
                    display_name = proc.info['name'].replace('.exe', '')
                    # Only add if it's not already in the list
                    if not any(app['process_name'] == proc.info['name'] for app in running_apps):
                        running_apps.append({
                            'name': display_name,
                            'process_name': proc.info['name']
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                print(f"Error processing process: {str(e)}")
                continue
        
        # Sort the list by name
        running_apps.sort(key=lambda x: x['name'])
        
        # Add some common applications that might not be running
        common_apps = [
            {'name': 'Notepad', 'process_name': 'notepad.exe'},
            {'name': 'Calculator', 'process_name': 'calc.exe'},
            {'name': 'Paint', 'process_name': 'mspaint.exe'},
            {'name': 'WordPad', 'process_name': 'wordpad.exe'},
            {'name': 'Command Prompt', 'process_name': 'cmd.exe'},
            {'name': 'PowerShell', 'process_name': 'powershell.exe'},
            {'name': 'Task Manager', 'process_name': 'taskmgr.exe'},
            {'name': 'Windows Explorer', 'process_name': 'explorer.exe'},
            {'name': 'Chrome', 'process_name': 'chrome.exe'},
            {'name': 'Firefox', 'process_name': 'firefox.exe'},
            {'name': 'Edge', 'process_name': 'msedge.exe'},
            {'name': 'VS Code', 'process_name': 'code.exe'},
            {'name': 'WhatsApp', 'process_name': 'WhatsApp.exe'}
        ]
        
        # Add common apps if they're not already in the list
        for app in common_apps:
            if not any(running['process_name'] == app['process_name'] for running in running_apps):
                running_apps.append(app)
        
        print(f"Found {len(running_apps)} applications")
        return jsonify(running_apps)
    except Exception as e:
        print(f"Error fetching running apps: {str(e)}")
        # Return common apps even if there's an error
        return jsonify([
            {'name': 'Notepad', 'process_name': 'notepad.exe'},
            {'name': 'Calculator', 'process_name': 'calc.exe'},
            {'name': 'Paint', 'process_name': 'mspaint.exe'},
            {'name': 'WordPad', 'process_name': 'wordpad.exe'},
            {'name': 'Command Prompt', 'process_name': 'cmd.exe'},
            {'name': 'PowerShell', 'process_name': 'powershell.exe'},
            {'name': 'Task Manager', 'process_name': 'taskmgr.exe'},
            {'name': 'Windows Explorer', 'process_name': 'explorer.exe'},
            {'name': 'Chrome', 'process_name': 'chrome.exe'},
            {'name': 'Firefox', 'process_name': 'firefox.exe'},
            {'name': 'Edge', 'process_name': 'msedge.exe'},
            {'name': 'VS Code', 'process_name': 'code.exe'},
            {'name': 'WhatsApp', 'process_name': 'WhatsApp.exe'}
        ])

@app.route('/api/monitor/windows-apps', methods=['POST', 'OPTIONS'])
@jwt_required()
def add_windows_app():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()
        app_name = data.get('app_name')
        process_name = data.get('process_name')
        
        print(f"Adding app to monitor: {app_name} ({process_name})")
        
        if not all([app_name, process_name]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if windows_monitor.add_app(app_name, process_name):
            # Start monitoring if not already running
            if not windows_monitor.is_running:
                windows_monitor.start_monitoring()
            return jsonify({'message': f'Added {app_name} to monitoring'})
        return jsonify({'error': 'Failed to add application'}), 400
    except Exception as e:
        print(f"Error adding app: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/status', methods=['GET'])
@jwt_required()
def get_monitoring_status():
    """Get the current status of monitored apps and any pending notifications"""
    try:
        monitored_apps = windows_monitor.get_monitored_apps()
        is_monitoring = windows_monitor.is_running
        
        # Get any pending notifications
        notification = Notification.query.filter_by(
            type='login_required',
            handled=False
        ).first()
        
        print(f"Monitoring status - Running: {is_monitoring}, Apps: {monitored_apps}")
        
        return jsonify({
            'is_monitoring': is_monitoring,
            'monitored_apps': monitored_apps,
            'has_pending_notification': notification is not None
        })
    except Exception as e:
        print(f"Error getting monitoring status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/windows-apps/<app_name>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def remove_windows_app(app_name):
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        return response

    try:
        print(f"Attempting to remove app: {app_name}")
        if windows_monitor.remove_app(app_name):
            return jsonify({'message': f'Removed {app_name} from monitoring'})
        return jsonify({'error': 'Application not found'}), 404
    except Exception as e:
        print(f"Error removing app: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/db/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users from HANA database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT USERNAME, EMAIL FROM USERS')
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify([{'username': user[0], 'email': user[1]} for user in users])
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/db/login-attempts', methods=['GET'])
@jwt_required()
def get_login_attempts():
    """Get all login attempts from HANA database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT USERNAME, SUCCESS, IP_ADDRESS, TIMESTAMP FROM LOGIN_ATTEMPTS ORDER BY TIMESTAMP DESC')
            attempts = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify([{
                'username': attempt[0],
                'success': attempt[1],
                'ip_address': attempt[2],
                'timestamp': attempt[3].isoformat() if attempt[3] else None
            } for attempt in attempts])
    except Exception as e:
        print(f"Error fetching login attempts: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\nInitializing database...")
    init_db()
    app.run(debug=True) 