import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.propertyfinder.qa/en/search?ob=mr&c=2&page={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}
MAX_PAGES = 20


def get_text(tag):
    """Safely extract text from a tag, stripping SVG/icon noise."""
    if not tag:
        return None
    # Remove svg elements before getting text
    for svg in tag.find_all("svg"):
        svg.decompose()
    return tag.get_text(strip=True) or None


def scrape_page(page_num):
    url = BASE_URL.format(page_num)
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"  Failed page {page_num} — status {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.find_all("article")
    print(f"  Found {len(cards)} cards on page {page_num}")

    properties = []
    for card in cards:
        try:
            title_tag = card.find("h3", id=lambda x: x and x.startswith("plp-"))
            title = title_tag.get_text(strip=True) if title_tag else None

            prop_type = get_text(card.find("p", {"data-testid": "property-card-type"}))

            price_div = card.find("div", {"data-testid": "property-card-price"})
            price = price_div.find("p").get_text(strip=True) if price_div else None

            location_div = card.find("div", {"data-testid": "property-card-location"})
            location = location_div.find("p").get_text(strip=True) if location_div else None

            block = card.find("div", {"data-testid": "property-card-details"})
            bedrooms  = get_text(block.find("p", {"data-testid": "property-card-spec-bedroom"})) if block else None
            bathrooms = get_text(block.find("p", {"data-testid": "property-card-spec-bathroom"})) if block else None
            area      = get_text(block.find("p", {"data-testid": "property-card-spec-area"})) if block else None

            properties.append({
                "title": title, "type": prop_type, "price": price,
                "location": location, "bedrooms": bedrooms,
                "bathrooms": bathrooms, "area": area,
            })

        except Exception as e:
            print(f"  Skipped a card: {e}")
            continue

    return properties


all_properties = []

for page in range(1, MAX_PAGES + 1):
    print(f"Scraping page {page}...")
    results = scrape_page(page)
    all_properties.extend(results)
    time.sleep(2)

df = pd.DataFrame(all_properties)
df.to_csv("data/raw_listings.csv", index=False)
print(f"\n✅ Done! Scraped {len(df)} listings → saved to data/raw_listings.csv")