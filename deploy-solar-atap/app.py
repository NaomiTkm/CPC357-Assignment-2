import streamlit as st
import google_auth  # Your custom helper file
from google.cloud import firestore
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import extra_streamlit_components as stx
import warnings
import time

# Hide technical warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Solar ATAP Monitor")

# --- CSS HACK TO STOP "GREYING OUT" ---
st.markdown("""
    <style>
    .stApp { opacity: 1 !important; }
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

DATABASE_NAME = 'home-solar-monitoring'
COLLECTION_NAME = 'solar_telemetry'
REPORT_COLLECTION = 'billing_reports' 

# [MALAYSIA CONFIGURATION]
ENERGY_RATE = 0.48  # RM per kWh (NEM 3.0)
TIMEZONE = 'Asia/Kuala_Lumpur'

# [CRITICAL] REPLACE THIS WITH YOUR REAL API KEY
GOOGLE_API_KEY = "place_google_api_key_here" 

# --- AUTHENTICATION FLOW ---
if not google_auth.render_login(GOOGLE_API_KEY):
    st.stop()

# ====================================================
#          LOGGED IN DASHBOARD
# ====================================================

# Initialize DB Client (Global access)
try:
    db = firestore.Client(database=DATABASE_NAME)
except Exception as e:
    st.error(f"❌ Database Connection Failed: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    # 1. User Info
    user_email = st.session_state.get('user_email', 'Homeowner')
    st.success(f"User: **{user_email}**")
    
    # 2. Alert Subscription
    st.markdown("### 🔔 Notifications")
    if st.button("Set as Alert Recipient"):
        try:
            db.collection('config').document('alert_settings').set({
                'recipient_email': user_email,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            st.toast(f"✅ Alerts routed to: {user_email}")
            time.sleep(1)
        except Exception as e:
            st.error(f"Failed to update settings: {e}")

    # 3. Live Mode Toggle
    st.divider()
    st.markdown("### ⏱️ Refresh Settings")
    live_mode = st.toggle("🔴 Live Data Feed", value=True, help="Auto-refresh dashboard every 3 seconds")
    
    if st.button("🔄 Manual Refresh"):
        st.rerun()

    # 4. Logout
    st.divider()
    if st.button("Logout"):
        # [FIX] Unique key ensures this manager is separate from the login manager
        cookie_manager = stx.CookieManager(key="logout_mgr")
        
        cookie_manager.delete('solar_user_email')
        st.session_state['authenticated'] = False
        st.session_state['user_email'] = None
        st.rerun()
        
    st.caption(f"📍 Location: Penang, MY")
    st.caption("System: Rooftop 5kW Inverter")

# --- MAIN TITLE ---
st.title("☀️ Solar ATAP: Smart Rooftop Solar Monitoring System")

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Live Dashboard", "🤖 AI Prediction"])

# --- DATA FETCHING (TELEMETRY) ---
try:
    # 1. Fetch Latest Telemetry (Fastest way)
    docs = db.collection(COLLECTION_NAME)\
        .order_by('timestamp', direction=firestore.Query.DESCENDING)\
        .limit(100).stream()
    data = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(data)
    
    # 2. Sort for Graphing (Oldest -> Newest)
    if not df.empty:
        df = df.sort_values(by='timestamp', ascending=True)

except Exception as e:
    st.error(f"Error reading telemetry: {e}")
    st.stop()

# --- TAB 1: LIVE MONITORING ---
with tab1:
    if not df.empty:
        latest = df.iloc[-1] # Get the newest record
        
        status = latest.get('health_status', 'UNKNOWN')
        alerts = latest.get('alerts', [])
        
        # STATUS BANNER + POP-UP TOAST
        if status == "CRITICAL":
            st.error(f"🚨 INVERTER FAULT: {alerts}")
            st.toast(f"🔥 CRITICAL ALERT: {alerts}", icon="🚨") 
        elif status == "WARNING":
            st.warning(f"⚠️ CHECK SYSTEM: {alerts}")
        else:
            st.success("✅ SYSTEM HEALTHY (Running)")

        # KPI METRICS
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Current Generation", f"{latest.get('power', 0):.1f} W")
        kpi2.metric("Inverter Temperature", f"{latest.get('temperature', 0):.1f} °C")
        kpi3.metric("Grid Voltage", f"{latest.get('voltage', 0):.1f} V")
        kpi4.metric("Load Current", f"{latest.get('current', 0):.1f} A")

        # Time Processing
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df['local_time'] = df['timestamp'].dt.tz_convert(TIMEZONE)
        df['time_str'] = df['local_time'].dt.strftime('%H:%M:%S')

        # Main Chart
        st.subheader("⚡ Rooftop Solar Generation")
        fig_main = make_subplots(specs=[[{"secondary_y": True}]])
        fig_main.add_trace(go.Scatter(x=df['time_str'], y=df['power'], name="Solar Output (W)", fill='tozeroy', line=dict(color='#ffaa00')), secondary_y=False)
        fig_main.add_trace(go.Scatter(x=df['time_str'], y=df['voltage'], name="Grid Voltage (V)", line=dict(color='#00cc96')), secondary_y=True)
        fig_main.add_trace(go.Scatter(x=df['time_str'], y=df['current'], name="Current (A)", line=dict(color='#636efa', dash='dot')), secondary_y=True)
        fig_main.update_layout(height=450, hovermode="x unified", title_text="Production vs Grid")
        fig_main.update_yaxes(title_text="<b>Generation (Watts)</b>", secondary_y=False)
        fig_main.update_yaxes(title_text="<b>Grid (V/A)</b>", secondary_y=True)
        st.plotly_chart(fig_main, use_container_width=True)

        # Component Charts
        st.subheader("🔍 Inverter Health Diagnostics")
        colA, colB, colC = st.columns(3)
        with colA:
            st.caption("Inverter Temperature")
            st.line_chart(df[['time_str', 'temperature']].set_index('time_str'), color='#EF553B')
        with colB:
            st.caption("Grid Voltage Stability")
            st.line_chart(df[['time_str', 'voltage']].set_index('time_str'), color='#00cc96')
        with colC:
            st.caption("Output Current")
            st.line_chart(df[['time_str', 'current']].set_index('time_str'), color='#636efa')

    else:
        st.info("Waiting for inverter data... (Backend running?)")

# --- TAB 2: AI PREDICTION ---
with tab2:
    st.header("🤖 AI Power Prediction & Savings")
    
    if len(df) > 10:
        # A. ACTUAL (Run Rate)
        actual_avg_power = df['power'].mean()
        actual_kwh_projection = (actual_avg_power * 24) / 1000
        actual_savings_projection = actual_kwh_projection * ENERGY_RATE

        # B. FORECAST (AI Prediction)
        df['index_time'] = range(len(df))
        X = df[['index_time']]
        y = df['power']
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_time = np.array(range(len(df), len(df) + 24)).reshape(-1, 1)
        prediction = model.predict(future_time)
        
        forecast_avg_power = np.mean(prediction)
        forecast_kwh = (forecast_avg_power * 24) / 1000
        forecast_savings = forecast_kwh * ENERGY_RATE
        
        # DISPLAY METRICS
        st.subheader("Today's Performance Snapshot")
        m1, m2, m3, m4 = st.columns(4)
        
        savings_delta = forecast_savings - actual_savings_projection
        
        m1.metric("Actual Avg Power", f"{actual_avg_power:.0f} W")
        m2.metric("Actual Savings", f"RM {actual_savings_projection:.2f}", help="Based on current run-rate")
        m3.metric("AI Forecast Power", f"{forecast_avg_power:.0f} W")
        
        m4.metric(
            "AI Projected Savings", 
            f"RM {forecast_savings:.2f}", 
            delta=f"RM {savings_delta:+.2f}" 
        )

        st.line_chart(prediction)
        st.caption("Graph: AI Trend Prediction for next cycle.")

        # REPORTING MODULE
        st.divider()
        st.subheader("📑 Daily Reporting Module")
        
        if st.button("💾 Save Snapshot Report"):
            report_data = {
                "timestamp": pd.Timestamp.now(tz=TIMEZONE),
                "actual_kwh_est": float(actual_kwh_projection),
                "actual_savings_rm": float(actual_savings_projection),
                "forecast_kwh": float(forecast_kwh),
                "forecast_savings_rm": float(forecast_savings),
                "status": "Verified"
            }
            db.collection(REPORT_COLLECTION).add(report_data)
            st.success("Report Saved!")
            time.sleep(1) 
            st.rerun()

        # HISTORY TABLE
        st.markdown("### 📜 Historical Report Log")
        
        try:
            report_docs = db.collection(REPORT_COLLECTION)\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(20).stream()
            
            report_list = []
            for doc in report_docs:
                r = doc.to_dict()
                report_list.append({
                    "Date & Time": r['timestamp'],
                    "Actual Savings (RM)": f"RM {r.get('actual_savings_rm', 0):.2f}",
                    "AI Forecast (RM)": f"RM {r.get('forecast_savings_rm', 0):.2f}",
                    "Actual Gen (kWh)": f"{r.get('actual_kwh_est', 0):.2f}",
                    "AI Gen (kWh)": f"{r.get('forecast_kwh', 0):.2f}",
                })
            
            if report_list:
                report_df = pd.DataFrame(report_list)
                report_df['Date & Time'] = pd.to_datetime(report_df['Date & Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(report_df, use_container_width=True)
            else:
                st.info("No reports generated yet.")

        except Exception as e:
            st.warning(f"Could not load history: {e}")

    else:
        st.warning("⚠️ Collecting more data to calibrate AI model...")

# --- AUTO-REFRESH LOGIC ---
if live_mode:
    time.sleep(3)
    st.rerun()

