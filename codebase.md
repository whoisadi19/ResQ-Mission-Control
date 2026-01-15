# dashboard/app.py

```py
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
```

# edge_node/best.pt

This is a binary file of the type: Binary

# dashboard/best.pt

This is a binary file of the type: Binary

# edge_node/check_env.py

```py
import torch
import cv2
import ultralytics
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"OpenCV Version: {cv2.__version__}")
print(f"YOLO Ready: {ultralytics.__version__}")
```

# edge_node/cloud_uplink.py

```py
import os
from supabase import create_client, Client
import time
import random
import json

# --- CONFIGURATION ---
# 1. Your Project URL (I copied this from your screenshot)
SUPABASE_URL = "https://wuzhsricuvjgvtiiylhz.supabase.co"

# 2. PASTE YOUR KEY BELOW (The one labeled "anon" or "public")
SUPABASE_KEY = "sb_publishable_ZPld2JKhdzKJbw2N6CcQgw_1M4SAbu7"

# Initialize Connection to the Cloud
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase Cloud")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    supabase = None

def upload_image(image_path, filename):
    """
    Takes a photo from the drone, uploads it to the cloud, 
    and returns a web link (URL) so the dashboard can display it.
    """
    if not supabase: return None
    
    try:
        with open(image_path, 'rb') as f:
            # Upload to the 'mission-images' bucket
            supabase.storage.from_("mission-images").upload(
                path=filename,
                file=f,
                file_options={"content-type": "image/jpeg"}
            )
        
        # Create the public link
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/mission-images/{filename}"
        return public_url
        
    except Exception as e:
        print(f"❌ Image Upload Error: {e}")
        return None

def send_telemetry(lat, lon, batt, status, image_url=None):
    """
    Sends GPS, Battery, and Status data to the 'telemetry' table.
    """
    if not supabase: return

    data = {
        "latitude": lat,
        "longitude": lon,
        "battery": batt,
        "status": status,
        "image_url": image_url
    }
    
    try:
        # Insert the data into the database
        supabase.table("telemetry").insert(data).execute()
        print(f"📡 Data Sent: Bat={batt}% | Lat={lat:.4f}")
    except Exception as e:
        print(f"❌ Data Send Error: {e}")

# --- TEST MODE ---
# If you run this file directly, it will simulate a flying drone
if __name__ == "__main__":
    print("🚀 Simulation Started: Sending fake data to cloud...")
    
    # Starting coordinates (Mumbai)
    lat, lon = 19.0760, 72.8777
    
    while True:
        # 1. Simulate movement
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)
        batt = random.randint(80, 100)
        
        # 2. Send data
        send_telemetry(lat, lon, batt, "Patrolling Sector 7")
        
        # 3. Wait 2 seconds
        time.sleep(2)
```

# command_center/dashboard.py

```py
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
```

# edge_node/data.yaml

```yaml
# RESQ TACTICAL DATASET CONFIG
# Use forward slashes / even on Windows to prevent path errors

path: C:/Users/User/OneDrive/Desktop/flood-rescue-system/datasets  # Base directory
train: images/train  # Relative to 'path' above
val: images/val      # Relative to 'path' above

# Number of classes (Change this based on your dataset)
nc: 1 

# Class Names (No emojis for a classy look)
names: ['Victim']
```

# edge_node/demo_proof.py

```py
from ultralytics import YOLO
import os
import random
import cv2

# --- CONFIG ---
MODEL_PATH = "FINAL_RESCUE_MODEL.pt"

# We check a few possible places just to be safe
POSSIBLE_PATHS = [
    "../training/datasets/images/train",
    "../training/datasets/images/val",
    r"../training/datasets/train/images"  # Backup structure
]

def run_demo():
    print(f"🧠 Loading {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # 1. Find the images folder
    found_dir = None
    for path in POSSIBLE_PATHS:
        
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            
            files = os.listdir(abs_path)
            
            if any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) for f in files):
                found_dir = abs_path
                print(f"✅ Found images in: {found_dir}")
                break
    
    if not found_dir:
        print("❌ CRITICAL: Could not find any image folder!")
        print("   I looked in these spots:")
        for p in POSSIBLE_PATHS:
            print(f"   - {os.path.abspath(p)}")
        return

    
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
    all_images = [f for f in os.listdir(found_dir) if f.lower().endswith(valid_exts)]
    
    
    selected_images = random.sample(all_images, min(6, len(all_images)))
    print(f"📸 Selected {len(selected_images)} images to test.")

    for img_name in selected_images:
        img_path = os.path.join(found_dir, img_name)
        
       
        results = model.predict(img_path, conf=0.25)
        
        for result in results:
            
            res_plotted = result.plot()
            
            
            window_name = f"Detection Proof: {img_name}"
            cv2.imshow(window_name, res_plotted)
            
            print(f"👀 Showing {img_name}... Press any key to see next.")
            cv2.waitKey(0) 

    cv2.destroyAllWindows()
    print("✅ Demo Complete!")

if __name__ == "__main__":
    run_demo()
```

