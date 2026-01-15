import torch
import cv2
import ultralytics
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"OpenCV Version: {cv2.__version__}")
print(f"YOLO Ready: {ultralytics.__version__}")