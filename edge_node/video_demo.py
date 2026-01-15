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
    
    # Speed variables
    current_delay = 30  
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
        # Using predict() as it is more aggressive for small object detection
        results = model.predict(frame, conf=0.15, imgsz=1280, verbose=False)
        
        # 4. ANNOTATE
        annotated_frame = results[0].plot()

        # 5. TACTICAL OVERLAY (Speed & Controls Only)
        cv2.putText(annotated_frame, f"MODE: {mode_text}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "S: Slow | N: Normal | F: Fast", (50, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 6. SHOW AND CAPTURE KEYS
        cv2.imshow("ResQ-AI Tactical Control", annotated_frame)
        
        key = cv2.waitKey(current_delay) & 0xFF
        
        if key == ord('s'):
            current_delay = 150
            mode_text = "SLOW MOTION"
        elif key == ord('n'):
            current_delay = 30
            mode_text = "NORMAL"
        elif key == ord('f'):
            current_delay = 1
            mode_text = "FAST MOTION"
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Demo session closed.")

if __name__ == "__main__":
    run_controlled_demo()