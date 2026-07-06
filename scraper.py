import requests
import json
import csv
import time
import random
from bs4 import BeautifulSoup

CITY = "szczecin"
OUTPUT_FILE = "parsed_listings.csv"

baseUrl = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/zachodniopomorskie/szczecin/szczecin/szczecin?ownerTypeSingleSelect=ALL&limit=36&page='
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

def connection(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
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
        "transaction": item.get("transaction", ""),
        "location": location,
        "price": total_price,
        "rentPrice": rent_price,
        "area": item.get("areaInSquareMeters", 0),
        "roomsNumber": item.get("roomsNumber", 0),
        "datePosted": date_posted,
        "link": link,
    }

def save_to_csv(parsed_listings, filename=OUTPUT_FILE):
    if not parsed_listings:
        print("Немає даних для збереження")
        return

    fieldnames = ["title", "transaction", "location", "price", "rentPrice", "area", "roomsNumber", "datePosted", "link"]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parsed_listings)

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
    #ret = data['props']['pageProps']['tracking']['listing']['page_count'] or 1
    return 1
################################################################################
#dont forget to change the return value to ret when you want to scrape all pages
################################################################################
def main():
    all_listings = []
    response = connection(baseUrl + "1")
    soup = make_soup(response)
    data = extract_json(soup)
    total_pages = get_total_pages(data)
    for pageNumber in range(1, total_pages + 1):
        url = baseUrl + str(pageNumber)
        response = connection(url)
        soup = make_soup(response)
        data = extract_json(soup)
        if data is None:
            print(f"Failed to extract JSON data for {url}")
            continue
        
        listings = get_listings(data)
        all_listings.extend(listings)
        time.sleep(random.uniform(1, 3))

    all_listings = deduplicate_by_content(all_listings)
    parsed_listings = [parse_listing(item) for item in all_listings]
    
    save_to_csv(parsed_listings)

if __name__ == "__main__":
    main()