# edge_node/FINAL_RESCUE_MODEL.pt

This is a binary file of the type: Binary

# edge_node/flood_footage.mp4

This is a binary file of the type: Binary

# edge_node/hackathon_model.pt

This is a binary file of the type: Binary

# dashboard/live_ops.py

```py
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
    # Looks for best.pt in the current folder or dashboard folder
    possible_paths = [Path("best.pt"), Path("dashboard/best.pt")]
    for path in possible_paths:
        if path.exists(): 
            return YOLO(str(path))
    return None

yolo_model = load_yolo()

# --- 4. TACTICAL UI STYLING ---
st.markdown("""
<style>
    .stApp { background: #0b0d11; color: #e0e0e0; }
    [data-testid="stMetricValue"] { color: #00FF41 !important; font-family: 'Courier New', monospace; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1E1E1E; border-radius: 4px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #00FF41 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

st.title("🚁 RESQ // LIVE OPERATIONS")

# --- 5. GLOBAL LAYOUT & CONTROLS ---
stats_row = st.empty()
col_intel, col_map, col_chat = st.columns([1.5, 2, 1])

with col_intel:
    st.markdown("### 📡 MISSION FEED")
    
    # Selection for different camera indices
    cam_option = st.selectbox(
        "Select Video Source", 
        ["Camera 1 (DroidCam/USB)", "Camera 0 (Laptop)", "Camera 2", "IP Webcam URL"], 
        key="cam_select"
    )
    
    # Logic to assign the correct source
    if cam_option == "Camera 1 (DroidCam/USB)":
        source = 1
    elif cam_option == "Camera 0 (Laptop)":
        source = 0
    elif cam_option == "Camera 2":
        source = 2
    else:
        source = st.text_input("Enter URL (e.g. http://192.168.x.x:4747/video)")
        
    is_live = st.toggle("🔴 ACTIVATE LIVE VISION", value=False, key="live_toggle")
    video_placeholder = st.empty()

# --- 6. MAIN MISSION LOOP (Fragment) ---
@st.fragment(run_every=4)
def update_mission_data():
    # A. Live Camera Logic
    if is_live and yolo_model:
        # Use CAP_DSHOW for Windows to find virtual cameras better
        if isinstance(source, int):
            cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            video_placeholder.error(f"❌ Cannot connect to Source {source}. Ensure DroidCam is active.")
        
        while is_live and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # AI Inference & Annotation
            results = yolo_model(frame, conf=0.5, verbose=False)
            annotated = results[0].plot()
            rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            
            # Display high-speed frame
            video_placeholder.image(rgb_frame, channels="RGB", width="stretch")
            
        cap.release()
        return 

    # B. Telemetry & Map Logic
    try:
        res = supabase.table("telemetry").select("*").order("created_at", desc=True).limit(50).execute()
        all_data = res.data
    except:
        return

    if all_data:
        latest = all_data[0]
        
        # Update Top Metrics
        with stats_row.container():
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("🔋 BATTERY", f"{latest['battery']}%")
            k2.metric("🛰️ LAT", f"{latest['latitude']:.4f}")
            k3.metric("🛰️ LON", f"{latest['longitude']:.4f}")
            k4.metric("⏱️ SYNC", time.strftime('%H:%M:%S'))

        # Show Gallery only if camera is OFF
        if not is_live:
            video_placeholder.empty()
            with col_intel:
                st.caption("📸 CLOUD INTEL ARCHIVE")
                images = [d for d in all_data if d.get('image_url')][:3]
                for img in images:
                    st.image(img['image_url'], width="stretch")

        # Update Tactical Map
        with col_map:
            st.subheader("📍 TACTICAL OVERLAY")
            m = folium.Map(location=[latest['latitude'], latest['longitude']], zoom_start=18)
            folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
            
            # Heatmap of past detections
            heat_data = [[d['latitude'], d['longitude'], 1] for d in all_data]
            HeatMap(heat_data, radius=10, blur=8).add_to(m)
            
            # Current Drone Marker
            folium.Marker(
                [latest['latitude'], latest['longitude']], 
                icon=folium.Icon(color="orange", icon="plane")
            ).add_to(m)
            
            st_folium(m, width=700, height=500, key="live_ops_map")

# --- 7. MISSION AI CHAT ---
with col_chat:
    st.subheader("🤖 MISSION AI")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    chat_box = st.container(height=500)
    for msg in st.session_state.messages:
        chat_box.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Tactical Command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_box.chat_message("user").write(prompt)
        response = gemini_model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()

# Execute Dashboard
update_mission_data()
```

