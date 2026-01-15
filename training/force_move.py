import kagglehub
import os
import shutil
import yaml

# --- CONFIG ---
DATASET_SLUG = "rgbnihal/c2a-dataset"
TARGET_FOLDER = os.path.abspath("datasets")

def force_move_data():
    print("🔍 Locating downloaded data in cache...")
    
    # 1. Get the path (This is instant because it's already downloaded)
    cache_path = kagglehub.dataset_download(DATASET_SLUG)
    print(f"✅ Found data at: {cache_path}")

    # 2. Clean the target folder to ensure a fresh start
    if os.path.exists(TARGET_FOLDER):
        print("🧹 Cleaning old empty folder...")
        shutil.rmtree(TARGET_FOLDER)
    
    # 3. Copy EVERYTHING (The "Force" Move)
    print(f"📦 Copying files to: {TARGET_FOLDER}...")
    shutil.copytree(cache_path, TARGET_FOLDER)
    print("✅ Copy complete.")

    # 4. Create the Map (data.yaml)
    print("🗺️  Creating YOLO Map...")
    yaml_data = {
        'path': TARGET_FOLDER,
        'train': 'images/train',  # Standard YOLO format
        'val': 'images/val',
        'names': {0: 'Person', 1: 'Car', 2: 'Flood', 3: 'Rubble', 4: 'Fire'}
    }
    
    yaml_path = os.path.join(TARGET_FOLDER, "custom_flood.yaml")
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f)

    print("🎉 FIXED! You are ready to train.")
    
    # 5. Verify
    count = 0
    for root, _, files in os.walk(TARGET_FOLDER):
        for f in files:
            if f.endswith(('.jpg', '.png')):
                count += 1
    print(f"📊 Verified Image Count: {count}")

if __name__ == "__main__":
    force_move_data()