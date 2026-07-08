# Otodom Rental Listings Scraper

A Python web scraper that collects apartment rental listings from [otodom.pl](https://www.otodom.pl), one of Poland's largest real estate platforms, and stores the results in a SQLite database for further analysis.

## Overview

Otodom is built with Next.js, which means most listing data isn't present as plain HTML — it's embedded in a `__NEXT_DATA__` JSON blob that the page uses to render content client-side. Instead of fragile CSS-selector scraping, this project extracts and parses that JSON directly, making it far more resilient to front-end/design changes.

## Features

- Automatically detects the total number of result pages and scrapes all of them for a given city
- Extracts key listing details: title, transaction type, location, price, rent, area, room count, date posted, and direct link
- Converts room count from Otodom's internal enum format (`"ONE"`, `"TWO"`, etc.) into plain integers for easier querying and analysis
- Deduplicates listings within a single run (some ads appear more than once in search results, e.g. promoted listings)
- Deduplicates across runs at the database level, so re-running the scraper never creates duplicate rows for the same listing
- Randomized delays between requests to avoid hammering the server
- Structured logging instead of print statements
- Stores clean, structured data in a SQLite database, ready for SQL-based analysis

## Data Extracted Per Listing

| Field | Description |
|---|---|
| `title` | Listing title |
| `transaction_type` | Transaction type (e.g. RENT) |
| `location` | City and street |
| `price` | Total price (PLN) |
| `rentPrice` | Additional rent/service charge (PLN) |
| `area` | Living area (m²) |
| `roomsNumber` | Number of rooms (integer) |
| `datePosted` | Date the listing was first created |
| `link` | Direct URL to the listing (unique key used for deduplication) |

## Tech Stack

- `requests` — HTTP requests with session handling and custom headers
- `BeautifulSoup4` — HTML parsing (used to locate the `__NEXT_DATA__` script tag)
- `json` — Parsing the embedded Next.js data payload
- `sqlite3` — Storing results in a local SQLite database
- `logging` — Structured runtime logging

## Installation

```bash
git clone https://github.com/volobuiev/otodom-scraper.git
cd otodom-scraper
pip install -r requirements.txt
```

## Usage

Edit the `CITY` variable in `main.py` to target the city you want (the script builds the search URL automatically), then run:

```bash
python main.py
```

Results are saved to `listings.db`, a SQLite database file, in the project directory.

## Querying the Results

Any SQLite client works — [DB Browser for SQLite](https://sqlitebrowser.org/) is a good free option for browsing the data visually and running queries. A few examples:

```sql
-- Average price by number of rooms
SELECT roomsNumber, AVG(price)
FROM apartments
GROUP BY roomsNumber;

-- Top 5 cheapest listings
SELECT title, price, area, link
FROM apartments
ORDER BY price ASC
LIMIT 5;

-- Number of listings per location
SELECT location, COUNT(*)
FROM apartments
GROUP BY location
ORDER BY COUNT(*) DESC;
```

## How It Works

1. **Fetch** — Sends an HTTP GET request to a search results page with browser-like headers, reusing a single `requests.Session`.
2. **Parse HTML** — Loads the response into BeautifulSoup and locates the `<script id="__NEXT_DATA__">` tag.
3. **Extract JSON** — Parses that tag's contents as JSON, which contains the full listing dataset used to render the page.
4. **Paginate** — Reads the total page count from the response and repeats the process across all result pages, with randomized delays between requests.
5. **Deduplicate** — Removes duplicate listings (matched by title, area, and price) that otherwise show up multiple times within the same run.
6. **Transform** — Normalizes fields such as room count into query-friendly types.
7. **Store** — Inserts the cleaned, structured data into a SQLite database, skipping any listing whose link already exists from a previous run.

## Project Structure

```
otodom-scraper/
├── main.py              # Main scraper script
├── requirements.txt     # Python dependencies
├── listings.db          # SQLite database (created after first run)
└── README.md
```

## Notes & Limitations

- This project was built for educational purposes to practice web scraping, JSON parsing, working with real-world messy data, and SQL-based data storage/analysis.
- Scraping behavior respects `robots.txt` and uses reasonable request delays; it is not designed to bypass anti-bot protections.
- Otodom's page structure may change over time, which could require updates to the JSON parsing paths.

## Possible Improvements

- Add CLI arguments for city, price range, and number of pages
- Add unit tests for the parsing logic
- Track price-per-m² trends over multiple scraping runs by keeping a scrape-date column
- Add a simple analysis/reporting script (e.g. with pandas or matplotlib) on top of the SQLite data