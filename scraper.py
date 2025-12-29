import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_brand_data():
    base_url = "https://web-scraping.dev"
    
    #HEADERS
    headers = {
        "x-secret-token": "secret123",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://web-scraping.dev/testimonials",
        "Content-Type": "application/json"
    }
    
    final_data = {"products": [], "testimonials": [], "reviews": []}

    # 1. PRODUCTS 
    print("Scraping Products...")
    for p in range(1, 7):
        res = requests.get(f"{base_url}/products?page={p}")
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.product')
        if not items: break
        for item in items:
            final_data["products"].append({
                "name": item.select_one('h3').text.strip(),
                "price": item.select_one('.price').text.strip()
            })

    # 2. TESTIMONIALS 
    print("Scraping Testimonials...")
    p = 1
    while True:
        res = requests.get(f"{base_url}/api/testimonials?page={p}", headers=headers)
        if res.status_code != 200 or not res.text.strip(): break
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.testimonial')
        if not items: break
        for item in items:
            final_data["testimonials"].append({
                "text": item.select_one('.text').text.strip(),
                "author": item.select_one('identicon-svg')['username'] if item.select_one('identicon-svg') else "User"
            })
        p += 1

    # 3. REVIEWS 
    print("Scraping Reviews...")
    graphql_url = f"{base_url}/api/graphql"
    has_next_page = True
    after_cursor = None # Starts at the beginning

    while has_next_page:
        payload = {
            "query": """
            query GetReviews($first: Int, $after: String) {
              reviews(first: $first, after: $after) {
                edges {
                  node {
                    text
                    date
                  }
                  cursor
                }
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
            }
            """,
            "variables": {
                "first": 20,
                "after": after_cursor
            }
        }
        
        try:
            res = requests.post(graphql_url, json=payload, headers=headers)
            data = res.json()
            reviews_data = data.get('data', {}).get('reviews', {})
            
            # Extract reviews from the 'edges'
            edges = reviews_data.get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                final_data["reviews"].append({
                    "text": node.get('text', ''),
                    "date": node.get('date', '2023-01-01')
                })
            
            # Update pagination info for the next loop
            page_info = reviews_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor', None)
            
            if not edges: break
            time.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")
            break

    with open('data.json', 'w') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"DONE! Total: {len(final_data['products'])} Products, {len(final_data['testimonials'])} Testimonials, {len(final_data['reviews'])} Reviews.")

if __name__ == "__main__":
    scrape_brand_data()