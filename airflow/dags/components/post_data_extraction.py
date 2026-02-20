"""
Post data extraction module for scraping vehicle details from listing pages.
Supports Ikman.lk and Riyasewana.com websites.
"""

import time
import random
import re
from typing import Dict, Optional, Any

import requests
import pandas as pd
from bs4 import BeautifulSoup

from components.logging_config import get_logger, TaskLogger
from components.config import (
    ikman_config,
    riyasewana_config,
    scraper_config,
    TABLE_SCHEMAS
)
from components.utils import create_table, populate_table, read_table
from components.post_links_extraction import FlareSolverrClient

logger = get_logger(__name__)

# =============================================================================
# TESTING CONFIGURATION - Comment out or set to None for production
# =============================================================================
TEST_LINK_LIMIT = None  # Set to None to process all links
# =============================================================================

# Key mapping for Ikman data normalization
IKMAN_KEY_MAPPING = {
    "Post_Link": "post_link",
    "Posted_Title": "posted_title",
    "Posted_Date": "posted_date",
    "Brand": "make",
    "Model": "model",
    "Grade": "grade",
    "Trim / Edition": "trim_edition",
    "Year of Manufacture": "yom",
    "Condition": "condition",
    "Transmission": "transmission",
    "Body type": "body_type",
    "Fuel type": "fuel_type",
    "Engine capacity": "engine_capacity",
    "Mileage": "mileage",
    "Vehicle_Price": "vehicle_price"
}


def _create_empty_ikman_record() -> Dict[str, str]:
    """Create an empty Ikman vehicle record with default values."""
    return {
        "Post_Link": "0",
        "Posted_Title": "0",
        "Posted_Date": "0",
        "Brand": "0",
        "Model": "0",
        "Grade": "0",
        "Trim / Edition": "0",
        "Year of Manufacture": "0",
        "Condition": "0",
        "Transmission": "0",
        "Body type": "0",
        "Fuel type": "0",
        "Engine capacity": "0",
        "Mileage": "0",
        "Vehicle_Price": "0"
    }


def _parse_ikman_page(soup: BeautifulSoup, link: str) -> Dict[str, str]:
    """
    Parse an Ikman vehicle detail page.

    Args:
        soup: BeautifulSoup object of the page
        link: URL of the page

    Returns:
        Dict containing vehicle information
    """
    car_info = _create_empty_ikman_record()
    car_info['Post_Link'] = link

    # Extract header and title
    header = soup.find("div", class_='title-wrapper--1lwSc')
    if header:
        title_elem = header.find('h1')
        if title_elem:
            car_info['Posted_Title'] = title_elem.get_text()

        date_elem = header.find("div", class_='subtitle-wrapper--1M5Mv')
        if date_elem:
            car_info['Posted_Date'] = re.sub('<[^<]+?>', '', str(date_elem))

    # Extract vehicle price
    price_elem = soup.find("div", class_='amount--3NTpl')
    if price_elem:
        car_info['Vehicle_Price'] = price_elem.get_text()

    # Extract vehicle details
    details_section = soup.find("div", class_='ad-meta--17Bqm')
    if details_section:
        detail_rows = details_section.find_all("div", class_='full-width--XovDn')
        for row in detail_rows:
            label_elem = row.find('div', class_='word-break--2nyVq label--3oVZK')
            value_elem = row.find('div', class_='word-break--2nyVq value--1lKHt')

            if label_elem and value_elem:
                label = label_elem.get_text().strip("' :")
                value = value_elem.get_text()
                car_info[label] = value

    # Normalize keys
    return {IKMAN_KEY_MAPPING.get(k, k): v for k, v in car_info.items()}


