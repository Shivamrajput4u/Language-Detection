import requests
from bs4 import BeautifulSoup
import os
import time
from tqdm import tqdm
import urllib.parse

def scrape_goodreads_search(query, num_images=30):
    """Scrapes book cover images from a Goodreads.com search query."""
    encoded_query = urllib.parse.quote_plus(query)
    base_url = f"https://www.goodreads.com/search?q={encoded_query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'}

    print(f"Fetching book list for query: '{query}'")
    try:
        search_response = requests.get(base_url, headers=headers)
        search_response.raise_for_status()
        search_soup = BeautifulSoup(search_response.content, 'html.parser')
        
        book_links = []
        for a_tag in search_soup.find_all('a', class_='bookTitle', href=True):
            if len(book_links) < num_images:
                book_links.append("https://www.goodreads.com" + a_tag['href'])
        
        print(f"Found {len(book_links)} book links to process.")
    except Exception as e:
        print(f"Error fetching search page for '{query}': {e}")
        return

    for book_url in tqdm(book_links, desc=f"Downloading '{query}'"):
        try:
            book_response = requests.get(book_url, headers=headers)
            book_response.raise_for_status()
            book_soup = BeautifulSoup(book_response.content, 'html.parser')
            image_tag = book_soup.find('img', class_='ResponsiveImage')
            
            if image_tag and image_tag.get('src'):
                image_url = image_tag.get('src')
                img_data = requests.get(image_url, headers=headers).content
                file_name = f"{query.replace(' ', '')}{book_url.split('/')[-1].split('.')[0]}.jpg"
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, 'wb') as handler:
                    handler.write(img_data)
                time.sleep(1)
        except Exception as e:
            print(f"Could not process {book_url}. Error: {e}")

if __name__ == '__main__':
    output_dir = "book_covers_mixed"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    queries = ["हिन्दी", "ಕನ್ನಡ", "বাংলা", "தமிழ்", "मराठी", "classic fiction"]
    for q in queries:
        scrape_goodreads_search(q, num_images=30)
    print(f"\n Scraping complete! Images are in '{output_dir}'.")
