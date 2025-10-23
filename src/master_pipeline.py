import google.generativeai as genai
import os
import json
from PIL import Image
from tqdm import tqdm
import time
import shutil
from sklearn.model_selection import train_test_split
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from collections import defaultdict
import io

# --- Configuration ---
KEY_FILE_PATH = "src/api_key.txt"
FINAL_DATASET_DIR = "dataset"
TRAIN_TEST_SPLIT_RATIO = 0.2
IMAGES_PER_QUERY = 20

# --- Better Search Queries ---
QUERIES = {
    "hindi": "hindi classic literature novels",
    "kannada": "kannada literature books",
    "bengali": "bengali classic novels",
    "tamil": "tamil classic literature books",
    "marathi": "marathi classic novels",
    "english": "classic fiction book covers"
}

# --- 1. Configure Gemini API ---
try:
    with open(KEY_FILE_PATH, "r") as f:
        API_KEY = f.read().strip()
    genai.configure(api_key=API_KEY)
    # Use the standard, stable vision model
    GEMINI_MODEL = genai.GenerativeModel('gemini-pro-vision')
except Exception as e:
    print(f"ERROR: Could not configure Gemini API. Check 'src/api_key.txt'. Details: {e}")
    exit()

def is_image_valid(image_bytes):
    """Uses Pillow to verify if the downloaded data is a valid image."""
    try:
        img = Image.open(image_bytes)
        img.verify()
        return True
    except Exception:
        return False

def run_pipeline():
    """The main function to scrape, verify, annotate, and prepare the dataset."""
    print("🚀 Starting the Master Data Preparation Pipeline...")
    
    RAW_DIR = "temp_raw_data"
    if os.path.exists(RAW_DIR): shutil.rmtree(RAW_DIR)
    os.makedirs(RAW_DIR)
    
    counters = defaultdict(int)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    print("\n--- Phase 1: Scraping, Verifying, and Annotating ---")
    for lang_key, query in QUERIES.items():
        print(f"\nProcessing query: '{query}'")
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.goodreads.com/search?q={encoded_query}"
        
        try:
            res = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')
            book_links = ["https://www.goodreads.com" + a['href'] for a in soup.find_all('a', class_='bookTitle', href=True)]
        except Exception as e:
            print(f"  Could not fetch search results. Skipping. Error: {e}")
            continue

        for book_url in tqdm(book_links, desc=f"  -> {lang_key}"):
            if counters[lang_key] >= IMAGES_PER_QUERY: break
            try:
                book_res = requests.get(book_url, headers=headers)
                book_soup = BeautifulSoup(book_res.content, 'html.parser')
                img_tag = book_soup.find('img', class_='ResponsiveImage')
                if not (img_tag and img_tag.get('src')): continue

                img_data_res = requests.get(img_tag['src'], headers=headers)
                
                if not is_image_valid(io.BytesIO(img_data_res.content)):
                    continue

                counters[lang_key] += 1
                count_str = f"{counters[lang_key]:03d}"
                base_name = f"{lang_key}_{count_str}"
                img_path = os.path.join(RAW_DIR, base_name + '.jpg')
                json_path = os.path.join(RAW_DIR, base_name + '.json')

                with open(img_path, 'wb') as f:
                    f.write(img_data_res.content)
                
                img_for_api = Image.open(img_path)
                prompt = """Analyze this image. Your response MUST be a single, valid JSON object and nothing else. The JSON should have one key: "shapes". The value of "shapes" is a list of objects, each with a "label" ('text') and a "points" list of [x, y] polygon coordinates. Example: {"shapes": [{"label": "text", "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]}]}"""
                response = GEMINI_MODEL.generate_content([prompt, img_for_api])
                cleaned_response = response.text.strip().replace("json", "").replace("", "")
                data = json.loads(cleaned_response)

                labelme_output = {"version": "5.0.1", "flags": {}, "shapes": data.get("shapes", []), "imagePath": base_name + '.jpg', "imageData": None, "imageHeight": img_for_api.height, "imageWidth": img_for_api.width}
                for shape in labelme_output["shapes"]:
                    shape.update({"group_id": None, "shape_type": "polygon", "flags": {}})
                with open(json_path, 'w') as f:
                    json.dump(labelme_output, f, indent=2)

                time.sleep(1.5)
            except Exception as e:
                print(f"  An error occurred processing {book_url}. Details: {e}")
                time.sleep(3)

    print("\n--- Phase 2: Finalizing dataset for training ---")
    if os.path.exists(FINAL_DATASET_DIR): shutil.rmtree(FINAL_DATASET_DIR)

    all_files = [os.path.splitext(f)[0] for f in os.listdir(RAW_DIR) if f.endswith('.jpg')]
    if not all_files:
        print("No images were successfully processed. Exiting.")
        return
        
    train_files, test_files = train_test_split(all_files, test_size=TRAIN_TEST_SPLIT_RATIO, random_state=42)

    for split, files in [('train', train_files), ('test', test_files)]:
        img_dest, lbl_dest = os.path.join(FINAL_DATASET_DIR, split, 'images'), os.path.join(FINAL_DATASET_DIR, split, 'labels')
        os.makedirs(img_dest, exist_ok=True)
        os.makedirs(lbl_dest, exist_ok=True)

        for basename in tqdm(files, desc=f"  Creating {split} set"):
            shutil.copy(os.path.join(RAW_DIR, basename + '.jpg'), img_dest)
            with open(os.path.join(RAW_DIR, basename + '.json'), 'r') as f:
                data = json.load(f)
            
            yolo_annotations = []
            img_w, img_h = data['imageWidth'], data['imageHeight']
            for shape in data['shapes']:
                points = np.array(shape['points'])
                x_min, y_min = np.min(points, axis=0)
                x_max, y_max = np.max(points, axis=0)
                x_center, y_center = ((x_min + x_max)/2)/img_w, ((y_min + y_max)/2)/img_h
                width, height = (x_max - x_min)/img_w, (y_max - y_min)/img_h
                yolo_annotations.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
            with open(os.path.join(lbl_dest, basename + '.txt'), 'w') as f:
                f.write('\n'.join(yolo_annotations))

    print("\n--- Phase 3: Create YAML Config ---")
    yaml_content = f"path: ../{FINAL_DATASET_DIR}\ntrain: train/images\nval: test/images\ntest: test/images\nnames:\n  0: text"
    with open(os.path.join(FINAL_DATASET_DIR, 'dataset.yaml'), 'w') as f:
        f.write(yaml_content)
    
    shutil.rmtree(RAW_DIR)
    print(f"\n Pipeline complete! Your training-ready dataset is in the '{FINAL_DATASET_DIR}' folder.")

if __name__ == '__main__':
    run_pipeline()
