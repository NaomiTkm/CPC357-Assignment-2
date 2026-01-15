import base64
import functions_framework
import json
import smtplib
from datetime import datetime
import pytz 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import firestore

# --- SECURITY CONFIGURATION ---
SENDER_EMAIL = "naomitham.usm@gmail.com" 
APP_PASSWORD = "abcd efgh ijkl mnop" # To replace with own created app password in Google

# Initialize DB Client
db = firestore.Client(database="home-solar-monitoring")

# Set your timezone
LOCAL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

@functions_framework.cloud_event
def subscribe(cloud_event):
    # --- 1. DECODE THE ALERT DATA ---
    try:
        raw_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        alert = json.loads(raw_data)
        print(f"Received Alert for device: {alert.get('device_id')}")
    except Exception as e:
        print(f"Error decoding message: {e}")
        return

    # --- 2. FIND OUT WHO TO EMAIL ---
    try:
        doc = db.collection('config').document('alert_settings').get()
        if doc.exists:
            recipient_email = doc.to_dict().get('recipient_email')
            print(f"Database says: Send to {recipient_email}")
        else:
            print("No user has subscribed yet. Sending to Admin.")
            recipient_email = SENDER_EMAIL 
            
    except Exception as e:
        print(f"Database Read Error: {e}")
        return

    # --- 3. FORMAT DATA FOR EMAIL ---
    
    # A. Format Temperature (2 Decimal Places)
    try:
        temp_val = float(alert.get('temp', 0))
        formatted_temp = f"{temp_val:.2f}"
    except:
        formatted_temp = str(alert.get('temp'))

    # B. Format Time (12-hour format)
    try:
        raw_time = str(alert.get('timestamp'))
        
        # [FIX] Clean the string to ensure it matches the pattern
        # 1. Remove microseconds (split at '.')
        if "." in raw_time:
            raw_time = raw_time.split(".")[0]
        # 2. Replace 'T' with space if it's ISO format
        raw_time = raw_time.replace("T", " ")
        
        # Now parse the clean string
        dt_obj = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
        
        # Ensure it has timezone info (localized to MYT)
        dt_obj = LOCAL_TZ.localize(dt_obj)
        
        # Convert to readable 12-hour format (e.g., "14 Jan 2026, 04:30:00 PM")
        formatted_time = dt_obj.strftime("%d %b %Y, %I:%M:%S %p")
        
    except Exception as e:
        print(f"Time format warning: {e}")
        formatted_time = alert.get('timestamp') # Fallback if it still fails

    # --- 4. CONSTRUCT THE EMAIL ---
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = f"🔥 CRITICAL ALERT: {alert.get('device_id', 'Inverter')} Overheating!"
    
    body = f"""
    ⚠️ INVERTER CRITICAL FAULT ⚠️
    
    The monitoring system has detected a dangerous condition.
    
    --------------------------------------------------
    ⏰ Time:   {formatted_time}
    🌡️ Temp:   {formatted_temp} °C (Threshold Exceeded)
    ⚡ Device: {alert.get('device_id')}
    ❌ Faults: {alert.get('fault')}
    --------------------------------------------------
    
    Please access the dashboard and check the inverter to prevent hardware damage.

    Link to Dashboard: https://solar-atap-dashboard-82861964922.us-central1.run.app/  
    
    - Automated Alert System
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # --- 5. SEND THE EMAIL ---
    try:
        print(f"Connecting to Gmail Server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_email, text)
        server.quit()
        print(f"SUCCESS: Email sent to {recipient_email}")
        return "Email Sent"
        
    except Exception as e:
        print(f"FAILED to send email: {e}")
        raise e

