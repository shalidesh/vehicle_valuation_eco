"""
Vehicle Data Scraping Pipeline - Ikman.lk

This DAG orchestrates the scraping of vehicle listings from Ikman.lk,
extracting vehicle details, and preprocessing the data for analysis.

Pipeline stages:
1. Scrape post links from Ikman.lk listings
2. Extract vehicle details from each listing page
3. Preprocess and clean the extracted data
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from components.post_links_extraction import scrape_links_ikman
from components.post_data_extraction import scrape_and_save_ikman
from components.data_preprocces import data_preprocces_ikman
from components.utils import success_email, failure_email
from components.config import ikman_config


# =============================================================================
# DAG Configuration
# =============================================================================

DAG_ID = "Vehicle_Data_scrape_Pipeline_Ikman"
DAG_DESCRIPTION = "Scrapes vehicle listings from Ikman.lk and processes the data"
DAG_TAGS = ["vehicle", "scraping", "ikman", "etl"]

DEFAULT_ARGS = {
    "owner": "shalika_Deshan",
    "depends_on_past": False,
    "start_date": datetime(2025, 7, 2),
    "email_on_failure": True,
    "email_on_success": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "execution_timeout": timedelta(hours=4),
}


# =============================================================================
# DAG Definition
# =============================================================================

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description=DAG_DESCRIPTION,
    schedule_interval=None,  # Triggered by Riyasewana DAG
    catchup=False,
    tags=DAG_TAGS,
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    # Task 1: Scrape post links from Ikman.lk
    scrape_post_links = PythonOperator(
        task_id="scrape_post_links_ikman",
        python_callable=scrape_links_ikman,
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Scrape Post Links
        Crawls Ikman.lk vehicle listings and extracts URLs for individual posts.
        Stores links in the `ikman_vehicle_post_links` table.
        """,
    )

    # Task 2: Scrape vehicle details from each link
    scrape_vehicle_info = PythonOperator(
        task_id="scrape_vehicle_info_from_link_ikman",
        python_callable=scrape_and_save_ikman,
        op_kwargs={
            "source_table": ikman_config.links_table,
            "data_table": ikman_config.data_table,
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Scrape Vehicle Details
        Visits each listing URL and extracts vehicle information including:
        - Make, model, year
        - Price, mileage, engine capacity
        - Transmission, fuel type
        Stores data in the `ikman_post_data` table.
        """,
    )

    # Task 3: Preprocess extracted data
    preprocess_data = PythonOperator(
        task_id="data_proprocessing_ikman",
        python_callable=data_preprocces_ikman,
        op_kwargs={
            "source_table": ikman_config.data_table,
            "data_table": ikman_config.processed_table,
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Preprocess Data
        Cleans and normalizes the scraped data:
        - Extracts numeric values from prices, mileage, engine capacity
        - Normalizes text fields to uppercase
        - Filters invalid records
        Stores processed data in the `ikman_post_data_preprocced` table.
        """,
    )

    # Define task dependencies
    scrape_post_links >> scrape_vehicle_info >> preprocess_data