# edge_node/rescue_detection_output.mp4

This is a binary file of the type: Binary

# edge_node/runs\detect\resq_ULTIMATE_v3\args.yaml

```yaml
task: detect
mode: train
model: hackathon_model.pt
data: C:/Users/User/OneDrive/Desktop/flood-rescue-system/training/datasets/custom_flood.yaml
epochs: 30
time: null
patience: 15
batch: 4
imgsz: 1280
save: true
save_period: -1
cache: false
device: null
workers: 1
project: null
name: resq_ULTIMATE_v3
exist_ok: true
pretrained: true
optimizer: auto
verbose: true
seed: 0
deterministic: true
single_cls: false
rect: false
cos_lr: false
close_mosaic: 10
resume: false
amp: true
fraction: 1.0
profile: false
freeze: null
multi_scale: false
compile: false
overlap_mask: true
mask_ratio: 4
dropout: 0.0
val: true
split: val
save_json: false
conf: null
iou: 0.7
max_det: 300
half: false
dnn: false
plots: true
source: null
vid_stride: 1
stream_buffer: false
visualize: false
augment: true
agnostic_nms: false
classes: null
retina_masks: false
embed: null
show: false
save_frames: false
save_txt: false
save_conf: false
save_crop: false
show_labels: true
show_conf: true
show_boxes: true
line_width: null
format: torchscript
keras: false
optimize: false
int8: false
dynamic: false
simplify: true
opset: null
workspace: null
nms: false
lr0: 0.01
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3.0
warmup_momentum: 0.8
warmup_bias_lr: 0.1
box: 7.5
cls: 0.5
dfl: 1.5
pose: 12.0
kobj: 1.0
nbs: 64
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 0.0
translate: 0.1
scale: 0.5
shear: 0.0
perspective: 0.0
flipud: 0.0
fliplr: 0.5
bgr: 0.0
mosaic: 1.0
mixup: 0.0
cutmix: 0.0
copy_paste: 0.0
copy_paste_mode: flip
auto_augment: randaugment
erasing: 0.4
cfg: null
tracker: botsort.yaml
save_dir: C:\Users\User\OneDrive\Desktop\flood-rescue-system\edge_node\runs\detect\resq_ULTIMATE_v3

```

# edge_node/runs\detect\resq_ULTIMATE_v3\BoxF1_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\BoxP_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\BoxPR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\BoxR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\confusion_matrix_normalized.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\confusion_matrix.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\results.csv

