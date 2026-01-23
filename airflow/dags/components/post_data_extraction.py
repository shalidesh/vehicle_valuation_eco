import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm 
import time
import re
from pandas import DataFrame
from components.utils import create_table, populate_table,read_table
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


def scarpe_and_save_ikman(source_table,data_table):

    df=read_table(source_table)
    create_table(data_table, [
                "post_link VARCHAR(255)",
                "posted_title VARCHAR(255)",
                "posted_date VARCHAR(255)",
                "make VARCHAR(255)",
                "model VARCHAR(255)",
                "grade VARCHAR(255)",
                "trim_edition VARCHAR(255)",
                "yom VARCHAR(255)",
                "condition VARCHAR(255)",
                "transmission VARCHAR(255)",
                "body_type VARCHAR(255)",
                "fuel_type VARCHAR(255)",
                "engine_capacity VARCHAR(255)",
                "mileage VARCHAR(255)",
                "vehicle_price VARCHAR(255)"
    ])     

    # Iterate over the links
    for link in tqdm(df['link']):
        
        car_info = {
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

        try:
            headers = {
                "User-Agent": "web-scrapping",
                "From": "youremail@example.com"
            }

            car_info['Post_Link'] = link
            response = requests.get(link, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the header and title
            header = soup.find("div", class_='title-wrapper--1lwSc')
            posted_title_name = header.find('h1').get_text() if header and header.find('h1') else ""
            car_info['Posted_Title'] = posted_title_name

            posted_date = header.find("div", class_='subtitle-wrapper--1M5Mv') if header else None
            posted_date_str = re.sub('<[^<]+?>', '', str(posted_date)) if posted_date else ""
            car_info['Posted_Date'] = posted_date_str

            # Extract the vehicle price
            vehicle_price = soup.find("div", class_='amount--3NTpl')
            price = vehicle_price.get_text() if vehicle_price else ""
            car_info['Vehicle_Price'] = price

            # Extract vehicle details
            vehicle_details = soup.find("div", class_='ad-meta--17Bqm')
            vehicle_details_table_rows = vehicle_details.find_all("div", class_='full-width--XovDn') if vehicle_details else []

            for row in vehicle_details_table_rows:
                tag = row.find('div', class_='word-break--2nyVq label--3oVZK')
                label = tag.get_text() if tag else ""
                tag1 = row.find('div', class_='word-break--2nyVq value--1lKHt')
                value = tag1.get_text() if tag1 else ""
                car_info[label.strip("' :")] = value

            # Mapping old key names to new ones
            key_mapping = {
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
                "Vehicle_Price": "price"
            }

            # Create a new dictionary with updated keys
            car_info_updated = {key_mapping.get(k, k): v for k, v in car_info.items()}

            populate_table(data_table, car_info_updated)
            time.sleep(0.25)

        except requests.RequestException as e:
            print(f"Request error for {link}: {e}")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            cleanup_driver()

        

def scarpe_and_save_riyasewana(source_table,data_table):
    global driver

    df=read_table(source_table)
    create_table(data_table, [
                "contact VARCHAR(255)",
                "posted_date VARCHAR(255)",
                "price VARCHAR(255)",
                "make VARCHAR(255)",
                "model VARCHAR(255)",
                "yom VARCHAR(255)",
                "mileage VARCHAR(255)",
                "transmision VARCHAR(255)",
                "fuel_type VARCHAR(255)",
                "options VARCHAR(255)",
                "engine_capacity VARCHAR(255)"
            
    ])     

    # Iterate over the links
    for link, posted_date in tqdm(zip(df['link'], df['posted_date']), total=len(df)):

        try:
            # Visit the URL
            driver.get(link)
            
            # Wait for the page to fully load
            time.sleep(3)
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract <tr> tags that contain <td> with specific classes
            table = soup.find('table', class_='moret')
            if table:
                rows = table.find_all('tr')
                data = {}
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) == 4:
                        key1 = tds[0].text.strip()
                        value1 = tds[1].text.strip()
                        key2 = tds[2].text.strip()
                        value2 = tds[3].text.strip()
                        if key1 and value1:
                            data[key1] = value1
                        if key2 and value2:
                            data[key2] = value2
                
                data={
                    "contact":data.get('Contact', ''),
                    "posted_date":posted_date,
                    "price":data.get('Price', ''),
                    "make":data.get('Make', ''),
                    "model":data.get('Model', ''),
                    "yom":data.get('YOM', ''),
                    "mileage":data.get('Mileage (km)', ''),
                    "transmision":data.get('Gear', ''),
                    "fuel_type":data.get('Fuel Type', ''),
                    "options":data.get('Options', ''),
                    "engine_capacity":data.get('Engine (cc)', '')
                }

                populate_table(data_table, data)

        except Exception as e:
            print(f"Error scraping {link}: {e}")
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

        
    
    