def scrape_and_save_ikman(source_table: str, data_table: str, **kwargs) -> int:
    """
    Scrape vehicle details from Ikman.lk listing pages.

    Args:
        source_table: Table containing listing links
        data_table: Table to store scraped data

    Returns:
        int: Number of records scraped
    """
    with TaskLogger(logger, "scrape_and_save_ikman"):
        df = read_table(source_table)
        if df is None or df.empty:
            logger.warning(f"No links found in {source_table}")
            return 0

        # Apply test limit if configured
        if TEST_LINK_LIMIT is not None:
            df = df.head(TEST_LINK_LIMIT)
            logger.info(f"TEST MODE: Limited to {TEST_LINK_LIMIT} links")

        create_table(data_table, TABLE_SCHEMAS['ikman_data'])

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; VehicleDataBot/1.0)",
            "From": "scraper@example.com"
        }

        total_records = 0
        total_links = len(df)

        for idx, link in enumerate(df['link'], 1):
            if idx % 100 == 0:
                logger.info(f"Processing link {idx}/{total_links}")

            try:
                response = requests.get(link, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                car_info = _parse_ikman_page(soup, link)
                populate_table(data_table, car_info)
                total_records += 1

                time.sleep(0.25)

            except requests.RequestException as e:
                logger.warning(f"Request error for {link}: {e}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing {link}: {e}")

        logger.info(f"Completed Ikman data extraction. Total records: {total_records}")
        return total_records


# Alias for backward compatibility
scarpe_and_save_ikman = scrape_and_save_ikman


def _parse_riyasewana_page(soup: BeautifulSoup, posted_date: str) -> Optional[Dict[str, Any]]:
    """
    Parse a Riyasewana vehicle detail page.

    Args:
        soup: BeautifulSoup object of the page
        posted_date: Date when the listing was posted

    Returns:
        Dict containing vehicle information or None if parsing failed
    """
    table = soup.find('table', class_='moret')
    if not table:
        return None

    parsed_data = {}
    rows = table.find_all('tr')

    for row in rows:
        tds = row.find_all('td')
        if len(tds) == 4:
            key1, value1 = tds[0].text.strip(), tds[1].text.strip()
            key2, value2 = tds[2].text.strip(), tds[3].text.strip()
            if key1:
                parsed_data[key1] = value1
            if key2:
                parsed_data[key2] = value2
        elif len(tds) == 2:
            key, val = tds[0].text.strip(), tds[1].text.strip()
            if key:
                parsed_data[key] = val

    return {
        "contact": parsed_data.get('Contact', ''),
        "posted_date": posted_date,
        "price": parsed_data.get('Price', ''),
        "make": parsed_data.get('Make', ''),
        "model": parsed_data.get('Model', ''),
        "yom": parsed_data.get('YOM', ''),
        "mileage": parsed_data.get('Mileage (km)', '') or parsed_data.get('Mileage', ''),
        "transmission": parsed_data.get('Gear', ''),
        "fuel_type": parsed_data.get('Fuel Type', ''),
        "options": parsed_data.get('Options', ''),
        "engine_capacity": parsed_data.get('Engine (cc)', '') or parsed_data.get('Engine', '')
    }


def scrape_and_save_riyasewana(source_table: str, data_table: str, **kwargs) -> int:
    """
    Scrape vehicle details from Riyasewana.com listing pages.

    Args:
        source_table: Table containing listing links
        data_table: Table to store scraped data

    Returns:
        int: Number of records scraped
    """
    with TaskLogger(logger, "scrape_and_save_riyasewana"):
        df = read_table(source_table)
        if df is None or df.empty:
            logger.warning(f"No links found in {source_table}")
            return 0

        # Apply test limit if configured
        if TEST_LINK_LIMIT is not None:
            df = df.head(TEST_LINK_LIMIT)
            logger.info(f"TEST MODE: Limited to {TEST_LINK_LIMIT} links")

        create_table(data_table, TABLE_SCHEMAS['riyasewana_data'])

        total_records = 0
        total_links = len(df)

        with FlareSolverrClient() as client:
            for idx, (link, posted_date) in enumerate(zip(df['link'], df['date']), 1):
                if idx % 50 == 0:
                    logger.info(f"Processing link {idx}/{total_links}")

                try:
                    if not link or pd.isna(link):
                        logger.debug("Skipping empty URL")
                        continue

                    logger.debug(f"Fetching: {link}")

                    html_content = client.fetch_page(link)
                    if not html_content:
                        logger.warning(f"Failed to fetch {link}")
                        continue

                    soup = BeautifulSoup(html_content, 'html.parser')
                    data = _parse_riyasewana_page(soup, posted_date)

                    if data:
                        populate_table(data_table, data)
                        total_records += 1
                        logger.debug(f"Extracted and saved record from {link}")
                    else:
                        logger.debug(f"No table data found on page: {link}")

                except Exception as e:
                    logger.error(f"Error scraping {link}: {e}")

                # Polite randomized delay
                time.sleep(random.uniform(
                    scraper_config.min_delay,
                    scraper_config.max_delay
                ))

        logger.info(f"Completed Riyasewana data extraction. Total records: {total_records}")
        return total_records


# Alias for backward compatibility
scarpe_and_save_riyasewana = scrape_and_save_riyasewana