```csv
epoch,time,train/box_loss,train/cls_loss,train/dfl_loss,metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B),val/box_loss,val/cls_loss,val/dfl_loss,lr/pg0,lr/pg1,lr/pg2
1,599.92,0.93206,1.40172,0.99738,0.1827,0.7247,0.17518,0.12795,0.69522,73.1245,0.81297,0.00066634,0.00066634,0.00066634
2,1174.33,0.95157,1.15321,1.00691,0.18166,0.71541,0.16825,0.1208,0.71218,92.7336,0.81741,0.00128902,0.00128902,0.00128902
3,1748.96,0.95262,1.15747,1.00385,0.18218,0.72694,0.16991,0.12149,0.68289,82.3839,0.81034,0.0018677,0.0018677,0.0018677
4,2325.92,0.95675,1.17594,1.0039,0.18394,0.72827,0.17303,0.12326,0.70446,66.9187,0.8077,0.001802,0.001802,0.001802
5,2895.03,0.94459,1.14098,0.99472,0.18309,0.72318,0.17194,0.12489,0.68981,73.9593,0.80797,0.001736,0.001736,0.001736
6,3463.44,0.93923,1.13241,0.99431,0.18369,0.72476,0.17394,0.12408,0.69673,83.0767,0.80779,0.00167,0.00167,0.00167
7,4031.34,0.93668,1.1481,0.99528,0.18269,0.73424,0.17054,0.12513,0.67929,78.5882,0.80609,0.001604,0.001604,0.001604
8,4598.84,0.92217,1.20535,0.99016,0.18339,0.73798,0.17129,0.12596,0.67542,75.5227,0.80336,0.001538,0.001538,0.001538
9,5175.31,0.92818,1.26887,0.99242,0.18441,0.73522,0.17245,0.12572,0.67166,99.079,0.80465,0.001472,0.001472,0.001472
10,5757.24,0.90906,1.1355,0.98666,0.18428,0.74025,0.17116,0.12679,0.65461,80.0121,0.79614,0.001406,0.001406,0.001406
11,6324.16,0.90723,1.14098,0.9881,0.1841,0.74355,0.17509,0.13044,0.65217,81.7893,0.79923,0.00134,0.00134,0.00134
12,6894.19,0.89814,1.18678,0.98541,0.18414,0.74038,0.17305,0.12906,0.65236,71.4317,0.79917,0.001274,0.001274,0.001274
13,7488.6,0.89558,1.28643,0.98243,0.18229,0.75022,0.17053,0.12628,0.6517,98.9962,0.79758,0.001208,0.001208,0.001208
14,8064.27,0.90041,1.13154,0.98248,0.18351,0.74782,0.17221,0.12708,0.65393,84.9877,0.79826,0.001142,0.001142,0.001142
15,8632.01,0.89186,1.1282,0.97842,0.1854,0.74871,0.17341,0.12987,0.63406,86.4662,0.79092,0.001076,0.001076,0.001076
16,9202.82,0.88278,1.09632,0.97698,0.18418,0.74197,0.17297,0.12871,0.64584,80.3922,0.7953,0.00101,0.00101,0.00101
17,11880.5,0.87448,1.13021,0.97469,0.18499,0.74892,0.17247,0.12961,0.62864,81.8668,0.78898,0.000944,0.000944,0.000944
18,12450.5,0.86954,1.12945,0.97496,0.18599,0.73419,0.17644,0.13083,0.62767,87.5844,0.79011,0.000878,0.000878,0.000878
19,13030.1,0.86746,1.09179,0.97381,0.18369,0.7474,0.17457,0.1314,0.62874,84.8834,0.78847,0.000812,0.000812,0.000812
20,13597,0.863,1.08663,0.96773,0.18614,0.74699,0.17688,0.1309,0.62355,75.5608,0.78786,0.000746,0.000746,0.000746
21,14156.5,0.84509,4.02306,0.95942,0.18024,0.78153,0.17345,0.12754,0.63556,26.8421,0.79032,0.00068,0.00068,0.00068
22,14710.4,0.82919,3.07821,0.94914,0.18243,0.77555,0.17398,0.13019,0.6261,42.5615,0.78852,0.000614,0.000614,0.000614
23,15263.5,0.82006,3.77652,0.94406,0.17906,0.79626,0.17209,0.12738,0.63268,17.1425,0.79226,0.000548,0.000548,0.000548
24,15817.1,0.81381,3.46116,0.94269,0.18029,0.79419,0.17554,0.13031,0.62899,28.9002,0.78976,0.000482,0.000482,0.000482
25,16370.9,0.81535,3.5116,0.94631,0.18248,0.78243,0.17605,0.13229,0.62578,31.9206,0.78719,0.000416,0.000416,0.000416
26,16924.7,0.81257,3.64182,0.94372,0.18359,0.77135,0.1765,0.13339,0.62285,35.2282,0.78681,0.00035,0.00035,0.00035
27,17478.3,0.80099,3.59865,0.9444,0.18447,0.76653,0.17851,0.13129,0.61899,48.6732,0.78894,0.000284,0.000284,0.000284
28,18031.6,0.80066,4.07565,0.94196,0.1847,0.76213,0.17692,0.13202,0.61851,46.8419,0.78648,0.000218,0.000218,0.000218
29,18585,0.7919,4.09562,0.93869,0.18472,0.7635,0.17781,0.13373,0.61213,40.9599,0.7838,0.000152,0.000152,0.000152
30,19138.7,0.78967,3.83698,0.93619,0.18448,0.76949,0.17754,0.1324,0.61114,47.7314,0.78454,8.6e-05,8.6e-05,8.6e-05

```

