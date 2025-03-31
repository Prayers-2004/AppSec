import cv2
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import current_app

def capture_image():
    """Capture image from webcam and save it."""
    try:
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        # Read frame
        ret, frame = cap.read()
        
        if ret:
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'intruder_{timestamp}.jpg'
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save image
            cv2.imwrite(filepath, frame)
            
            # Release webcam
            cap.release()
            
            return filepath
            
        cap.release()
        return None
        
    except Exception as e:
        print(f"Error capturing image: {str(e)}")
        return None

def get_location(ip_address):
    """Get location from IP address using geopy."""
    try:
        geolocator = Nominatim(user_agent="appsec")
        location = geolocator.geocode(ip_address)
        
        if location:
            return f"{location.address}"
        return "Location not found"
        
    except GeocoderTimedOut:
        return "Location lookup timed out"
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        return "Error getting location"

def send_alert_email(user_email, image_path, location):
    """Send email alert with intruder image and location."""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = 'AppSec Security Alert - Unauthorized Access Attempt'
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = user_email
        
        # Email body
        body = f"""
        Security Alert!
        
        An unauthorized access attempt was detected.
        Location: {location}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Please check the attached image of the intruder.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach image if available
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)
        
        # Send email
        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False 