"""
Vehicle Data Scraping Pipeline - Riyasewana.com

This DAG orchestrates the scraping of vehicle listings from Riyasewana.com,
extracting vehicle details, and preprocessing the data for analysis.

Uses FlareSolverr to bypass Cloudflare protection.

Pipeline stages:
1. Scrape post links from Riyasewana.com listings
2. Extract vehicle details from each listing page
3. Preprocess and clean the extracted data

Orchestration:
- Acts as a DATA PRODUCER using Airflow Datasets
- Publishes to RIYASEWANA_DATASET when preprocessing completes
- Master DAG consumes this dataset along with Ikman dataset
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
# Dataset enables event-driven orchestration without ExternalTaskSensor
# When this DAG completes, it "produces" to a Dataset, triggering downstream consumers
from airflow.datasets import Dataset

from components.post_links_extraction import scrape_links_riyasewana
from components.post_data_extraction import scrape_and_save_riyasewana
from components.data_preprocces import data_preprocces_riyasewana
from components.utils import success_email, failure_email
from components.config import riyasewana_config


# =============================================================================
# Dataset Definition
# =============================================================================

# Dataset URI represents the logical output of this pipeline
# The Master DAG will subscribe to this dataset and trigger when it's updated
# URI format: scheme://identifier - using postgres table as the identifier
RIYASEWANA_DATASET = Dataset("postgres://riyasewana_post_data_preprocced")


# =============================================================================
# DAG Configuration
# =============================================================================

DAG_ID = "Vehicle_Data_scrape_Pipeline_Riyasewana"
DAG_DESCRIPTION = "Scrapes vehicle listings from Riyasewana.com and processes the data"
DAG_TAGS = ["vehicle", "scraping", "riyasewana", "etl", "producer"]

# Shared start_date ensures consistent scheduling across all DAGs
SHARED_START_DATE = datetime(2025, 7, 2)

DEFAULT_ARGS = {
    "owner": "shalika_Deshan",
    "depends_on_past": False,
    "start_date": SHARED_START_DATE,
    "email_on_failure": True,
    "email_on_success": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "execution_timeout": timedelta(hours=6),
}


# =============================================================================
# DAG Definition
# =============================================================================

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description=DAG_DESCRIPTION,
    # Every Friday at 4:05 PM (cron: minute hour day month weekday)
    schedule="36 17 * * 5",
    # catchup=False prevents backfill runs on DAG deployment
    catchup=False,
    tags=DAG_TAGS,
    # max_active_runs=1 prevents concurrent executions that could cause data conflicts
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    # Task 1: Scrape post links from Riyasewana.com
    scrape_post_links = PythonOperator(
        task_id="scrape_post_links_riyasewana",
        python_callable=scrape_links_riyasewana,
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Scrape Post Links
        Crawls Riyasewana.com vehicle listings using FlareSolverr
        and extracts URLs for individual posts.
        Stores links in the `riyasewana_vehicle_post_links` table.
        """,
    )

    # Task 2: Scrape vehicle details from each link
    scrape_vehicle_info = PythonOperator(
        task_id="scrape_vehicle_info_from_link_riyasewana",
        python_callable=scrape_and_save_riyasewana,
        op_kwargs={
            "source_table": riyasewana_config.links_table,
            "data_table": riyasewana_config.data_table,
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Scrape Vehicle Details
        Visits each listing URL via FlareSolverr and extracts vehicle information:
        - Make, model, year of manufacture
        - Price, mileage, engine capacity
        - Transmission, fuel type, options
        Stores data in the `riyasewana_post_data` table.
        """,
    )

    # Task 3: Preprocess extracted data
    # outlets=[RIYASEWANA_DATASET] marks this task as a Dataset producer
    # When this task succeeds, Airflow updates the Dataset, triggering any consumer DAGs
    preprocess_data = PythonOperator(
        task_id="data_proprocessing_riyasewana",
        python_callable=data_preprocces_riyasewana,
        op_kwargs={
            "source_table": riyasewana_config.data_table,
            "data_table": riyasewana_config.processed_table,
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        # Dataset outlet - signals completion to downstream consumer DAGs
        outlets=[RIYASEWANA_DATASET],
        doc_md="""
        ### Preprocess Data (Dataset Producer)
        Cleans and normalizes the scraped data:
        - Extracts numeric values from prices
        - Filters out negotiable prices
        - Normalizes text fields to uppercase
        Stores processed data in the `riyasewana_post_data_preprocced` table.

        **Publishes to RIYASEWANA_DATASET on success.**
        """,
    )

    # Define task dependencies
    scrape_post_links >> scrape_vehicle_info >> preprocess_data