# edge_node/runs\detect\resq_ULTIMATE_v3\results.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch0.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch1.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch2.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch40860.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch40861.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\train_batch40862.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch0_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch0_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch1_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch1_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch2_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\val_batch2_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_ULTIMATE_v3\weights\best.pt

This is a binary file of the type: Binary

# edge_node/runs\detect\resq_ULTIMATE_v3\weights\last.pt

This is a binary file of the type: Binary

# edge_node/runs\detect\resq_v2_fine_tuned\args.yaml

```yaml
task: detect
mode: train
model: best.pt
data: C:/Users/User/OneDrive/Desktop/flood-rescue-system/training/datasets/custom_flood.yaml
epochs: 30
time: null
patience: 100
batch: 8
imgsz: 640
save: true
save_period: -1
cache: false
device: '0'
workers: 2
project: null
name: resq_v2_fine_tuned
exist_ok: true
pretrained: true
optimizer: auto
verbose: true
seed: 0
deterministic: true
single_cls: false
rect: false
cos_lr: false
close_mosaic: 10
resume: false
amp: true
fraction: 1.0
profile: false
freeze: null
multi_scale: false
compile: false
overlap_mask: true
mask_ratio: 4
dropout: 0.0
val: true
split: val
save_json: false
conf: null
iou: 0.7
max_det: 300
half: false
dnn: false
plots: true
source: null
vid_stride: 1
stream_buffer: false
visualize: false
augment: false
agnostic_nms: false
classes: null
retina_masks: false
embed: null
show: false
save_frames: false
save_txt: false
save_conf: false
save_crop: false
show_labels: true
show_conf: true
show_boxes: true
line_width: null
format: torchscript
keras: false
optimize: false
int8: false
dynamic: false
simplify: true
opset: null
workspace: null
nms: false
lr0: 0.01
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3.0
warmup_momentum: 0.8
warmup_bias_lr: 0.1
box: 7.5
cls: 0.5
dfl: 1.5
pose: 12.0
kobj: 1.0
nbs: 64
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 0.0
translate: 0.1
scale: 0.5
shear: 0.0
perspective: 0.0
flipud: 0.0
fliplr: 0.5
bgr: 0.0
mosaic: 1.0
mixup: 0.0
cutmix: 0.0
copy_paste: 0.0
copy_paste_mode: flip
auto_augment: randaugment
erasing: 0.4
cfg: null
tracker: botsort.yaml
save_dir: C:\Users\User\OneDrive\Desktop\flood-rescue-system\edge_node\runs\detect\resq_v2_fine_tuned

```

# edge_node/runs\detect\resq_v2_fine_tuned\BoxF1_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\BoxP_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\BoxPR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\BoxR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\confusion_matrix_normalized.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\confusion_matrix.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\results.csv

