# Otodom Rental Listings Scraper

A Python web scraper that collects apartment rental listings from [otodom.pl](https://www.otodom.pl), one of Poland's largest real estate platforms, and exports the results to CSV.

## Overview

Otodom is built with Next.js, which means most listing data isn't present as plain HTML — it's embedded in a `__NEXT_DATA__` JSON blob that the page uses to render content client-side. Instead of fragile CSS-selector scraping, this project extracts and parses that JSON directly, making it far more resilient to front-end/design changes.

## Features

- Scrapes all paginated search result pages for a given city/filter combination
- Extracts key listing details: title, transaction type, location, price, rent, area, room count, date posted, and direct link
- Deduplicates listings (some ads appear more than once in search results, e.g. promoted listings)
- Randomized delays between requests to avoid hammering the server
- Exports clean, structured data to CSV

## Data Extracted Per Listing

| Field | Description |
|---|---|
| `title` | Listing title |
| `transaction` | Transaction type (e.g. RENT) |
| `location` | City and street |
| `price` | Total price (PLN) |
| `rentPrice` | Additional rent/service charge (PLN) |
| `area` | Living area (m²) |
| `roomsNumber` | Number of rooms |
| `datePosted` | Date the listing was first created |
| `link` | Direct URL to the listing |

## Tech Stack

- `requests` — HTTP requests with session handling and custom headers
- `BeautifulSoup4` — HTML parsing (used to locate the `__NEXT_DATA__` script tag)
- `json` — Parsing the embedded Next.js data payload
- `csv` — Exporting results

## Installation

```bash
git clone https://github.com/volobuiev/otodom-scraper.git
cd otodom-scraper
pip install -r requirements.txt
```

## Usage

Edit the `baseUrl` in `main.py` to target the city and filters you want (or extend the script to accept command-line arguments), then run:

```bash
python main.py
```

Results are saved to `parsed_listings.csv` in the project directory.

## How It Works

1. **Fetch** — Sends an HTTP GET request to a search results page with browser-like headers.
2. **Parse HTML** — Loads the response into BeautifulSoup and locates the `<script id="__NEXT_DATA__">` tag.
3. **Extract JSON** — Parses that tag's contents as JSON, which contains the full listing dataset used to render the page.
4. **Paginate** — Repeats the process across all result pages, with randomized delays between requests.
5. **Deduplicate** — Removes duplicate listings (matched by ID and by content) that otherwise show up multiple times in the results.
6. **Export** — Writes the cleaned, structured data to a CSV file.

## Project Structure

```
otodom-scraper/
├── main.py              # Main scraper script
├── requirements.txt     # Python dependencies
└── README.md
```

## Notes & Limitations

- This project was built for educational purposes to practice web scraping, JSON parsing, and working with real-world messy data.
- Scraping behavior respects `robots.txt` and uses reasonable request delays; it is not designed to bypass anti-bot protections.
- Otodom's page structure may change over time, which could require updates to the JSON parsing paths.

## Possible Improvements

- Add CLI arguments for city, price range, and number of pages
- Add logging instead of print statements
- Add unit tests for the parsing logic
- Store results in a database instead of (or in addition to) CSV
- Add price-per-m² trend tracking over multiple scraping runs
