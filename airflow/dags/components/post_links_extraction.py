"""
Post links extraction module for scraping vehicle listing links.
Supports Ikman.lk and Riyasewana.com websites.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Optional

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
from components.utils import create_table, populate_table

logger = get_logger(__name__)


class FlareSolverrClient:
    """Client for interacting with FlareSolverr proxy service."""

    def __init__(self):
        self.url = scraper_config.flaresolverr_url
        self.headers = {"Content-Type": "application/json"}
        self.session_id: Optional[str] = None

    def create_session(self) -> bool:
        """Create a new FlareSolverr session."""
        try:
            session_data = {
                "cmd": "sessions.create",
                "session": f"session_{random.randint(1000, 9999)}"
            }
            resp = requests.post(
                self.url,
                headers=self.headers,
                json=session_data,
                timeout=10
            )
            if resp.status_code == 200 and resp.json().get('status') == 'ok':
                self.session_id = resp.json().get('session')
                logger.info(f"Created FlareSolverr session: {self.session_id}")
                return True
        except Exception as e:
            logger.warning(f"Failed to create FlareSolverr session: {e}")
        return False

    def destroy_session(self) -> None:
        """Destroy the current FlareSolverr session."""
        if self.session_id:
            try:
                destroy_data = {"cmd": "sessions.destroy", "session": self.session_id}
                requests.post(
                    self.url,
                    headers=self.headers,
                    json=destroy_data,
                    timeout=10
                )
                logger.info(f"Destroyed FlareSolverr session: {self.session_id}")
            except Exception as e:
                logger.warning(f"Failed to destroy session: {e}")
            finally:
                self.session_id = None

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch a page through FlareSolverr.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Optional[str]: HTML content or None if failed
        """
        for attempt in range(max_retries):
            try:
                fetch_data = {
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": 60000
                }
                if self.session_id:
                    fetch_data["session"] = self.session_id

                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=fetch_data,
                    timeout=scraper_config.request_timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'ok':
                        html_content = result.get('solution', {}).get('response', '')
                        if html_content:
                            return html_content
                    else:
                        logger.warning(
                            f"FlareSolverr error (attempt {attempt + 1}): "
                            f"{result.get('message', 'Unknown error')}"
                        )
                else:
                    logger.warning(f"HTTP {response.status_code} from FlareSolverr (attempt {attempt + 1})")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(random.uniform(5, 10))

        return None

    def __enter__(self):
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy_session()
        return False


def scrape_links_ikman(**kwargs) -> int:
    """
    Scrape vehicle listing links from Ikman.lk.

    Returns:
        int: Number of links scraped
    """
    with TaskLogger(logger, "scrape_links_ikman"):
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; VehicleDataBot/1.0)",
            "From": "scraper@example.com"
        }

        create_table(ikman_config.links_table, TABLE_SCHEMAS['ikman_links'])

        total_links = 0
        total_makes = len(ikman_config.makes)

        for make_idx, make in enumerate(ikman_config.makes, 1):
            logger.info(f"Processing make {make_idx}/{total_makes}: {make}")

            for transmission in ikman_config.transmissions:
                for fuel_type in ikman_config.fuel_types:
                    page = 1
                    has_next_page = True

                    while has_next_page:
                        target_url = (
                            f'{ikman_config.base_url}/en/ads/sri-lanka/cars/{make}'
                            f'?sort=date&order=desc&buy_now=0&urgent=0&page={page}'
                            f'&enum.transmission={transmission}&tree.brand={make}'
                            f'&enum.fuel_type={fuel_type}'
                        )

                        try:
                            response = requests.get(target_url, headers=headers, timeout=10)
                            soup = BeautifulSoup(response.text, 'lxml')
                            product_list = soup.find('ul', class_="list--3NxGO")

                            if not product_list:
                                logger.debug(f"No products found for {make}/{transmission}/{fuel_type} page {page}")
                                has_next_page = False
                                break

                            items = product_list.find_all("li", class_="normal--2QYVk gtm-normal-ad")
                            if not items:
                                has_next_page = False
                                break

                            for item in items:
                                anchor = item.find('a')
                                if anchor and anchor.get('href'):
                                    link = f"{ikman_config.base_url}{anchor.get('href')}"
                                    data = {
                                        "link": link,
                                        "page": str(page),
                                        "transmition": transmission,
                                        "fuel_type": fuel_type
                                    }
                                    populate_table(ikman_config.links_table, data)
                                    total_links += 1

                            page += 1
                            if page > 2:  # Limit pages per combination
                                has_next_page = False
                                break

                            time.sleep(0.5)

                        except requests.RequestException as e:
                            logger.error(f"Request error for {target_url}: {e}")
                            time.sleep(2)
                        except Exception as e:
                            logger.error(f"Unexpected error processing {target_url}: {e}")
                            has_next_page = False

        logger.info(f"Completed Ikman link scraping. Total links: {total_links}")
        return total_links