```csv
epoch,time,train/box_loss,train/cls_loss,train/dfl_loss,metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B),val/box_loss,val/cls_loss,val/dfl_loss,lr/pg0,lr/pg1,lr/pg2
1,167.207,1.11227,1.11386,0.94223,0.18056,0.60345,0.15314,0.0973,1.03666,12.3853,0.90891,0.000666014,0.000666014,0.000666014
2,324.261,1.16191,1.14543,0.9546,0.17594,0.6016,0.15038,0.09634,1.04151,19.8632,0.91545,0.0012887,0.0012887,0.0012887
3,479.548,1.16781,1.1504,0.95648,0.17754,0.58508,0.14835,0.09466,1.03868,15.8165,0.90947,0.00186739,0.00186739,0.00186739
4,633.975,1.18658,1.1685,0.95591,0.17721,0.59169,0.15,0.0968,1.02555,13.5619,0.90501,0.001802,0.001802,0.001802
5,788.345,1.1714,1.1515,0.95748,0.17787,0.60476,0.15082,0.09541,1.0411,14.0525,0.90759,0.001736,0.001736,0.001736
6,942.902,1.1765,1.15222,0.95917,0.17813,0.60552,0.1487,0.09559,1.01695,15.953,0.90208,0.00167,0.00167,0.00167
7,1097.08,1.15771,1.13325,0.95652,0.17875,0.61102,0.15447,0.10172,1.01926,17.3972,0.90325,0.001604,0.001604,0.001604
8,1251.18,1.14698,1.13927,0.95149,0.17909,0.6071,0.15111,0.09768,1.01082,15.873,0.90447,0.001538,0.001538,0.001538
9,1406.18,1.14369,1.12516,0.95016,0.17816,0.59176,0.14844,0.09503,1.04226,16.1658,0.91438,0.001472,0.001472,0.001472
10,1560.42,1.13917,1.12341,0.95065,0.17774,0.61966,0.14911,0.09709,0.99506,14.2461,0.89731,0.001406,0.001406,0.001406
11,1714.85,1.13783,1.1308,0.9491,0.17924,0.61295,0.15681,0.10319,0.98995,14.547,0.89738,0.00134,0.00134,0.00134
12,1869.13,1.12626,1.12868,0.94739,0.17885,0.6146,0.153,0.10065,0.98852,16.4157,0.89908,0.001274,0.001274,0.001274
13,2023.85,1.12213,1.10538,0.94528,0.17951,0.62403,0.15171,0.10037,0.96388,18.6808,0.8902,0.001208,0.001208,0.001208
14,2178.17,1.11645,1.11542,0.94537,0.17752,0.62946,0.15094,0.09861,0.98459,16.8962,0.89512,0.001142,0.001142,0.001142
15,2331.93,1.10669,1.10831,0.94153,0.17826,0.62527,0.15146,0.09847,0.98289,16.218,0.89944,0.001076,0.001076,0.001076
16,2485.84,1.10533,1.10148,0.94023,0.17982,0.62375,0.1529,0.10037,0.9688,15.4953,0.89427,0.00101,0.00101,0.00101
17,2639.97,1.10145,1.10721,0.93928,0.17937,0.62425,0.15135,0.09984,0.96229,15.4493,0.89006,0.000944,0.000944,0.000944
18,2794.23,1.09593,1.10013,0.94057,0.17973,0.62437,0.1544,0.10179,0.95166,17.1846,0.88969,0.000878,0.000878,0.000878
19,2948.15,1.08813,1.07967,0.93765,0.17861,0.6263,0.15357,0.10275,0.95516,18.2554,0.89155,0.000812,0.000812,0.000812
20,3102.56,1.08043,1.08476,0.9366,0.17964,0.63249,0.15444,0.10261,0.94164,16.5573,0.88785,0.000746,0.000746,0.000746
21,3260.16,1.04388,1.14709,0.93943,0.17865,0.63578,0.15341,0.10263,0.93925,15.7948,0.88884,0.00068,0.00068,0.00068
22,3411.11,1.04855,1.14628,0.93837,0.17915,0.63421,0.15352,0.10191,0.95205,15.8045,0.89107,0.000614,0.000614,0.000614
23,3561.55,1.04046,1.12907,0.93715,0.17979,0.62816,0.15649,0.10451,0.94354,15.738,0.8903,0.000548,0.000548,0.000548
24,3712.54,1.03018,1.15597,0.93438,0.18037,0.6242,0.15445,0.10293,0.93625,15.1245,0.88508,0.000482,0.000482,0.000482
25,3863.17,1.02245,1.80624,0.93028,0.1804,0.62437,0.15544,0.10408,0.93727,17.6182,0.88817,0.000416,0.000416,0.000416
26,4013.46,1.01424,1.31278,0.92897,0.18103,0.63771,0.15684,0.10413,0.93238,16.8309,0.88662,0.00035,0.00035,0.00035
27,4163.61,1.00989,1.11026,0.93021,0.18071,0.63524,0.15683,0.10569,0.92424,16.4941,0.88444,0.000284,0.000284,0.000284
28,4314.32,1.00519,1.12095,0.92599,0.18132,0.62988,0.15713,0.10564,0.92079,14.8439,0.88436,0.000218,0.000218,0.000218
29,4465.09,0.99885,1.33716,0.92523,0.18069,0.63882,0.15627,0.10509,0.9192,14.4842,0.88314,0.000152,0.000152,0.000152
30,4615.85,0.98637,1.68663,0.92021,0.18091,0.6371,0.15645,0.10598,0.91483,15.8702,0.88229,8.6e-05,8.6e-05,8.6e-05

```

