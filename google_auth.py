import requests
import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta

# Function to verify login with Google Cloud
def login_with_google(email, password, api_key):
    request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(request_url, json=payload)
    if response.status_code == 200:
        return True, response.json()['email']
    else:
        return False, response.json().get('error', {}).get('message', 'Unknown Error')

# UI Component for Login
def render_login(api_key):
    # [FIX] Unique key prevents clash with app.py
    cookie_manager = stx.CookieManager(key="auth_mgr")
    
    # 2. Check if we are already in Session State (Memory)
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    # 3. If NOT in memory, check the Browser Cookie
    # This runs when you refresh the page!
    if not st.session_state['authenticated']:
        user_cookie = cookie_manager.get(cookie='solar_user_email')
        if user_cookie:
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = user_cookie
            return True

    # 4. If still not authenticated, show the Login Form
    if not st.session_state['authenticated']:
        st.markdown("## Solar ATAP Monitoring Dashboard Login")
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                success, info = login_with_google(email, password, api_key)
                if success:
                    st.session_state['authenticated'] = True
                    st.session_state['user_email'] = info
                    
                    # SAVE COOKIE (Valid for 7 Days)
                    expires = datetime.now() + timedelta(days=7)
                    cookie_manager.set('solar_user_email', info, expires_at=expires)
                    
                    st.rerun()
                else:
                    st.error(f"Login Failed: {info}")
        return False
    else:
        return True