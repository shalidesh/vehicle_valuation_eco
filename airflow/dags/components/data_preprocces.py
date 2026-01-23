import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm 
import time
import re
from pandas import DataFrame
from components.utils  import create_table,populate_table,read_table

def extract_price(price):
    numbers = re.findall(r'\d+', price.replace('Rs. ', '').replace(',', ''))
    return int(numbers[0]) if numbers else None


def extract_engine(engine_cap):
    numbers = re.findall(r'\d+', engine_cap.replace(' cc', '').replace(',', ''))
    return int(numbers[0]) if numbers else None


def extract_milage(milage):
    numbers = re.findall(r'\d+', milage.replace(' km', '').replace(',', ''))
    return int(numbers[0]) if numbers else None

def extract_name(model):
    numbers = re.findall(r'\d+', model.replace('-', ' ').replace(',', ''))
    return int(numbers[0]) if numbers else None

# Function to clean and concatenate model names
def clean_model_name(model_name):
    return model_name.replace("-", "")


# Extract day and month, then construct full date string
def extract_date(posted_text):

    current_year = datetime.now().year
    match = re.search(r'(\d{1,2}) (\w{3})', posted_text)
    if match:
        day, month_str = match.groups()
        try:
            date_obj = datetime.datetime.strptime(f"{day} {month_str} {current_year}", "%d %b %Y")
            return date_obj.strftime("%Y/%m/%d")
        except ValueError:
            return None
    return None

# Scrape the sun website
def data_preprocces_ikman(source_table,data_table):


    dataset=read_table(source_table)
    # dataset = dataset.dropna()
    dataset = dataset[dataset['make'] != '0']
   
    # Apply the function to the dataset
    dataset['model'] = dataset['model'].apply(clean_model_name)
    dataset['price'] = dataset['price'].apply(extract_price)
    dataset['engine_capacity'] = dataset['engine_capacity'].apply(extract_engine)
    dataset['mileage'] = dataset['mileage'].apply(extract_milage)
    dataset['posted_date'] = dataset['posted_date'].apply(extract_date)

    # Remove records with None values in the 'Price' column
    dataset = dataset.dropna(subset=['price'])

    # Convert the 'Model' column to uppercase
    dataset['model'] = dataset['model'].astype(str).str.upper()
    dataset['make'] = dataset['make'].astype(str).str.upper()
    dataset['yom'] = dataset['yom'].astype(str).str.upper()
    dataset['transmission'] = dataset['transmission'].astype(str).str.upper()
    dataset['body_type'] = dataset['body_type'].astype(str).str.upper()
    dataset['fuel_type'] = dataset['fuel_type'].astype(str).str.upper()
    dataset['engine_capacity'] = dataset['engine_capacity'].astype(str)
    dataset['mileage'] = dataset['mileage'].astype(str)
    dataset['posted_date'] = dataset['posted_date'].astype(str)
    dataset['scrape_date'] = datetime.now().strftime('%Y/%m/%d')

    dataset=dataset[['make','posted_date','scrape_date','model','yom','transmission','fuel_type','engine_capacity','price']]

    create_table(data_table, [
                "make VARCHAR(255)",
                "posted_date VARCHAR(255)",
                "scrape_date VARCHAR(255)",
                "model VARCHAR(255)",
                "yom VARCHAR(255)",
                "transmission VARCHAR(255)",
                "fuel_type VARCHAR(255)",
                "engine_capacity VARCHAR(255)",
                "price VARCHAR(255)"
            ])
    # Insert records one by one into the table
    for _, row in dataset.iterrows():
        populate_table(data_table, row.to_dict())



# Scrape the sun website
def data_preprocces_riyasewana(source_table,data_table):

    dataset=read_table(source_table)

    dataset = dataset[dataset['price'] != 'Negotiable']

    dataset['price'] = dataset['price'].apply(extract_price)

    # Remove records with None values in the 'Price' column
    dataset = dataset.dropna(subset=['price'])

    # Convert the 'Model' column to uppercase
    dataset['model'] = dataset['model'].str.upper() 
    dataset['make'] = dataset['make'].str.upper()
    dataset['transmission'] = dataset['transmission'].str.upper()
    dataset['fuel_type'] = dataset['fuel_type'].str.upper()
    dataset['posted_date'] = dataset['posted_date'].astype(str)
    dataset['scrape_date'] = datetime.now().strftime('%Y/%m/%d')

    dataset=dataset[['make','model','posted_date','scrape_date','mileage','yom','transmission','fuel_type','engine_capacity','price']]

    create_table(data_table, [
                "make VARCHAR(255)",
                "posted_date VARCHAR(255)",
                "scrape_date VARCHAR(255)",
                "model VARCHAR(255)",
                "yom VARCHAR(255)",
                "mileage VARCHAR(255)",
                "transmission VARCHAR(255)",
                "fuel_type VARCHAR(255)",
                "engine_capacity VARCHAR(255)",
                "price VARCHAR(255)"
            ])
    # Insert records one by one into the table
    for _, row in dataset.iterrows():
        populate_table(data_table, row.to_dict())

