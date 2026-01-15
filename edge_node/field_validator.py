from ultralytics import YOLO
import os
import random
import cv2

# --- CONFIG ---
MODEL_PATH = "FINAL_RESCUE_MODEL.pt"


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