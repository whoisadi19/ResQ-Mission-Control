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
       
        supabase.table("telemetry").insert(data).execute()
        print(f"📡 Data Sent: Bat={batt}% | Lat={lat:.4f}")
    except Exception as e:
        print(f"❌ Data Send Error: {e}")

# --- TEST MODE ---

if __name__ == "__main__":
    print("Simulation Started: Sending data to cloud...")
    
    # Starting coordinates (Mumbai)
    lat, lon = 21.2863, 74.8028
    
    while True:
        # 1. Simulate movement
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)
        batt = random.randint(80, 100)
        
        # 2. Send data
        send_telemetry(lat, lon, batt, "Patrolling Sector 7")
        
        # 3. Wait 2 seconds
        time.sleep(2)