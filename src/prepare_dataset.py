import google.generativeai as genai
import os
import json
from PIL import Image
from tqdm import tqdm
import time
import shutil
from sklearn.model_selection import train_test_split
import numpy as np

# --- Configuration ---
KEY_FILE_PATH = "src/api_key.txt"
RAW_DATA_DIR = "book_covers_mixed"
FINAL_DATASET_DIR = "dataset"
TRAIN_TEST_SPLIT_RATIO = 0.2 # 20% for testing

# --- 1. Configure Gemini API ---
try:
    with open(KEY_FILE_PATH, "r") as f:
        API_KEY = f.read().strip()
    genai.configure(api_key=API_KEY)
except FileNotFoundError:
    print(f"ERROR: API key file not found at '{KEY_FILE_PATH}'")
    exit()
except Exception as e:
    print(f"An error occurred while configuring the API key: {e}")
    exit()

# --- 2. Annotation Function (Gemini) ---
def auto_annotate_with_gemini(image_dir):
    """Checks for missing annotations and generates them using the Gemini API."""
    print("--- Phase 1: Checking for and generating missing annotations ---")
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith('.jpg')]
    
    tasks_to_do = []
    for filename in image_files:
        json_path = os.path.join(image_dir, os.path.splitext(filename)[0] + '.json')
        if not os.path.exists(json_path):
            tasks_to_do.append(filename)
    
    if not tasks_to_do:
        print("All images are already annotated. Skipping generation.")
        return

    print(f"Found {len(tasks_to_do)} images that need annotation.")
    for filename in tqdm(tasks_to_do, desc="Annotating with Gemini"):
        image_path = os.path.join(image_dir, filename)
        json_path = os.path.join(image_dir, os.path.splitext(filename)[0] + '.json')
        try:
            img = Image.open(image_path)
            prompt = """Analyze this image. Identify every distinct text region. Your response MUST be a single, valid JSON object and nothing else. The JSON should have one key: "shapes". The value of "shapes" is a list of objects, each with a "label" ('text') and a "points" list of [x, y] polygon coordinates. Example: {"shapes": [{"label": "text", "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]}]}"""
            response = model.generate_content([prompt, img])
            cleaned_response = response.text.strip().replace("json", "").replace("", "")
            data = json.loads(cleaned_response)
            
            labelme_output = {
                "version": "5.0.1", "flags": {},
                "shapes": data.get("shapes", []),
                "imagePath": filename, "imageData": None,
                "imageHeight": img.height, "imageWidth": img.width,
            }
            for shape in labelme_output["shapes"]:
                shape["group_id"], shape["shape_type"], shape["flags"] = None, "polygon", {}
            with open(json_path, 'w') as f:
                json.dump(labelme_output, f, indent=2)
            time.sleep(1.5)
        except Exception as e:
            print(f"\nCould not process {filename}. Error: {e}")
            time.sleep(5)
    print("Annotation phase complete.")

# --- 3. Conversion and Splitting Function ---
def prepare_dataset_for_training():
    """Converts annotations, splits data, and creates the final training-ready folder."""
    print("\n--- Phase 2: Preparing dataset for training ---")

    if os.path.exists(FINAL_DATASET_DIR):
        shutil.rmtree(FINAL_DATASET_DIR)
        print(f"Removed existing dataset directory: '{FINAL_DATASET_DIR}'")

    all_image_files = [f for f in os.listdir(RAW_DATA_DIR) if f.lower().endswith('.jpg')]
    
    # Split data into training and testing sets
    train_files, test_files = train_test_split(all_image_files, test_size=TRAIN_TEST_SPLIT_RATIO, random_state=42)
    print(f"Splitting data: {len(train_files)} for training, {len(test_files)} for testing.")

    # Create the required directory structure
    os.makedirs(os.path.join(FINAL_DATASET_DIR, 'train', 'images'), exist_ok=True)
    os.makedirs(os.path.join(FINAL_DATASET_DIR, 'train', 'labels'), exist_ok=True)
    os.makedirs(os.path.join(FINAL_DATASET_DIR, 'test', 'images'), exist_ok=True)
    os.makedirs(os.path.join(FINAL_DATASET_DIR, 'test', 'labels'), exist_ok=True)

    # Process and move files
    for split_name, file_list in [('train', train_files), ('test', test_files)]:
        print(f"Processing '{split_name}' set...")
        for filename in tqdm(file_list, desc=f"Creating {split_name} data"):
            basename = os.path.splitext(filename)[0]
            json_path = os.path.join(RAW_DATA_DIR, basename + '.json')
            image_path = os.path.join(RAW_DATA_DIR, filename)

            # Copy image to its new location
            shutil.copy(image_path, os.path.join(FINAL_DATASET_DIR, split_name, 'images', filename))

            # Convert JSON to YOLO format and save
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            yolo_annotations = []
            img_w, img_h = data['imageWidth'], data['imageHeight']
            
            for shape in data['shapes']:
                points = np.array(shape['points'])
                x_min, y_min = np.min(points, axis=0)
                x_max, y_max = np.max(points, axis=0)
                
                # Convert to YOLO format (class_id, x_center, y_center, width, height)
                x_center = ((x_min + x_max) / 2) / img_w
                y_center = ((y_min + y_max) / 2) / img_h
                width = (x_max - x_min) / img_w
                height = (y_max - y_min) / img_h
                
                # We only have one class, "text", so its index is 0
                yolo_annotations.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
            with open(os.path.join(FINAL_DATASET_DIR, split_name, 'labels', basename + '.txt'), 'w') as f:
                f.write('\n'.join(yolo_annotations))

    # --- 4. Create dataset.yaml file ---
    yaml_content = f"""
path: ../{FINAL_DATASET_DIR}  # dataset root dir
train: train/images
val: test/images
test: test/images

# Classes
names:
  0: text
"""
    with open(os.path.join(FINAL_DATASET_DIR, 'dataset.yaml'), 'w') as f:
        f.write(yaml_content)
    print("Created dataset.yaml configuration file.")
    print("\n✅ Dataset is now ready for training!")

if __name__ == '__main__':
    auto_annotate_with_gemini(RAW_DATA_DIR)
    prepare_dataset_for_training()
