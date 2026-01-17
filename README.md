# CPC357-Assignment-2
Solar ATAP: A Smart Rooftop Solar Monitoring System Developed on Google Cloud Platform (GCP)

## System Architecture
The system utilizes a Layered IoT Architecture hosted entirely on Google Cloud Platform (GCP).
1. Perception: Simulated ESP32 logic generates synthetic telemetry (Voltage, Current, Temp).
2. Network: Data is transmitted via MQTT to a Mosquitto Broker hosted on a Compute Engine VM.
3. Ingestion: A Python backend.py script bridges MQTT to Google Firestore.
4. Processing: Scikit-Learn performs linear regression for forecasting; Cloud Functions handle critical alerts via Pub/Sub.
5. Application: A Streamlit dashboard hosted on Cloud Run visualizes data.

## Features
1. Secure Access: Google Identity Platform login integration.
2. Real-Time Monitoring: Visualises real time data on web dashboard.
3. AI Forecasting: Predicts next-24h generation and financial savings (NEM 3.0 Rates).
4. Critical Alerts: Automated HTML emails sent via Cloud Functions upon anomaly detection.
5. Reporting: Historical snapshots and billing report generation.

## Hardware
This project uses a ESP32 microcontroller to simulate the generation of data from solar inverters installed at households and the transmission of data using MQTT. The ESP32 has a built-in WiFi module to enable WiFi connnection.
  1. Data Generation: The script algorithmically generates sensor readings (Voltage, Current, Temperature) based on a defined diurnal profile, introducing random variance to simulate cloud cover and grid fluctuations.
  2. To validate the cloud alerting logic, the firmware includes a probabilistic fault generator that occasionally spikes the simulated temperature above 75°C (Critical Overheating Event).

Program the ESP32 microcontroller with the code provided in 'Hardware Simulator' folder.

Edit the configuration for WiFi credentials, MQTT Connection as needed.

## Project Structure
```
/solar-atap-monitoring-system
├── backend.py                    
├── /deploy-solar-atap
│   ├── Dockerfile             
│   ├── requirements.txt    
│   ├── app.py                   
│   └── google_auth.py     
└── /email-alert-handler          # Email Alert Logic
    ├── main.py           
    └── requirements.txt
```

## Prerequisites
1. Google Cloud Platform Account with Billing enabled.
2. Gmail Account with 2-Step Verification enabled and App Password generated.

## Installation and Setup
### Cloud Infrastructure
#### GCP Compute Engine
   Provision an e2-medium Compute Engine instance (Ubuntu 22.04). SSH into the VM and run:
   ```
   # Update and install system dependencies
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y mosquitto mosquitto-clients python3-pip

   # Start Mosquitto Service
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto

   # Install Python Libraries for Backend
   pip3 install paho-mqtt google-cloud-firestore google-cloud-pubsub
   ```
#### GCP Firestore
1. Go to GCP Console > Firestore.
2. Create Database -> Select Native Mode.
3. Location: us-central1 (or Multi-Region).
4. Database ID: home-solar-monitoring.

#### Cloud Functions
1. Create a Pub/Sub Topic named solar-inverter-critical-alerts.
2. Create a Cloud Function (Gen 2) triggered by this topic.
3. Runtime: Python 3.14
4. Files: main.py, requirements.txt
5. Deploy.

#### Google Identity Platform
User authentication is implemented using Google Cloud Identity Platform to provide secure, scalable, and industry-standard identity management.
1. GCP Console > Enable Identify Platform Service
2. Add a Provider
3. Select Email/Password
4. Enable and Save
5. Create user in the cloud (User > Add User)

#### Email Security
This project uses Gmail SMTP. Ensure you use an App Password, not your raw login password.
```
Go to Google Account > Security > 2-Step Verification > App Passwords.
```

### Backend Service
Upload backend.py to your VM. Run it in the background to start collecting data:
```
# Run backend in background (persists after SSH logout)
nohup python3 backend.py > output.log 2>&1 &

# Verify it is running
ps aux | grep backend.py
```

