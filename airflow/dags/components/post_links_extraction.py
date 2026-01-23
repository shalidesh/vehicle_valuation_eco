import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm 
import time
import re
from pandas import DataFrame
from components.utils import create_table, populate_table
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import random
import csv
import os

# Set up Selenium with pre-installed ChromeDriver
def setup_chrome_driver():
    """Setup Chrome WebDriver using pre-installed ChromeDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run headless for no UI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # Use the pre-installed ChromeDriver path from environment or default
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome')
    
    # Set Chrome binary location
    options.binary_location = chrome_bin
    
    # Create service with the pre-installed ChromeDriver
    service = Service(executable_path=chromedriver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome driver setup successful")
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        # Fallback: try without specifying explicit paths
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
            print("Chrome driver setup successful with fallback")
            return driver
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            raise e2

# Initialize driver globally
driver = setup_chrome_driver()

def scrape_links_ikman():
    headers = {
        "User-Agent": "web-scrapping",
        "From": "youremail@example.com"  # Include your email so the website owner can contact you if necessary
    }

    page = 1
    make = ['honda', 'toyota', 'nissan', 'suzuki', 'micro', 'mitsubishi', 'mahindra', 'mazda', 'daihatsu', 'hyundai', 'kia', 'bmw', 'perodua', 'tata','audi','isuzu','renault','ford','volkswagen','land rover','jaguar','mg']
    # make = ['honda', 'toyota', 'nissan', 'suzuki', 'micro', 'mitsubishi', 'mahindra', 'mazda', 'daihatsu', 'hyundai', 'kia', 'bmw', 'perodua', 'tata']
    transmission = ['automatic', 'manual', 'tiptronic']
    fuel_type = ['petrol', 'diesel', 'hybrid', 'electric']

    create_table("ikman_vehicle_post_links", ["link VARCHAR(255)","page VARCHAR(255)","transmition VARCHAR(255)","fuel_type VARCHAR(255)"])

    # Add an outer progress bar for "make"
    for m in tqdm(make, desc="Processing Makes", unit="make"):
        for t in tqdm(transmission, desc=f"Processing Transmissions ({m})", leave=False, unit="transmission"):
            for f in tqdm(fuel_type, desc=f"Processing Fuel Types ({m}, {t})", leave=False, unit="fuel type"):
                isHaveNextPage = True
                while isHaveNextPage:
                    target_url = f'https://ikman.lk/en/ads/sri-lanka/cars/{m}?sort=date&order=desc&buy_now=0&urgent=0&page={page}&enum.transmission={t}&tree.brand={m}&enum.fuel_type={f}'
                    
                    try:
                        url = requests.get(target_url, headers=headers, timeout=10)
                        soup = BeautifulSoup(url.text, 'lxml')
                        product = soup.find('ul', class_="list--3NxGO")

                        # If no results found, stop the loop
                        if product is None or len(product.find_all("li", class_="normal--2QYVk gtm-normal-ad")) == 0:
                            isHaveNextPage = False
                            page = 1
                            print("page is no content-----------------")
                            break

                        # Add progress bar for items within a page
                        for item in tqdm(product.find_all("li", class_="normal--2QYVk gtm-normal-ad"), desc="Processing Items", leave=False):
                            anchor = item.find('a')
                            if anchor is not None:
                                link = anchor.get('href')
                                link = f"https://ikman.lk{link}"   
                                data={
                                    "link": link,
                                    "page": str(page),
                                    "transmition": t,
                                    "fuel_type": f
                                }
                                populate_table("ikman_vehicle_post_links", data)
                            else:
                                print('No anchor tag found in the item.')

                        page += 1
                        if page == 3:  # Safety break to avoid infinite loops
                            isHaveNextPage = False
                            page = 1
                            break
                        time.sleep(0.5)
                        
                    except requests.RequestException as e:
                        print(f"Request error for {target_url}: {e}")
                        time.sleep(2)  # Wait before retrying
                        continue
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                    finally:
                        cleanup_driver()



# Scrape the riyasewana website
def scrape_links_riyasewana():
    global driver
    
    threshold_date = datetime.now() - timedelta(weeks=3)

    page = 1
    makes = ['nissan', 'suzuki', 'micro', 'mitsubishi']
    # makes = ['honda', 'toyota', 'nissan', 'suzuki', 'micro', 'mitsubishi', 'mahindra', 'mazda', 'daihatsu', 'hyundai', 'kia', 'bmw', 'perodua', 'tata']
    types = ['cars', 'vans', 'suvs', 'crew-cabs', 'pickups']

    create_table("riyasewana_vehicle_post_links", ["link VARCHAR(255)","page VARCHAR(255)","date VARCHAR(255)","make VARCHAR(255)"])

    for make in makes:
        for type in types:
            isHaveNextPage = True
            while isHaveNextPage:
                try:
                    if page == 1:
                        target_url = f'https://riyasewana.com/search/{type}/{make}'
                    else:
                        target_url = f'https://riyasewana.com/search/{type}/{make}?page={page}'

                    print(f"Scraping: {target_url}")
                    driver.get(target_url)

                    time.sleep(random.uniform(3, 7))  # Random delay between 3 to 7 seconds

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    content_div = soup.find('div', id='content')

                    pagination = soup.find('div', class_='pagination')

                    if pagination is None:
                        current_page = 1
                    else:
                        current_page_element = pagination.find('a', class_="current")
                        if current_page_element:
                            current_page = current_page_element.text.strip()
                        else:
                            current_page = 1

                    current_page_number = current_page

                    if not int(current_page_number) == page:
                        isHaveNextPage = False
                        page = 1
                        break

                    ul_tag = content_div.find('ul') if content_div else None

                    if ul_tag is None or len(ul_tag.find_all('li', class_="item round")) == 0:
                        isHaveNextPage = False
                        page = 1
                        break

                    li_tags = ul_tag.find_all('li', class_="item round") if ul_tag else []

                    for li in li_tags:
                        h2_tag = li.find('h2')
                        date_div = li.find('div', class_='boxintxt s')
                        date_text = date_div.text.strip() if date_div else ""

                        try:
                            date_obj = pd.to_datetime(date_text)
                            if date_obj < pd.Timestamp(threshold_date):
                                isHaveNextPage = False
                                break
                        except ValueError:
                            print(f"Error parsing date: {date_text}")

                        if h2_tag:
                            a_tag = h2_tag.find('a')
                            if a_tag and 'href' in a_tag.attrs:
                                # Write each record to the database
                                data={
                                        "link": a_tag['href'],
                                        "page": str(page),
                                        "date": str(date_text),
                                        "make": str(make)
                                }
                                populate_table("riyasewana_vehicle_post_links", data)

                    page += 1
                    
                except Exception as e:
                    print(f"Error scraping {target_url}: {e}")
                finally:
                    cleanup_driver()


# Cleanup function to properly close the driver
def cleanup_driver():
    """Cleanup function to properly close the driver"""
    global driver
    try:
        if driver:
            driver.quit()
            print("Driver closed successfully")
    except Exception as e:
        print(f"Error closing driver: {e}")