def scrape_links_riyasewana(**kwargs) -> int:
    """
    Scrape vehicle listing links from Riyasewana.com using FlareSolverr.

    Returns:
        int: Number of links scraped
    """
    with TaskLogger(logger, "scrape_links_riyasewana"):
        threshold_date = datetime.now() - timedelta(weeks=riyasewana_config.weeks_threshold)

        create_table(riyasewana_config.links_table, TABLE_SCHEMAS['riyasewana_links'])

        total_links = 0

        with FlareSolverrClient() as client:
            for make in riyasewana_config.makes:
                for vehicle_type in riyasewana_config.vehicle_types:
                    page = 1
                    consecutive_failures = 0
                    has_next_page = True

                    while has_next_page and page <= 2:
                        if page == 1:
                            target_url = f'{riyasewana_config.base_url}/search/{vehicle_type}/{make}'
                        else:
                            target_url = f'{riyasewana_config.base_url}/search/{vehicle_type}/{make}?page={page}'

                        logger.info(f"Scraping: {target_url}")

                        html_content = client.fetch_page(target_url)

                        if not html_content:
                            consecutive_failures += 1
                            logger.warning(f"Failed to fetch page (#{consecutive_failures})")
                            if consecutive_failures >= 3:
                                logger.error(f"Too many failures for {make} - {vehicle_type}, skipping")
                                break
                            time.sleep(random.uniform(10, 20))
                            continue

                        consecutive_failures = 0

                        soup = BeautifulSoup(html_content, 'html.parser')
                        content_div = soup.find('div', id='content')

                        # Check pagination
                        pagination = soup.find('div', class_='pagination')
                        current_page = 1
                        if pagination:
                            current_elem = pagination.find('a', class_='current')
                            if current_elem:
                                try:
                                    current_page = int(current_elem.text.strip())
                                except ValueError:
                                    pass

                        if current_page != page:
                            logger.warning(f"Page mismatch: expected {page}, got {current_page}")
                            has_next_page = False
                            break

                        ul_tag = content_div.find('ul') if content_div else None
                        if not ul_tag:
                            logger.debug(f"No items found on page {page}")
                            has_next_page = False
                            break

                        li_tags = ul_tag.find_all('li', class_='item round')
                        if not li_tags:
                            has_next_page = False
                            break

                        logger.info(f"Found {len(li_tags)} items on page {page}")

                        for li in li_tags:
                            date_div = li.find('div', class_='boxintxt s')
                            date_text = date_div.text.strip() if date_div else ""

                            try:
                                date_obj = pd.to_datetime(date_text)
                                if date_obj < pd.Timestamp(threshold_date):
                                    logger.info(f"Reached date cutoff: {date_text}")
                                    has_next_page = False
                                    break
                            except ValueError:
                                logger.warning(f"Error parsing date: {date_text}")

                            h2_tag = li.find('h2')
                            if h2_tag:
                                a_tag = h2_tag.find('a')
                                if a_tag and 'href' in a_tag.attrs:
                                    data = {
                                        "link": a_tag['href'],
                                        "page": str(page),
                                        "date": str(date_text),
                                        "make": str(make)
                                    }
                                    populate_table(riyasewana_config.links_table, data)
                                    total_links += 1

                        page += 1
                        time.sleep(random.uniform(3, 8))

                    # Delay between make/type combinations
                    time.sleep(random.uniform(5, 15))

        logger.info(f"Completed Riyasewana link scraping. Total links: {total_links}")
        return total_links
