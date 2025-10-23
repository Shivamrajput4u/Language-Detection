import os
import re
from collections import defaultdict

def master_cleanup(root_dir="dataset"):
    """
    A robust, two-phase script to first sanitize and then standardize all filenames.
    """
    print("--- Starting Master Filename Cleanup ---")
    
    # --- Phase 1: Brute-force Sanitization ---
    # Remove all URL parameters and special characters from every file.
    print("\n--- Phase 1: Sanitizing all filenames... ---")
    for subdir, dirs, files in os.walk(root_dir):
        for filename in files:
            # Keep only the part of the name before the '?'
            clean_base = filename.split('?')[0]
            
            # Re-add the original extension
            extension = os.path.splitext(filename)[1].split('?')[0]
            if not clean_base.endswith(extension):
                clean_name = clean_base + extension
            else:
                clean_name = clean_base

            if clean_name != filename:
                os.rename(os.path.join(subdir, filename), os.path.join(subdir, clean_name))

    print("✅ Sanitization complete.")

    # --- Phase 2: Standardization ---
    # Rename all files to the clean 'language_XXX' format.
    print("\n--- Phase 2: Standardizing to sequential names... ---")
    counters = defaultdict(int)
    for split in ["train", "test"]:
        image_dir = os.path.join(root_dir, split, "images")
        label_dir = os.path.join(root_dir, split, "labels")
        
        for filename in sorted(os.listdir(image_dir)):
            # Extract the language prefix (works for both 'हिन्दी' and 'classicfiction')
            # This regex finds the initial non-numeric part of the string.
            match = re.match(r'([^\d_]+)', filename)
            if not match: continue
            
            prefix = match.group(1).replace('-', '_') # Sanitize prefix itself
            counters[prefix] += 1
            count_str = f"{counters[prefix]:03d}"
            
            old_base = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]
            new_base = f"{prefix}_{count_str}"
            
            # Rename image and its corresponding label
            os.rename(os.path.join(image_dir, filename), os.path.join(image_dir, new_base + extension))
            if os.path.exists(os.path.join(label_dir, old_base + ".txt")):
                os.rename(os.path.join(label_dir, old_base + ".txt"), os.path.join(label_dir, new_base + ".txt"))

    print("✅ Standardization complete.")
    print("\n🚀 Dataset is now 100% clean and ready!")

if __name__ == '__main__':
    master_cleanup()
