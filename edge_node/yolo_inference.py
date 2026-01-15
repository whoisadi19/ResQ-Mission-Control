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