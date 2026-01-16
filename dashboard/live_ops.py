import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import time
import cv2
from ultralytics import YOLO
import numpy as np

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="ResQ Operations", layout="wide", initial_sidebar_state="collapsed")

# Load YOLO Model
@st.cache_resource
def load_yolo():
    try:
        return YOLO("FINAL_RESCUE_MODEL.pt")
    except:
        return YOLO("yolov8n.pt") 

model_yolo = load_yolo()

# Get API key from Streamlit secrets (for cloud) or fallback to hardcoded (for local)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # Fallback for local development
    api_key = "AIzaSyBSURSwvegn0gop6uPH4lG-ExZkvaagbuw"
    SUPABASE_URL = "https://wuzhsricuvjgvtiiylhz.supabase.co"
    SUPABASE_KEY = "sb_publishable_ZPld2JKhdzKJbw2N6CcQgw_1M4SAbu7"

if not api_key:
    st.error("❌ API Key Missing! Check your Streamlit secrets.")
else:
    genai.configure(api_key=api_key)
    
model_ai = genai.GenerativeModel('gemini-2.5-flash')

# Supabase Connection
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    supabase = None

# --- 2. CSS: TACTICAL GLASS THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* Main Background */
    .stApp {
        background: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                    radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                    radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-color: #0B0D11;
        background-attachment: fixed;
    }
    
    /* Remove default Streamlit top padding so there is no empty gap */
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important;
    }

    * { font-family: 'Plus Jakarta Sans', sans-serif !important; color: #FFFFFF !important; }

    /* NEW TACTICAL HEADER */
    .mission-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px 25px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    .header-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 1px;
        background: linear-gradient(90deg, #FFFFFF, #B0B0B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .status-badge {
        font-family: 'Courier New', monospace;
        color: #00FF41;
        background: rgba(0, 255, 65, 0.1);
        padding: 5px 12px;
        border-radius: 4px;
        border: 1px solid rgba(0, 255, 65, 0.3);
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 65, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 65, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 65, 0); }
    }

    /* Glass Cards for Columns */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] { 
        color: #00FF41 !important; 
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.5); 
        font-size: 2rem !important; 
    }
    
    header, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. NEW HEADER & TELEMETRY ---
st.markdown("""
<div class="mission-header">
    <div>
        <div class="header-title">RESQ // MISSION CONTROL</div>
        <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 5px;">AERIAL SURVEILLANCE UNIT</div>
    </div>
    <div class="status-badge">● SYSTEM ONLINE</div>
</div>
""", unsafe_allow_html=True)

@st.fragment(run_every=2.0)
def update_telemetry():
    # CHANGED: Default coordinates to NMIMS Shirpur
    if "telemetry" not in st.session_state:
        st.session_state.telemetry = {"bat": 85, "lat": 21.2863, "lon": 74.8028}
    
    if supabase:
        try:
            res = supabase.table("telemetry").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data:
                d = res.data[0]
                st.session_state.telemetry = {
                    "bat": d.get('battery', 85), 
                    "lat": d.get('latitude', 21.2863), 
                    "lon": d.get('longitude', 74.8028)
                }
        except: pass
        
    t1, t2, t3, t4 = st.columns(4)
    tel = st.session_state.telemetry
    t1.metric("BATTERY", f"{tel['bat']}%")
    t2.metric("LATITUDE", f"{tel['lat']:.4f}")
    t3.metric("LONGITUDE", f"{tel['lon']:.4f}")
    t4.metric("SIGNAL", "STRONG")

update_telemetry()

# --- 4. MAIN INTERFACE GRID ---
col_video, col_map, col_chat = st.columns([1.5, 2, 1])

with col_video:
    st.markdown("###  Live Optics")
    
    v_c1, v_c2 = st.columns(2)
    user_id = v_c1.text_input("Username", value="admin")
    user_pw = v_c2.text_input("Password", type="password")
    ip_raw = st.text_input("Phone IP", value="10.221.13.120:8081")
    
    is_streaming = st.toggle("Activate Vision Feed", value=False)
    vision_placeholder = st.empty()

with col_map:
    st.markdown("###  Tactical Map")
    tel = st.session_state.get("telemetry", {"lat": 21.2863, "lon": 74.8028})
    map_df = pd.DataFrame({'lat': [tel['lat']], 'lon': [tel['lon']]})
    
    
    st.map(map_df, zoom=16, color="#D52929", use_container_width=True) 

with col_chat:
    st.markdown("###  Mission AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=250)
    with chat_box:
        for m in st.session_state.messages: 
            st.markdown(f"**{m['role'].upper()}**: {m['content']}")
            
    if prompt := st.chat_input("Command AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        tel_data = st.session_state.telemetry
        ctx = f"ResQ-AI. Bat: {tel_data['bat']}%. User: {prompt}"
        try:
            r = model_ai.generate_content(ctx)
            st.session_state.messages.append({"role": "assistant", "content": r.text})
            st.rerun() 
        except Exception as e:
            st.error(f"AI Error: {e}")

# --- 5. VISION LOOP (Persistent & Non-Blocking) ---
if is_streaming and ip_raw:
    clean_ip = ip_raw.replace("http://", "").replace("https://", "").strip()
    stream_url = f"http://{user_id}:{user_pw}@{clean_ip}/video"
    
    if 'cap' not in st.session_state or not st.session_state.cap.isOpened():
        st.session_state.cap = cv2.VideoCapture(stream_url)
        st.session_state.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        
    cap = st.session_state.cap

    if not cap.isOpened():
        st.error("❌ Connection Failed. Check IP/Hotspot.")
    else:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.warning("📡 Signal Lost. Reconnecting...")
                st.session_state.cap.release()
                del st.session_state.cap
                break
                
            results = model_yolo.predict(frame, conf=0.3, verbose=False)
            annotated_frame = results[0].plot()
            
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            
          
            vision_placeholder.image(frame_rgb, channels="RGB", width="stretch")
            
            time.sleep(0.01)
else:
    if 'cap' in st.session_state:
        st.session_state.cap.release()
        del st.session_state.cap