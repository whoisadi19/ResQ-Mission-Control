import os
import yt_dlp
import subprocess
import shutil

# --- MISSION LIBRARY (Updated with Verified Links) ---
MISSIONS = {
    # BBC News: Helicopter/Drone rescue in Kerala (Very clear people on rooftops)
    "Mission_Kerala": ["https://www.youtube.com/watch?v=mnZPyiqNLV8", "00:00:10", "00:00:40"],
    
    # Confirmed working from your screenshot (Chennai Flood)
    "Mission_Chennai": ["https://www.youtube.com/watch?v=fuOKYmaXhDQ", "00:00:10", "00:00:40"],
    
    # Hurricane Harvey Drone Footage (Good for "Survey" mode)
    "Mission_Texas":   ["https://www.youtube.com/watch?v=PxGodhPKz1U", "00:00:30", "00:01:00"] 
}

OUTPUT_DIR = "data/raw_videos"

# --- SETUP ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_ffmpeg_installed():
    """Checks if ffmpeg is available in the system path."""
    return shutil.which("ffmpeg") is not None

def download_and_process(name, url, start, end, has_ffmpeg):
    print(f"\n🚁 Processing Mission: {name}...")
    
    full_path = os.path.join(OUTPUT_DIR, "temp_full.mp4")
    final_path = os.path.join(OUTPUT_DIR, f"{name}.mp4")

    # If the file already exists (e.g. Chennai), skip it to save time
    if os.path.exists(final_path):
        print(f"   ✅ File already exists: {final_path}")
        return

    # 1. DOWNLOAD
    if has_ffmpeg:
        format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        print("   ⚠️ FFmpeg missing. Using Safe Mode.")
        format_str = 'best[ext=mp4]/best'

    ydl_opts = {
        'format': format_str,
        'outtmpl': full_path,
        'quiet': True,
        'overwrites': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("   ✅ Download complete.")
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return

    # 2. TRIM
    if has_ffmpeg:
        print(f"   ✂️  Trimming ({start} to {end})...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", full_path,
            "-ss", start,
            "-to", end,
            "-c", "copy",
            final_path
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"   ✅ Clip ready: {final_path}")
            if os.path.exists(full_path): os.remove(full_path)
        except Exception as e:
            print(f"   ❌ Trim failed: {e}")
    else:
        if os.path.exists(final_path): os.remove(final_path)
        os.rename(full_path, final_path)
        print(f"   ✅ Full video saved (Untrimmed): {final_path}")

def main():
    has_ffmpeg = is_ffmpeg_installed()
    print(f"🛠️  System Check: FFmpeg is {'✅ Installed' if has_ffmpeg else '❌ Missing'}")

    for name, details in MISSIONS.items():
        url, start, end = details
        download_and_process(name, url, start, end, has_ffmpeg)
    
    print("\n🎉 All Missions Loaded into Library.")

if __name__ == "__main__":
    main()