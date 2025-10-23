import requests
from bs4 import BeautifulSoup
import os
import time
from tqdm import tqdm
import argparse

def scrape_amazon_indic(query, num_images=25):
    """Scrapes book cover images from an Amazon.in search query."""
    
    # --- Configuration ---
    base_url = f"https://www.amazon.in/s?k={query}"
    output_dir = "data_indic"
    
    # --- MORE REALISTIC HEADERS ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1', # Do Not Track
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

    # --- Setup ---
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # --- Step 1: Fetch Search Page and find images ---
    print(f"Fetching search results for query: '{query}'")
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        image_tags = soup.find_all('img', class_='s-image', src=True)
        
        if not image_tags:
            print("Could not find any image tags with class 's-image'. The page structure might have changed.")
            return

        print(f"Found {len(image_tags)} potential images. Downloading the first {num_images}...")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching search page: {e}")
        return

    # --- Step 2: Download the images ---
    download_count = 0
    for img_tag in tqdm(image_tags, desc=f"Downloading '{query}' covers"):
        if download_count >= num_images:
            break
        
        try:
            image_url = img_tag['src']
            
            if 'images/I/01' in image_url or 'images/G/01' in image_url:
                continue

            img_data = requests.get(image_url, headers=headers).content
            
            file_name = f"{query.replace('+', '')}{download_count+1}.jpg"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, 'wb') as handler:
                handler.write(img_data)
            
            download_count += 1
            time.sleep(1) # Be polite

        except Exception as e:
            print(f"An unexpected error occurred for image {image_url}: {e}")

    print(f"\nScraping complete. Downloaded {download_count} images to '{output_dir}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape book covers from Amazon.in")
    parser.add_argument('--query', type=str, required=True, help='Search query (e.g., "kannada+books")')
    parser.add_argument('--num', type=int, default=25, help='Number of images to download')
    args = parser.parse_args()
    
    scrape_amazon_indic(args.query, args.num)
