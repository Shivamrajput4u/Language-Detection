import easyocr
import json
import os
from tqdm import tqdm
from PIL import Image

def auto_annotate_images(image_dir):
    """Uses EasyOCR to generate draft annotations in LabelMe JSON format."""
    print("Loading EasyOCR model... (This will take time on first run)")
    # Using gpu=False is crucial for Codespaces
    reader = easyocr.Reader(['en', 'hi'], gpu=False) 
    
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith('.jpg')]
    print(f"Found {len(image_files)} images to annotate...")

    for filename in tqdm(image_files, desc="Auto-Annotating"):
        image_path = os.path.join(image_dir, filename)
        json_path = os.path.join(image_dir, os.path.splitext(filename)[0] + '.json')

        if os.path.exists(json_path): continue

        try:
            with Image.open(image_path) as img:
                h, w = img.height, img.width
            result = reader.readtext(image_path)

            labelme_output = {
                "version": "5.0.1", "flags": {}, "shapes": [],
                "imagePath": filename, "imageData": None,
                "imageHeight": h, "imageWidth": w,
            }

            for (bbox, text, prob) in result:
                points = [list(map(float, p)) for p in bbox]
                shape = {
                    "label": "text", "points": points, "group_id": None,
                    "shape_type": "polygon", "flags": {}
                }
                labelme_output["shapes"].append(shape)
            
            with open(json_path, 'w') as f:
                json.dump(labelme_output, f, indent=2)
        except Exception as e:
            print(f"\nError on {filename}: {e}")

if __name__ == '__main__':
    auto_annotate_images('book_covers_mixed')
    print("\n✅ Auto-annotation complete!")
