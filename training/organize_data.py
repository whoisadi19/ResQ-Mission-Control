import os
import shutil
import random
import yaml
import glob

# CONFIG
BASE_DIR = os.path.abspath("datasets")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
LABELS_DIR = os.path.join(BASE_DIR, "labels")

def organize_dataset():
    print(f"🧹 Starting Cleanup in: {BASE_DIR}")
    
    # 1. Find ALL images recursively (ignoring where they are currently)
    # We look for jpg, png, and jpeg
    all_images = []
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                full_path = os.path.join(root, file)
                all_images.append(full_path)
    
    total_images = len(all_images)
    print(f"🔍 Found {total_images} total images.")
    
    if total_images == 0:
        print("❌ CRITICAL: No images found! The download must have failed.")
        print("   Please run force_move.py again or check your internet.")
        return

    # 2. Shuffle and Split (80% Train, 20% Val)
    random.shuffle(all_images)
    split_idx = int(total_images * 0.8)
    train_imgs = all_images[:split_idx]
    val_imgs = all_images[split_idx:]
    
    print(f"📊 Splitting: {len(train_imgs)} Training | {len(val_imgs)} Validation")

    # 3. Create Standard YOLO Structure
    # Structure:
    # datasets/images/train
    # datasets/images/val
    # datasets/labels/train
    # datasets/labels/val
    
    for split in ['train', 'val']:
        os.makedirs(os.path.join(IMAGES_DIR, split), exist_ok=True)
        os.makedirs(os.path.join(LABELS_DIR, split), exist_ok=True)

    # 4. Move Files (Safely)
    print("🚚 Moving files to their new homes...")
    
    def move_file_and_label(img_path, split):
        # Move Image
        filename = os.path.basename(img_path)
        dest_img_path = os.path.join(IMAGES_DIR, split, filename)
        
        # Don't move if it's already there (prevents errors on re-runs)
        if img_path != dest_img_path:
            shutil.move(img_path, dest_img_path)
        
        # Move Label (if it exists)
        # We assume label has same name but .txt extension
        label_path = os.path.splitext(img_path)[0] + ".txt"
        if os.path.exists(label_path):
            dest_label_path = os.path.join(LABELS_DIR, split, os.path.basename(label_path))
            if label_path != dest_label_path:
                shutil.move(label_path, dest_label_path)

    # Move Train
    for img in train_imgs:
        move_file_and_label(img, 'train')
        
    # Move Val
    for img in val_imgs:
        move_file_and_label(img, 'val')

    # 5. Rewrite the YAML Map
    print("🗺️  Updating YOLO Map (custom_flood.yaml)...")
    yaml_data = {
        'path': BASE_DIR,
        'train': 'images/train',
        'val': 'images/val',
        'names': {0: 'Person', 1: 'Car', 2: 'Flood', 3: 'Rubble', 4: 'Fire'}
    }
    
    yaml_path = os.path.join(BASE_DIR, "custom_flood.yaml")
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f)
        
    print("✅ ORGANIZATION COMPLETE! Your folder is now perfect.")
    print("👉 Now run: python train.py")

if __name__ == "__main__":
    organize_dataset()