MQTT Topic Testing 
Verify data flow using mosquitto_sub CLI tool on the VM.
```
# Verify topic inverter/readings
Mosquitto_sub -t “inverter/readings”
```
<img width="929" height="245" alt="image" src="https://github.com/user-attachments/assets/5e677fa8-057e-48ac-ad3a-aec5b6caebd6" />


### Frontend (Streamlit Dashboard)
1. The app.py file serves as the main entry point for the Streamlit frontend. It connects to Firestore to visualize telemetry and runs the AI forecasting model.
2. The dashboard is gated by google_auth.py. To make the login work:
   - Ensure the GOOGLE_API_KEY in app.py matches your project's Client API Key found in the GCP Console (APIs & Services > Credentials).
   - Users must be explicitly added to the Identity Platform > Users list in the Google Cloud Console to grant them access.
  
3. Within the VM, the dashboard may be launced locally for testing:
   ```
   # Navigate to the deployment folder
   cd deploy-solar-atap
   
   # Run backend 
   python3 backend.py
   
   # Run Streamlit
   streamlit run app.py
   
   # The application will launch at http://localhost:8501

   # Verify if backend is running
   ps aux | grep backend.py

   # Restart or kill backend.py process if needed
   # 1. Find the PID (Process ID) from the command above (e.g., 12345)
   # 2. Kill it
   kill 12345
   ```

### Dashboard Deployment (Cloud Run)
Prepare your frontend for the web.

A. Create Deployment Files Inside your local project folder, ensure you have:
- app.py (The dashboard code)
- google_auth.py (The login logic)
- requirements.txt (Dependencies)
- Dockerfile (Container instructions)

```
# Create a new folder in the virtual machine for frontend deployment
mkdir deploy-frontend
cp app.py deploy-frontend/
cp google_auth.py deploy-frontend/
cd deploy-frontend

# Create a specific requirements file for the cloud server
nano requirements.txt

# Contents of requirements.txt
streamlit
google-cloud-firestore
pandas
numpy
scikit-learn
plotly
extra-streamlit-components
Google-auth

# Create the Dockerfile (content is as per Dockerfile provided in repo)
nano Dockerfile
```

B. Deploy to Cloud Run 
```
# Run this command from your terminal (inside the deploy-solar-atap folder)
gcloud run deploy solar-atap-dashboard --source . --region us-central1 --allow-unauthenticated
```
C. Navigate to Cloud Run console, look for solar-atap-dashboard and get the URL to access the dashboard

### User Interface
Solar ATAP PoC Website: https://solar-atap-dashboard-82861964922.us-central1.run.app/

#### Live Monitoring Dashboard
<img width="959" height="469" alt="image" src="https://github.com/user-attachments/assets/fbe5290f-e432-4ec7-8571-4074bde56317" />
<img width="959" height="467" alt="image" src="https://github.com/user-attachments/assets/edf44775-65ba-4a46-b309-c93aaf53194b" />
<img width="478" height="433" alt="image" src="https://github.com/user-attachments/assets/dc39f401-9f93-4618-8461-32a071f6bfe9" />

#### Configure Alert Recipient Email
<img width="959" height="471" alt="image" src="https://github.com/user-attachments/assets/fb709d86-1435-497a-a603-ef4cf4a30cf8" />

#### Alert Email sent to user upon anomaly detection
<img width="959" height="391" alt="image" src="https://github.com/user-attachments/assets/f4fc73a2-9155-4e1b-9765-c96c0268d225" />

#### AI Prediction Module
<img width="959" height="436" alt="image" src="https://github.com/user-attachments/assets/25fff641-473e-40b0-9f53-487cccac8a65" />

#### Reporting Module
<img width="956" height="432" alt="image" src="https://github.com/user-attachments/assets/dcd4083b-0125-476b-bf8a-ac4d4c067668" />






