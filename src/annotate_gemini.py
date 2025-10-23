import google.generativeai as genai
import os
import json
from PIL import Image
from tqdm import tqdm
import time

# --- Configure the API Key ---
# This securely gets the key from your Codespace secrets
try:
    API_KEY = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=API_KEY)
except KeyError:
    print("ERROR: GEMINI_API_KEY not found in environment secrets.")
    print("Please follow the setup steps to add your API key to Codespaces secrets and reload the window.")
    exit()

def auto_annotate_with_gemini(image_dir):
    """Uses the Gemini API to generate annotations in LabelMe JSON format."""
    
    print("Initializing Gemini Pro Vision model...")
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"Found {len(image_files)} images to annotate...")

    for filename in tqdm(image_files, desc="Annotating with Gemini"):
        image_path = os.path.join(image_dir, filename)
        json_path = os.path.join(image_dir, os.path.splitext(filename)[0] + '.json')

        if os.path.exists(json_path):
            continue

        try:
            img = Image.open(image_path)
            
            prompt = """
            Analyze this book cover image. Identify every distinct region containing text.
            For each text region, provide the corner coordinates of its bounding polygon.
            Your response MUST be a single, valid JSON object and nothing else.
            The JSON object should have one key: "shapes".
            The value of "shapes" should be a list of objects, where each object has:
            - A "label" key with the value "text".
            - A "points" key with a list of [x, y] coordinates for the polygon.
            Example: {"shapes": [{"label": "text", "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]}]}
            """

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
                shape["group_id"] = None
                shape["shape_type"] = "polygon"
                shape["flags"] = {}

            with open(json_path, 'w') as f:
                json.dump(labelme_output, f, indent=2)

            time.sleep(1.5)

        except Exception as e:
            print(f"\nCould not process {filename}. Error: {e}")
            time.sleep(5)

    print("\n✅ Gemini annotation complete!")

if _name_ == '_main_':
    auto_annotate_with_gemini('book_covers_mixed')
