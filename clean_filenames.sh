#!/bin/bash
echo "--- Starting filename cleanup ---"
DATASET_DIR="dataset"

find "$DATASET_DIR" -type f | while read -r filepath; do
    dir=$(dirname "$filepath")
    filename=$(basename "$filepath")

    if [[ "$filename" == \? ]]; then
        new_filename="${filename%%\?*}"
        extension="${filename##*.}"
        new_filepath="$dir/$new_filename.$extension"
        mv "$filepath" "$new_filepath"
    fi
done

echo "✅ Filename cleaning complete."
