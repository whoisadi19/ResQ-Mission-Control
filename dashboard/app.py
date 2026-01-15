import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from ultralytics import YOLO
import numpy as np
import cv2
from pathlib import Path
import time
import gc

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RESQ LIVE OPS", page_icon="🚁", layout="wide")
gc.collect() 

# --- 2. CREDENTIALS ---
GEMINI_KEY = "AIzaSyBSURSwvegn0gop6uPH4lG-ExZkvaagbuw"
SUPABASE_URL = "https://wuzhsricuvjgvtiiylhz.supabase.co"
SUPABASE_KEY = "sb_publishable_ZPld2JKhdzKJbw2N6CcQgw_1M4SAbu7"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# --- 3. LOAD YOLO MODEL ---
@st.cache_resource
def load_yolo():
    possible_paths = [Path("best.pt"), Path("dashboard/best.pt")]
    for path in possible_paths:
        if path.exists(): 
            return YOLO(str(path))
    return None

yolo_model = load_yolo()

# --- 4. STABLE PROFESSIONAL STYLING ---
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0f1419 0%, #1a202c 100%);
        color: #e2e8f0;
    }
    [data-testid="metric-container"] {
        background: rgba(15, 20, 25, 0.9);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] { 
        color: #3b82f6 !important; 
        font-weight: 700;
        font-size: 1.8rem;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.title("RESQ Live Operations")

# --- 5. GLOBAL LAYOUT & CONTROLS ---
stats_row = st.empty()
col_intel, col_map, col_chat = st.columns([1.5, 2, 1])

# Store source and is_live in session_state for stability
if "source" not in st.session_state:
    st.session_state.source = 0
if "is_live" not in st.session_state:
    st.session_state.is_live = False

with col_intel:
    st.markdown("### Mission Feed")
    
    cam_option = st.selectbox(
        "Select Video Source", 
        ["Camera 1 (DroidCam/USB)", "Camera 0 (Laptop)", "Camera 2", "IP Webcam URL"], 
        key="cam_select"
    )
    
    # Update source safely
    if cam_option == "Camera 1 (DroidCam/USB)":
        st.session_state.source = 1
    elif cam_option == "Camera 0 (Laptop)":
        st.session_state.source = 0
    elif cam_option == "Camera 2":
        st.session_state.source = 2
    else:
        st.session_state.source = st.text_input("Enter URL (e.g. http://192.168.x.x:4747/video)", key="url_input")
    
    st.session_state.is_live = st.toggle("Activate Live Vision", value=st.session_state.is_live, key="live_toggle")
    video_placeholder = st.empty()

# --- 6. FIXED STABLE MISSION LOOP ---
@st.fragment(run_every=5)
def update_mission_data():
    source = st.session_state.source
    is_live = st.session_state.is_live
    
    # SINGLE FRAME PROCESSING - NO INFINITE LOOP
    if is_live and yolo_model:
        cap = None
        try:
            if isinstance(source, int):
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(source)
            
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    results = yolo_model(frame, conf=0.5, verbose=False)
                    annotated = results[0].plot()
                    rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
        except:
            video_placeholder.error(f"Cannot connect to Source {source}")
        finally:
            if cap:
                cap.release()
    else:
        video_placeholder.empty()

    # SAFE TELEMETRY
    try:
        res = supabase.table("telemetry").select("*").order("created_at", desc=True).limit(50).execute()
        all_data = res.data or []
    except:
        all_data = []

    if all_data:
        latest = all_data[0]
        
        # SAFE METRICS
        try:
            with stats_row.container():
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Battery", f"{latest.get('battery', 0)}%")
                k2.metric("Latitude", f"{latest.get('latitude', 0):.4f}")
                k3.metric("Longitude", f"{latest.get('longitude', 0):.4f}")
                k4.metric("Sync", time.strftime('%H:%M:%S'))
        except:
            pass

        # SAFE GALLERY
        if not is_live and len(all_data) > 0:
            images = [d for d in all_data if d.get('image_url')][:3]
            if images:
                st.caption("Cloud Intel Archive")
                for img in images:
                    st.image(img['image_url'], use_column_width=True)

        # SAFE MAP
        try:
            with col_map:
                st.subheader("Tactical Overlay")
                m = folium.Map(
                    location=[latest.get('latitude', 19.0), latest.get('longitude', 72.0)], 
                    zoom_start=18
                )
                folium.TileLayer(
                    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                    attr='Esri'
                ).add_to(m)
                
                heat_data = [[d.get('latitude', 19.0), d.get('longitude', 72.0), 1] for d in all_data[:20]]
                HeatMap(heat_data, radius=10, blur=8).add_to(m)
                
                folium.Marker(
                    [latest.get('latitude', 19.0), latest.get('longitude', 72.0)], 
                    icon=folium.Icon(color="orange", icon="plane")
                ).add_to(m)
                
                st_folium(m, width=700, height=500, key="live_ops_map")
        except:
            pass

# --- 7. SAFE MISSION AI CHAT ---
with col_chat:
    st.subheader("Mission AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    chat_box = st.container(height=500)
    for msg in st.session_state.messages:
        chat_box.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Tactical Command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_box.chat_message("user").write(prompt)
        
        try:
            response = gemini_model.generate_content(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.session_state.messages.append({"role": "assistant", "content": "AI response unavailable"})
        
        st.rerun()

# Execute Dashboard
update_mission_data()