import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import time

# Try to import cv2, but make it optional for cloud deployment
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try to import YOLO, but make it optional for cloud deployment (since it requires cv2)
try:
    from ultralytics import YOLO
    import numpy as np
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    
if not CV2_AVAILABLE or not YOLO_AVAILABLE:
    st.info("Running in cloud mode: Camera and YOLO features disabled. Tactical Map and Mission AI are fully functional!")

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="ResQ // Mission Control", layout="wide", initial_sidebar_state="collapsed")

# Load YOLO Model
@st.cache_resource
def load_yolo():
    if not YOLO_AVAILABLE:
        return None
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
    st.error("API Key Missing! Check your Streamlit secrets.")
else:
    genai.configure(api_key=api_key)
    
model_ai = genai.GenerativeModel('gemini-2.5-flash')

# Supabase Connection
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    supabase = None

# --- 2. CSS: AEGIS COMMAND — TACTICAL LUMINANCE THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Manrope:wght@300;400;500;600;700;800&display=swap');
    
    /* ===== GLOBAL RESET & BASE ===== */
    :root {
        --bg-abyss: #0A0E1A;
        --bg-surface: #0f131f;
        --bg-container-low: #171b28;
        --bg-container: #1b1f2c;
        --bg-container-high: #262a37;
        --bg-container-highest: #313442;
        --bg-surface-bright: #353946;
        
        --primary: #00F0FF;
        --primary-dim: #00dbe9;
        --primary-glow: rgba(0, 240, 255, 0.15);
        --primary-glow-strong: rgba(0, 240, 255, 0.35);
        
        --secondary: #00FF41;
        --secondary-glow: rgba(0, 255, 65, 0.15);
        
        --tertiary: #FF2D55;
        --tertiary-glow: rgba(255, 45, 85, 0.15);
        
        --text-primary: #dfe2f3;
        --text-secondary: #b9cacb;
        --text-muted: #849495;
        --ghost-border: rgba(59, 73, 75, 0.25);
        --glass-bg: rgba(53, 57, 70, 0.35);
    }

    .stApp {
        background: var(--bg-abyss) !important;
        background-image: 
            radial-gradient(ellipse at 10% 0%, rgba(0, 240, 255, 0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 90% 0%, rgba(255, 45, 85, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 100%, rgba(0, 219, 233, 0.02) 0%, transparent 40%) !important;
        background-attachment: fixed !important;
    }

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }

    * { 
        font-family: 'Manrope', sans-serif !important; 
        color: var(--text-primary) !important; 
    }
    
    h1, h2, h3, h4, h5, h6, .header-title, .section-title, .metric-label, .status-badge {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    header, footer { visibility: hidden !important; }
    
    /* Hide default Streamlit elements */
    #MainMenu { visibility: hidden; }
    div[data-testid="stToolbar"] { display: none; }
    div[data-testid="stDecoration"] { display: none; }
    div[data-testid="stStatusWidget"] { display: none; }

    /* ===== LIVE DOT INDICATOR ===== */
    .live-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--secondary);
        vertical-align: middle;
        margin-right: 2px;
        animation: live-pulse 2s ease-in-out infinite;
        box-shadow: 0 0 4px rgba(0, 255, 65, 0.6);
    }
    
    .live-dot.green {
        background: var(--secondary);
        box-shadow: 0 0 4px rgba(0, 255, 65, 0.6);
    }

    @keyframes live-pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 4px rgba(0, 255, 65, 0.6); }
        50% { opacity: 0.5; box-shadow: 0 0 10px rgba(0, 255, 65, 0.9), 0 0 20px rgba(0, 255, 65, 0.3); }
    }
    
    /* SVG Icons Inheritance */
    .header-icon svg {
        display: block;
    }
    
    .tel-icon svg {
        display: block;
    }
    
    .status-item svg {
        display: inline-block;
        vertical-align: middle;
        flex-shrink: 0;
    }

    /* ===== RADAR SCAN KEYFRAMES ===== */
    @keyframes radar-scan {
        0% { transform: translateX(-100%); opacity: 0; }
        50% { opacity: 0.6; }
        100% { transform: translateX(200%); opacity: 0; }
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 4px var(--secondary), 0 0 8px rgba(0, 255, 65, 0.2); }
        50% { box-shadow: 0 0 8px var(--secondary), 0 0 20px rgba(0, 255, 65, 0.4), 0 0 30px rgba(0, 255, 65, 0.1); }
    }
    
    @keyframes data-flicker {
        0%, 100% { opacity: 1; }
        92% { opacity: 1; }
        93% { opacity: 0.7; }
        94% { opacity: 1; }
        97% { opacity: 0.8; }
        98% { opacity: 1; }
    }
    
    @keyframes typing-dots {
        0%, 20% { opacity: 0.2; }
        40% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    
    @keyframes border-glow-cycle {
        0%, 100% { border-color: rgba(0, 240, 255, 0.08); }
        50% { border-color: rgba(0, 240, 255, 0.2); }
    }

    /* ===== MISSION HEADER ===== */
    .mission-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, var(--bg-container-low) 0%, var(--bg-container) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid var(--ghost-border);
        border-bottom: 1px solid rgba(0, 240, 255, 0.1);
        padding: 14px 28px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
        border-radius: 2px;
    }
    
    .mission-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 60%;
        height: 1px;
        background: linear-gradient(90deg, var(--primary), transparent);
        opacity: 0.5;
    }
    
    .mission-header::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 60%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.03), transparent);
        animation: radar-scan 4s ease-in-out infinite;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: 3px;
        color: var(--primary) !important;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        margin: 0;
        line-height: 1;
    }
    
    .header-subtitle {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.65rem;
        color: var(--text-muted) !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .header-nav {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    
    .nav-link {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.7rem;
        color: var(--text-muted) !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        text-decoration: none;
        padding: 6px 12px;
        border: 1px solid transparent;
        transition: all 0.15s ease;
        border-radius: 2px;
    }
    
    .nav-link:hover {
        color: var(--primary) !important;
        border-color: rgba(0, 240, 255, 0.15);
        background: rgba(0, 240, 255, 0.05);
    }
    
    .nav-link.active {
        color: var(--primary) !important;
        border-color: rgba(0, 240, 255, 0.2);
        background: rgba(0, 240, 255, 0.08);
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .status-badge {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--secondary) !important;
        background: rgba(0, 255, 65, 0.06);
        padding: 5px 14px;
        border-radius: 2px;
        border: 1px solid rgba(0, 255, 65, 0.2);
        font-weight: 600;
        font-size: 0.65rem;
        letter-spacing: 2px;
        animation: pulse-glow 2.5s ease-in-out infinite;
        text-transform: uppercase;
    }
    
    .header-icons {
        display: flex;
        gap: 12px;
    }
    
    .header-icon {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--ghost-border);
        border-radius: 2px;
        color: var(--text-muted) !important;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.15s ease;
        background: rgba(255, 255, 255, 0.02);
    }
    
    .header-icon:hover {
        border-color: rgba(0, 240, 255, 0.3);
        color: var(--primary) !important;
        background: rgba(0, 240, 255, 0.05);
    }

    /* ===== TELEMETRY ROW ===== */
    .telemetry-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }
    
    .tel-card {
        background: linear-gradient(145deg, rgba(23, 27, 40, 0.8), rgba(27, 31, 44, 0.6));
        backdrop-filter: blur(16px);
        border: 1px solid var(--ghost-border);
        padding: 16px 20px;
        position: relative;
        overflow: hidden;
        border-radius: 2px;
        animation: border-glow-cycle 4s ease-in-out infinite;
        transition: all 0.15s ease;
    }
    
    .tel-card:hover {
        border-color: rgba(0, 240, 255, 0.25);
        background: linear-gradient(145deg, rgba(23, 27, 40, 0.95), rgba(27, 31, 44, 0.8));
    }
    
    .tel-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 2px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary), transparent);
        opacity: 0.3;
    }
    
    .tel-label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.6rem;
        color: var(--text-muted) !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    
    .tel-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .tel-value {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        line-height: 1;
        animation: data-flicker 8s infinite;
    }
    
    .tel-value.signal {
        color: var(--secondary) !important;
        text-shadow: 0 0 12px rgba(0, 255, 65, 0.4);
    }
    
    .tel-icon {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        border: 1.5px solid rgba(0, 240, 255, 0.25);
        color: var(--primary) !important;
        font-size: 1rem;
    }
    
    /* Battery Ring */
    .battery-ring {
        position: relative;
        width: 44px;
        height: 44px;
    }
    
    .battery-ring svg {
        transform: rotate(-90deg);
    }
    
    .battery-ring .ring-bg {
        fill: none;
        stroke: rgba(0, 240, 255, 0.1);
        stroke-width: 3;
    }
    
    .battery-ring .ring-fill {
        fill: none;
        stroke: var(--primary);
        stroke-width: 3;
        stroke-linecap: round;
        stroke-dasharray: 113;
        stroke-dashoffset: 18;
        filter: drop-shadow(0 0 4px rgba(0, 240, 255, 0.4));
        transition: stroke-dashoffset 1s ease;
    }
    
    .battery-pct {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.55rem;
        font-weight: 600;
        color: var(--primary) !important;
    }

    /* ===== SECTION PANELS ===== */
    .section-panel {
        background: linear-gradient(160deg, var(--bg-container-low) 0%, rgba(15, 19, 31, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid var(--ghost-border);
        position: relative;
        overflow: hidden;
        border-radius: 2px;
        min-height: 420px;
    }
    
    /* Corner Brackets - HUD accent */
    .section-panel::before,
    .section-panel::after {
        content: '';
        position: absolute;
        width: 16px;
        height: 16px;
        border-color: var(--primary);
        opacity: 0.4;
        z-index: 5;
    }
    
    .section-panel::before {
        top: 0;
        left: 0;
        border-top: 2px solid;
        border-left: 2px solid;
        border-color: inherit;
        border-color: var(--primary);
    }
    
    .section-panel::after {
        bottom: 0;
        right: 0;
        border-bottom: 2px solid;
        border-right: 2px solid;
        border-color: inherit;
        border-color: var(--primary);
    }
    
    .corner-tr, .corner-bl {
        position: absolute;
        width: 16px;
        height: 16px;
        opacity: 0.4;
        z-index: 5;
    }
    
    .corner-tr {
        top: 0;
        right: 0;
        border-top: 2px solid var(--primary);
        border-right: 2px solid var(--primary);
    }
    
    .corner-bl {
        bottom: 0;
        left: 0;
        border-bottom: 2px solid var(--primary);
        border-left: 2px solid var(--primary);
    }
    
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        border-bottom: 1px solid var(--ghost-border);
    }
    
    .section-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--primary) !important;
        letter-spacing: 2.5px;
        text-transform: uppercase;
    }
    
    .section-badge {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.55rem;
        color: var(--text-muted) !important;
        letter-spacing: 1px;
        padding: 3px 8px;
        border: 1px solid var(--ghost-border);
        border-radius: 2px;
        text-transform: uppercase;
    }
    
    .section-badge.encrypted {
        color: var(--secondary) !important;
        border-color: rgba(0, 255, 65, 0.2);
    }
    
    .section-body {
        padding: 16px 18px;
    }

    /* ===== LIVE OPTICS FEED ===== */
    .optics-feed {
        background: var(--bg-abyss);
        border: 1px solid var(--ghost-border);
        border-radius: 2px;
        min-height: 280px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .optics-feed::before {
        content: 'AWAITING FEED';
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.7rem;
        letter-spacing: 3px;
        color: var(--text-muted);
        opacity: 0.4;
    }
    
    .optics-hud-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
    }
    
    .optics-badge-row {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }
    
    .optics-info-badge {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.55rem;
        color: var(--text-muted) !important;
        letter-spacing: 1px;
        padding: 3px 8px;
        background: rgba(10, 14, 26, 0.6);
        border: 1px solid var(--ghost-border);
        border-radius: 2px;
    }
    
    .toggle-vision {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 12px;
        padding: 8px 14px;
        background: rgba(0, 240, 255, 0.05);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 2px;
        cursor: pointer;
        transition: all 0.15s ease;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.65rem;
        color: var(--primary) !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    
    .toggle-vision:hover {
        border-color: rgba(0, 240, 255, 0.35);
        background: rgba(0, 240, 255, 0.1);
    }

    /* ===== MISSION AI CHAT ===== */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 340px;
        overflow-y: auto;
        padding-right: 4px;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 3px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: rgba(0, 240, 255, 0.15);
        border-radius: 2px;
    }
    
    .chat-message {
        margin-bottom: 12px;
    }
    
    .chat-role {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.5rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    
    .chat-role.ai {
        color: var(--primary) !important;
    }
    
    .chat-role.user {
        color: var(--text-muted) !important;
    }
    
    .chat-bubble {
        padding: 10px 14px;
        font-size: 0.78rem;
        line-height: 1.5;
        border-radius: 2px;
        color: var(--text-primary) !important;
    }
    
    .chat-bubble.ai {
        background: rgba(0, 240, 255, 0.05);
        border: 1px solid rgba(0, 240, 255, 0.12);
        border-left: 2px solid var(--primary);
    }
    
    .chat-bubble.human {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--ghost-border);
        border-left: 2px solid var(--text-muted);
    }
    
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 8px 14px;
    }
    
    .typing-dot {
        width: 5px;
        height: 5px;
        background: var(--primary);
        border-radius: 50%;
        animation: typing-dots 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    /* ===== STATUS BAR ===== */
    .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--bg-container-low);
        border: 1px solid var(--ghost-border);
        border-top: 1px solid rgba(0, 240, 255, 0.06);
        padding: 8px 24px;
        margin-top: 16px;
        border-radius: 2px;
    }
    
    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.6rem;
        color: var(--text-muted) !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--secondary);
        box-shadow: 0 0 6px rgba(0, 255, 65, 0.4);
    }
    
    .status-value {
        color: var(--text-primary) !important;
        font-weight: 600;
    }

    /* ===== STREAMLIT COMPONENT OVERRIDES ===== */
    
    /* Metric values */
    [data-testid="stMetricValue"] { 
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--primary) !important; 
        text-shadow: 0 0 12px rgba(0, 240, 255, 0.3); 
        font-size: 1.6rem !important; 
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        font-size: 0.6rem !important;
        color: var(--text-muted) !important;
    }
    
    /* Remove padding from inner containers to let our custom layout breathe */
    div[data-testid="stVerticalBlock"] > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        backdrop-filter: none !important;
        border-radius: 0 !important;
    }
    
    /* Inputs */
    div[data-testid="stTextInput"] input {
        background: var(--bg-container-high) !important;
        border: none !important;
        border-bottom: 2px solid var(--text-muted) !important;
        border-radius: 0 !important;
        padding: 10px 14px !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 0.85rem !important;
        color: var(--text-primary) !important;
        transition: border-color 0.15s ease !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-bottom-color: var(--primary) !important;
        box-shadow: 0 2px 8px rgba(0, 240, 255, 0.15) !important;
    }
    
    div[data-testid="stTextInput"] label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.6rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
    }
    
    /* Toggle */
    div[data-testid="stToggle"] label span {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 1px !important;
        font-size: 0.75rem !important;
        color: var(--primary) !important;
    }
    
    /* Map */
    div[data-testid="stDeckGlJsonChart"] {
        border: 1px solid var(--ghost-border) !important;
        border-radius: 2px !important;
        overflow: hidden !important;
    }

    /* Chat input */
    div[data-testid="stChatInput"] {
        border: none !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        background: var(--bg-container-high) !important;
        border: 1px solid var(--ghost-border) !important;
        border-radius: 2px !important;
        font-family: 'Manrope', sans-serif !important;
        color: var(--text-primary) !important;
        font-size: 0.8rem !important;
    }
    
    div[data-testid="stChatInput"] textarea:focus {
        border-color: rgba(0, 240, 255, 0.3) !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.08) !important;
    }
    
    div[data-testid="stChatInput"] button {
        background: rgba(0, 240, 255, 0.1) !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 2px !important;
        color: var(--primary) !important;
    }
    
    /* Chat container height */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--ghost-border) !important;
        border-radius: 2px !important;
        background: rgba(15, 19, 31, 0.5) !important;
    }
    
    /* Markdown headers inside columns */
    .stMarkdown h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--primary) !important;
        font-size: 0.75rem !important;
        letter-spacing: 2.5px !important;
        text-transform: uppercase !important;
        font-weight: 600 !important;
        margin-bottom: 12px !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid var(--ghost-border) !important;
    }
    
    /* Columns layout */
    div[data-testid="stHorizontalBlock"] {
        gap: 12px !important;
    }
    
    /* Warning/Info messages */
    div[data-testid="stAlert"] {
        background: rgba(0, 240, 255, 0.05) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 2px !important;
        color: var(--text-primary) !important;
    }
    
    /* Expander */
    div[data-testid="stExpander"] {
        background: var(--bg-container-low) !important;
        border: 1px solid var(--ghost-border) !important;
        border-radius: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. MISSION HEADER ---
st.markdown("""
<div class="mission-header">
    <div class="header-left">
        <div>
            <div class="header-title">RESQ // MISSION CONTROL</div>
            <div class="header-subtitle">AERIAL SURVEILLANCE UNIT &bull; ALPHA-1 &bull; <span style="color: #00FF41 !important;"><span class="live-dot"></span> SYSTEM ONLINE</span></div>
        </div>
    </div>
    <div class="header-right">
        <div class="header-nav">
            <span class="nav-link active">DASHBOARD</span>
            <span class="nav-link">FLEET</span>
            <span class="nav-link">INTEL</span>
        </div>
        <div class="header-icons">
            <div class="header-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div>
            <div class="header-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>
        </div>
        <div class="status-badge"><span class="live-dot"></span> SYSTEM ONLINE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. TELEMETRY ROW ---
@st.fragment(run_every=2.0)
def update_telemetry():
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

    tel = st.session_state.telemetry
    bat_pct = tel['bat']
    # SVG ring: circumference = 2*pi*18 ≈ 113.1, offset = 113.1 * (1 - pct/100)
    bat_offset = 113.1 * (1 - bat_pct / 100)
    
    st.markdown(f"""
    <div class="telemetry-grid">
        <div class="tel-card">
            <div class="tel-label">BATTERY LIFE</div>
            <div class="tel-content">
                <div class="tel-value">{bat_pct}%</div>
                <div class="battery-ring">
                    <svg width="44" height="44" viewBox="0 0 44 44">
                        <circle class="ring-bg" cx="22" cy="22" r="18"/>
                        <circle class="ring-fill" cx="22" cy="22" r="18" style="stroke-dashoffset: {bat_offset};"/>
                    </svg>
                    <div class="battery-pct"><svg width="12" height="12" viewBox="0 0 24 24" fill="var(--primary)" stroke="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
                </div>
            </div>
        </div>
        <div class="tel-card">
            <div class="tel-label">LATITUDE</div>
            <div class="tel-content">
                <div class="tel-value">{tel['lat']:.4f}</div>
                <div class="tel-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
            </div>
        </div>
        <div class="tel-card">
            <div class="tel-label">LONGITUDE</div>
            <div class="tel-content">
                <div class="tel-value">{tel['lon']:.4f}</div>
                <div class="tel-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" opacity="0.3"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg></div>
            </div>
        </div>
        <div class="tel-card">
            <div class="tel-label">SIGNAL STATUS</div>
            <div class="tel-content">
                <div class="tel-value signal">STRONG</div>
                <div class="tel-icon" style="border-color: rgba(0, 255, 65, 0.25); color: #00FF41 !important;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="6" y1="18" x2="6" y2="15"/><line x1="10" y1="18" x2="10" y2="12"/><line x1="14" y1="18" x2="14" y2="9"/><line x1="18" y1="18" x2="18" y2="6"/></svg></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

update_telemetry()

# --- 5. MAIN INTERFACE GRID ---
col_video, col_map, col_chat = st.columns([1.5, 2, 1])

with col_video:
    st.markdown('<h3><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:8px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>LIVE OPTICS // FEED_01</h3>', unsafe_allow_html=True)
    
    v_c1, v_c2 = st.columns(2)
    user_id = v_c1.text_input("Username", value="admin")
    user_pw = v_c2.text_input("Password", type="password")
    ip_raw = st.text_input("Phone IP", value="10.221.13.120:8081")
    
    is_streaming = st.toggle("Activate Vision Feed", value=False)
    vision_placeholder = st.empty()

with col_map:
    st.markdown('<h3><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:8px;"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>TACTICAL MAP // SECTOR_G7</h3>', unsafe_allow_html=True)
    tel = st.session_state.get("telemetry", {"lat": 21.2863, "lon": 74.8028})
    map_df = pd.DataFrame({'lat': [tel['lat']], 'lon': [tel['lon']]})
    st.map(map_df, zoom=16, color="#FF2D55", use_container_width=True)

with col_chat:
    st.markdown('<h3><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:8px;"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>MISSION AI // ORBITAL</h3>', unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=280)
    with chat_box:
        for m in st.session_state.messages:
            role_class = "ai" if m['role'] == 'assistant' else "user"
            role_label = "AI_ORBITAL" if m['role'] == 'assistant' else "COMMANDER"
            bubble_class = "ai" if m['role'] == 'assistant' else "human"
            st.markdown(f"""
            <div class="chat-message">
                <div class="chat-role {role_class}">{role_label}</div>
                <div class="chat-bubble {bubble_class}">{m['content']}</div>
            </div>
            """, unsafe_allow_html=True)
            
    if prompt := st.chat_input("Command AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        tel_data = st.session_state.telemetry
        ctx = f"You are ResQ-AI Orbital, a tactical mission AI assisting flood rescue drone operations. Battery: {tel_data['bat']}%. Current coords: {tel_data['lat']}, {tel_data['lon']}. Respond concisely and tactically. User command: {prompt}"
        try:
            r = model_ai.generate_content(ctx)
            st.session_state.messages.append({"role": "assistant", "content": r.text})
            st.rerun() 
        except Exception as e:
            st.error(f"AI Error: {e}")

# --- 6. STATUS BAR ---
st.markdown("""
<div class="status-bar">
    <div class="status-item">
        <div class="status-dot"></div>
        <span>ELAPSED:</span>
        <span class="status-value">00:14:32</span>
    </div>
    <div class="status-item">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span>DETECTIONS:</span>
        <span class="status-value">19</span>
    </div>
    <div class="status-item">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
        <span>ALTITUDE:</span>
        <span class="status-value">120M</span>
    </div>
    <div class="status-item">
        <span class="live-dot green"></span>
        <span>SIGNAL:</span>
        <span class="status-value" style="color: #00FF41 !important;">NOMINAL</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 7. VISION LOOP (Persistent & Non-Blocking) ---
if CV2_AVAILABLE and is_streaming and ip_raw:
    clean_ip = ip_raw.replace("http://", "").replace("https://", "").strip()
    stream_url = f"http://{user_id}:{user_pw}@{clean_ip}/video"
    
    if 'cap' not in st.session_state or not st.session_state.cap.isOpened():
        st.session_state.cap = cv2.VideoCapture(stream_url)
        st.session_state.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        
    cap = st.session_state.cap

    if not cap.isOpened():
        st.error("Connection Failed. Check IP/Hotspot.")
    else:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.warning("Signal Lost. Reconnecting...")
                st.session_state.cap.release()
                del st.session_state.cap
                break
                
            if model_yolo is not None:
                results = model_yolo.predict(frame, conf=0.3, verbose=False)
                annotated_frame = results[0].plot()
            else:
                annotated_frame = frame
            
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            vision_placeholder.image(frame_rgb, channels="RGB", width="stretch")
            time.sleep(0.01)
elif not CV2_AVAILABLE and is_streaming:
    vision_placeholder.info("Camera streaming is only available in local deployment. \n\nFor cloud demo, the tactical map and Mission AI are fully functional!")
else:
    if 'cap' in st.session_state:
        st.session_state.cap.release()
        del st.session_state.cap