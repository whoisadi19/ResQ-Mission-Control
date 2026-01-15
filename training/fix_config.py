import os
import yaml

# We are looking inside the 'datasets' folder
BASE_DIR = os.path.abspath("datasets")
YAML_PATH = os.path.join(BASE_DIR, "custom_flood.yaml")

def find_image_folder(search_terms):
    """Hunts for a folder that contains images AND matches the search term (train/val)"""
    for root, dirs, files in os.walk(BASE_DIR):
        # 1. Check if this folder actually has images
        has_images = any(f.lower().endswith(('.jpg', '.png', '.jpeg')) for f in files)
        
        if has_images:
            # 2. Check if the folder name matches our search term
            folder_name = os.path.basename(root).lower()
            if any(term in folder_name for term in search_terms):
                return root
    return None

def run_fix():
    print(f"🕵️  Scanning {BASE_DIR} for image folders...")

    # 1. Find the REAL Training folder
    real_train_path = find_image_folder(['train'])
    
    # 2. Find the REAL Validation folder (look for 'val', 'valid', or 'test')
    real_val_path = find_image_folder(['val', 'valid', 'test'])

    # Fallback: If we can't find a validation folder, just use the training one
    # (Not perfect for science, but fine for getting the code to run!)
    if not real_val_path and real_train_path:
        print("⚠️  Warning: No separate 'val' folder found. Using 'train' folder for both.")
        real_val_path = real_train_path

    if real_train_path and real_val_path:
        print(f"✅ Found Training Images:   {real_train_path}")
        print(f"✅ Found Validation Images: {real_val_path}")

        # 3. Update the YAML file
        with open(YAML_PATH, 'r') as f:
            data = yaml.safe_load(f)

        # UPDATE: We use absolute paths to prevent any confusion
        data['path'] = BASE_DIR
        data['train'] = real_train_path
        data['val'] = real_val_path

        with open(YAML_PATH, 'w') as f:
            yaml.dump(data, f)
            
        print("\n🎉 SUCCESS! The map (custom_flood.yaml) has been fixed.")
        print("👉 You can now run 'python train.py' again.")
    else:
        print("\n❌ CRITICAL ERROR: Could not find ANY images in 'datasets'.")
        print("   Did the download finish? Check if the folder is empty.")

if __name__ == "__main__":
    run_fix()