import requests
import json
import time
import random
import sqlite3
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
CITY = "szczecin"

baseUrl = f'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/zachodniopomorskie/{CITY}/{CITY}/{CITY}?ownerTypeSingleSelect=ALL&limit=36&page='
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://google.com",
    "Connection": "keep-alive",
}

session = requests.Session()
session.headers.update(headers)

ROOMS_MAPPING = {
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
    "MORE": 6,
}

def convert_rooms(value):
    return ROOMS_MAPPING.get(value, None)

def connection(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred: {e}")
        return None

def make_soup(response):
    if response is not None:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return None
    
def extract_json(soup):
    if soup:
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            return json.loads(script_tag.string)
    return None

def get_listings(data):
    props = data.get("props") or {}
    page_props = props.get("pageProps") or {}
    inner_data = page_props.get("data") or {}
    search_ads = inner_data.get("searchAds") or {}
    items = search_ads.get("items") or []
    return items

def parse_listing(item):

    location_data = item.get("location") or {}
    address = location_data.get("address") or {}
    city = address.get("city") or {}
    street = address.get("street") or {}

    city_name = city.get("name", "")
    street_name = street.get("name", "")
    location = ", ".join(filter(None, [city_name, street_name]))
    date_posted = item.get("createdAtFirst") or ""
    href = item.get("href") or ""
    href = href.replace("[lang]", "")
    href = href.replace("/ad/", "")
    link = (f"https://www.otodom.pl/pl/oferta/{href}" if href else "")

    total_price_data = item.get("totalPrice") or {}
    rent_price_data = item.get("rentPrice") or {}

    total_price = total_price_data.get("value", 0) or 0
    rent_price = rent_price_data.get("value", 0) or 0

    return {
        "title": item.get("title", ""),
        "transaction_type": item.get("transaction", ""),
        "location": location,
        "price": total_price,
        "rentPrice": rent_price,
        "area": item.get("areaInSquareMeters", 0),
        "roomsNumber": convert_rooms(item.get("roomsNumber", 0)),
        "datePosted": date_posted,
        "link": link,
    }

def save_to_db(parsed_listings, db_name="listings.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            transaction_type TEXT,
            location TEXT,
            price REAL,
            rentPrice REAL,
            area REAL,
            roomsNumber INTEGER,
            datePosted TEXT,
            link TEXT UNIQUE
        )
    """)
    for listing in parsed_listings:
        cursor.execute("""
            INSERT OR IGNORE INTO apartments (title, transaction_type, location, price, rentPrice, area, roomsNumber, datePosted, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing["title"],
            listing["transaction_type"],
            listing["location"],
            listing["price"],
            listing["rentPrice"],
            listing["area"],
            listing["roomsNumber"],
            listing["datePosted"],
            listing["link"]
        ))
    conn.commit()
    conn.close()

def deduplicate_by_content(items):
    seen = set()
    unique_items = []
    for item in items:
        key = (
            item.get("title"),
            item.get("areaInSquareMeters"),
            (item.get("totalPrice") or {}).get("value"),
        )
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    return unique_items

def get_total_pages(data):
    props = data.get("props") or {}
    page_props = props.get("pageProps") or {}
    tracking = page_props.get("tracking") or {}
    listing = tracking.get("listing") or {}
    return listing.get("page_count", 1)

def main():
    all_listings = []
    response = connection(baseUrl + "1")
    soup = make_soup(response)
    data = extract_json(soup)
    if data is None:
        logging.error("Data extraction failed for the first page. Exiting.")
        return
    total_pages = get_total_pages(data)
    for pageNumber in range(1, total_pages + 1):
        url = baseUrl + str(pageNumber)
        response = connection(url)
        soup = make_soup(response)
        data = extract_json(soup)
        if data is None:
            logging.error(f"Failed to extract JSON data for {url}")
            continue
        
        listings = get_listings(data)
        all_listings.extend(listings)
        time.sleep(random.uniform(1, 3))

    all_listings = deduplicate_by_content(all_listings)
    parsed_listings = [parse_listing(item) for item in all_listings]
    
    save_to_db(parsed_listings)

if __name__ == "__main__":
    main()