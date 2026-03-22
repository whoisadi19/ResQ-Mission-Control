import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

try:
    import cv2
    print("✓ OpenCV imported successfully")
    print("  OpenCV version:", cv2.__version__)
except Exception as e:
    print("✗ OpenCV import failed:", e)

try:
    from ultralytics import YOLO
    print("✓ Ultralytics imported successfully")
except Exception as e:
    print("✗ Ultralytics import failed:", e)

# Check for video file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
video_file = None
for f in os.listdir(BASE_DIR):
    if f.startswith("flood_footage") and f.lower().endswith(('.mp4', '.mov', '.avi')):
        video_file = os.path.join(BASE_DIR, f)
        print(f"✓ Found video file: {f}")
        break

if not video_file:
    print("✗ No video file found")
else:
    # Check if video can be opened
    cap = cv2.VideoCapture(video_file)
    if cap.isOpened():
        print("✓ Video file can be opened")
        ret, frame = cap.read()
        if ret:
            print(f"✓ Video frame read successfully: {frame.shape}")
        else:
            print("✗ Could not read video frame")
        cap.release()
    else:
        print("✗ Could not open video file")

# Check model file
MODEL_PATH = os.path.join(BASE_DIR, "FINAL_RESCUE_MODEL.pt")
if os.path.exists(MODEL_PATH):
    print(f"✓ Model file exists: {MODEL_PATH}")
    try:
        model = YOLO(MODEL_PATH)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
else:
    print("✗ Model file not found")
