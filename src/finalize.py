import os
from collections import defaultdict

def finalize_dataset_names(root_dir="dataset"):
    """
    Renames all files in the train/test directories to a clean, sequential format.
    Example: 'हिन्दी_long_messy_name.jpg' -> 'हिन्दी_001.jpg'
    """
    print(f"--- Finalizing dataset filenames in '{root_dir}' ---")
    
    # This dictionary will keep a running count for each language prefix
    counters = defaultdict(int)
    
    # We process both train and test sets
    for split in ["train", "test"]:
        print(f"Processing '{split}' directory...")
        image_dir = os.path.join(root_dir, split, "images")
        label_dir = os.path.join(root_dir, split, "labels")
        
        # We only need to iterate through the images
        for filename in sorted(os.listdir(image_dir)):
            if not filename.lower().endswith(('.jpg', '.png')):
                continue

            # Identify the language prefix (e.g., 'हिन्दी', 'classicfiction')
            prefix = filename.split('_')[0]
            
            # Increment the counter for this language
            counters[prefix] += 1
            count_str = f"{counters[prefix]:03d}" # Formats the number as 001, 002, etc.
            
            # --- Define new filenames ---
            old_base_name = os.path.splitext(filename)[0]
            new_base_name = f"{prefix}_{count_str}"
            
            # Get the extension (.jpg)
            extension = os.path.splitext(filename)[1]
            
            # --- Define full old and new paths ---
            old_image_path = os.path.join(image_dir, filename)
            new_image_path = os.path.join(image_dir, new_base_name + extension)
            
            old_label_path = os.path.join(label_dir, old_base_name + ".txt")
            new_label_path = os.path.join(label_dir, new_base_name + ".txt")
            
            # --- Rename the files ---
            os.rename(old_image_path, new_image_path)
            # Check if a corresponding label file exists before renaming
            if os.path.exists(old_label_path):
                os.rename(old_label_path, new_label_path)

    print("\n✅ All filenames have been standardized successfully!")

if __name__ == '__main__':
    finalize_dataset_names()