# edge_node/runs\detect\resq_v2_fine_tuned\results.png

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch0.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch1.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch2.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch20440.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch20441.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\train_batch20442.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch0_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch0_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch1_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch1_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch2_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\val_batch2_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\resq_v2_fine_tuned\weights\best.pt

This is a binary file of the type: Binary

# edge_node/runs\detect\resq_v2_fine_tuned\weights\last.pt

This is a binary file of the type: Binary

# edge_node/runs\detect\val\BoxF1_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\BoxP_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\BoxPR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\BoxR_curve.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\confusion_matrix_normalized.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\confusion_matrix.png

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch0_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch0_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch1_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch1_pred.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch2_labels.jpg

This is a binary file of the type: Image

# edge_node/runs\detect\val\val_batch2_pred.jpg

This is a binary file of the type: Image

# edge_node/video_demo.py

```py
import cv2
import os
from ultralytics import YOLO

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "FINAL_RESCUE_MODEL.pt")

def run_controlled_demo():
    # 1. FIND VIDEO
    video_file = None
    for f in os.listdir(BASE_DIR):
        if f.startswith("flood_footage") and f.lower().endswith(('.mp4', '.mov', '.avi')):
            video_file = os.path.join(BASE_DIR, f)
            break
            
    if not video_file:
        print("❌ Could not find video file!")
        return

    # 2. SETUP
    print(f"🧠 Loading Model... Please wait.")
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(video_file)
    
    # Speed variables (milliseconds of delay)
    current_delay = 30  # Start at normal speed
    mode_text = "NORMAL"

    print("\n🎮 MANUAL CONTROLS:")
    print(" [S] - SLOW MOTION")
    print(" [N] - NORMAL SPEED")
    print(" [F] - FAST MOTION")
    print(" [Q] - QUIT DEMO\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 3. RUN AI (Inference)
        results = model.predict(frame, conf=0.25, imgsz=1280, verbose=False)
        annotated_frame = results[0].plot()

        # 4. ADD TACTICAL OVERLAY (For the Judges)
        # Displays the current speed mode on the screen
        cv2.putText(annotated_frame, f"MODE: {mode_text}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "S: Slow | N: Normal | F: Fast", (50, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 5. SHOW AND CAPTURE KEYS
        cv2.imshow("ResQ-AI Tactical Control", annotated_frame)
        
        key = cv2.waitKey(current_delay) & 0xFF
        
        if key == ord('s'):      # SLOW: High delay
            current_delay = 150
            mode_text = "SLOW MOTION"
        elif key == ord('n'):    # NORMAL: Balanced delay
            current_delay = 30
            mode_text = "NORMAL"
        elif key == ord('f'):    # FAST: Minimal delay
            current_delay = 1
            mode_text = "FAST MOTION"
        elif key == ord('q'):    # QUIT
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Demo session closed.")

if __name__ == "__main__":
    run_controlled_demo()
```

# edge_node/yolo_inference.py

```py
import os
# Fix for 6GB VRAM fragmentation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from ultralytics import YOLO
import gc
import torch

def tactical_precision_training():
    # 1. Clean up GPU memory before starting
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 2. Load your current best brain
    model = YOLO("hackathon_model.pt") 

    # 3. Start Ultimate Refinement
    model.train(
        data="C:/Users/User/OneDrive/Desktop/flood-rescue-system/training/datasets/custom_flood.yaml",
        epochs=30,
        imgsz=1280,          # High resolution for better small object detection
        batch=4,             # Lower batch to prevent CUDA Out of Memory on 6GB VRAM
        workers=1,           # Windows stability fix
        mosaic=1.0,          # Essential for detecting survivors in complex scenes
        augment=True,        # General robustness boost
        name="resq_ULTIMATE_v3",
        exist_ok=True,
        patience=15,         # Auto-stops if no improvement for 15 rounds
        amp=True             # Uses mixed precision for faster training
    )

if __name__ == "__main__":
   
    tactical_precision_training()
```

# edge_node/yolo11n.pt

This is a binary file of the type: Binary

# edge_node/yolov8m.pt

This is a binary file of the type: Binary

# edge_node/yolov8n.pt

This is a binary file of the type: Binary

# edge_node/yolov8s.pt

This is a binary file of the type: Binary

