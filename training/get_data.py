import kagglehub
import os
import shutil
import yaml

# --- PASTE YOUR COPIED TOKEN BELOW ---
# It should look like "KGAT_fdd00284..."
MY_KAGGLE_TOKEN = "KGAT_fdd00284c48f92abd7f1c5a7f23efe25" 

# CONFIG
DATASET_SLUG = "rgbnihal/c2a-dataset"
TARGET_FOLDER = "datasets"

def setup_environment():
    print(f"🚀 Authenticating with Kaggle Token...")
    
    # 1. Set the token manually (So we don't need a file)
    os.environ["KGAT_fdd00284c48f92abd7f1c5a7f23efe25"] = MY_KAGGLE_TOKEN
    
    try:
        # 2. Download (kagglehub saves to a hidden cache folder first)
        print(f"⬇️  Downloading {DATASET_SLUG}...")
        path = kagglehub.dataset_download(DATASET_SLUG)
        print(f"✅ Downloaded to cache: {path}")

        # 3. Move files to our project folder
        if not os.path.exists(TARGET_FOLDER):
            os.makedirs(TARGET_FOLDER)
            
        # Copy the contents from cache to 'training/datasets'
        print(f"📦 Moving files to {TARGET_FOLDER}...")
        for file_name in os.listdir(path):
            full_file_name = os.path.join(path, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, TARGET_FOLDER)
            elif os.path.isdir(full_file_name):
                # Copy folders (like 'images' or 'labels')
                dest_dir = os.path.join(TARGET_FOLDER, file_name)
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir)
                shutil.copytree(full_file_name, dest_dir)
        
        # 4. Create the Map (data.yaml) for YOLO
        # This tells YOLO where the images are.
        yaml_data = {
            'path': os.path.abspath(TARGET_FOLDER),  
            'train': 'images/train',                 
            'val': 'images/val',                     
            'names': {                               
                0: 'Person',
                1: 'Car',
                2: 'Flood',
                3: 'Rubble',
                4: 'Fire'
            }
        }
        
        yaml_path = os.path.join(TARGET_FOLDER, "custom_flood.yaml")
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_data, f)
        
        print(f"✅ Configuration saved to: {yaml_path}")
        print("READY TO TRAIN! 🥊")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_environment()