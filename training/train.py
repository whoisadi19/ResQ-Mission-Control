from ultralytics import YOLO
import torch
import os

def train_brain():
    # 1. Check for GPU ( RTX 4050)
    if torch.cuda.is_available():
        torch.cuda.set_device(0)
        device = 0
        name = torch.cuda.get_device_name(0)
        print(f"🔥 POWERED BY: {name}")
    else:
        print("⚠️ WARNING: Running on CPU (Will be slow!)")
        device = 'cpu'

    # 2. Load the Student (Small Model)
    # We use 'yolov8s.pt' because it learns fast.
    model = YOLO("yolov8s.pt") 

    # 3. Start Learning
    print("🧠 Beginning Training Session...")
    
    # Verify the yaml file exists first
    yaml_path = os.path.abspath("datasets/custom_flood.yaml")
    if not os.path.exists(yaml_path):
        print(f"❌ Error: Could not find {yaml_path}")
        return

    model.train(
        data=yaml_path,          # The map we created in the last step
        epochs=30,               # 10 rounds of study (approx 45-60 mins)
        imgsz=640,               # Standard size
        batch=16,                # Small batch size for 6GB VRAM
        device=device,
        workers=1,
        project="flood_brain",   # Save folder
        name="v1_flood_model"    # Name of this specific run
    )
    
    print("✅ TRAINING FINISHED!")
    print("Find your new brain at: training/flood_brain/v1_flood_model/weights/best.pt")

if __name__ == "__main__":
    train_brain()