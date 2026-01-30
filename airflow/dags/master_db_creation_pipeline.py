"""
Master Database Creation Pipeline

This DAG orchestrates the creation of the master vehicle valuation database
by merging data from Ikman.lk and Riyasewana.com pipelines, applying
statistical analysis, and generating summary statistics.

Pipeline stages:
1. Wait for upstream pipelines (Ikman & Riyasewana) to complete
2. Load and clean data from master vehicle table
3. Apply IQR filtering to remove outliers
4. Group data and apply conditional aggregation
5. Apply text cleaning and normalization
6. Apply price floor and ceiling filters
7. Save final summary statistics
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from components.data_preprocces import (
    merge_and_filter_yom,
    load_and_clean_data,
    apply_iqr_filter,
    group_and_aggregate,
    apply_text_cleaning,
    apply_price_filters,
    save_summary_statistics,
)
from components.utils import success_email, failure_email
from components.config import ikman_config, riyasewana_config


# =============================================================================
# DAG Configuration
# =============================================================================

DAG_ID = "Master_DB_Creation_Pipeline"
DAG_DESCRIPTION = "Creates master vehicle valuation database with statistical analysis"
DAG_TAGS = ["vehicle", "master", "statistics", "etl"]

# Intermediate table names
TABLES = {
    "input": "master_vehicle_data",
    "cleaned": "temp_cleaned_data",
    "iqr_filtered": "temp_iqr_filtered",
    "aggregated": "temp_aggregated",
    "text_cleaned": "temp_text_cleaned",
    "price_filtered": "temp_price_filtered",
    "output": "summery_statistics_table",
}

DEFAULT_ARGS = {
    "owner": "shalika_Deshan",
    "depends_on_past": False,
    "start_date": datetime(2025, 7, 2),
    "email_on_failure": True,
    "email_on_success": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "execution_timeout": timedelta(hours=2),
}

# External task sensor configuration
SENSOR_CONFIG = {
    "allowed_states": ["success"],
    "mode": "reschedule",
    "timeout": 14400,  # 4 hours
    "poke_interval": 120,  # 2 minutes
}


# =============================================================================
# DAG Definition
# =============================================================================

with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description=DAG_DESCRIPTION,
    schedule_interval="@daily",
    catchup=False,
    tags=DAG_TAGS,
    max_active_runs=1,
    doc_md=__doc__,
) as dag:

    # -------------------------------------------------------------------------
    # External Task Sensors - Wait for upstream pipelines
    # -------------------------------------------------------------------------

    wait_for_riyasewana = ExternalTaskSensor(
        task_id="wait_for_riyasewana_pipeline",
        external_dag_id="Vehicle_Data_scrape_Pipeline_Riyasewana",
        external_task_id="data_proprocessing_riyasewana",
        **SENSOR_CONFIG,
        doc_md="""
        ### Wait for Riyasewana Pipeline
        Waits for the Riyasewana data scraping pipeline to complete
        before proceeding with data merge.
        """,
    )

    wait_for_ikman = ExternalTaskSensor(
        task_id="wait_for_ikman_pipeline",
        external_dag_id="Vehicle_Data_scrape_Pipeline_Ikman",
        external_task_id="data_proprocessing_ikman",
        **SENSOR_CONFIG,
        doc_md="""
        ### Wait for Ikman Pipeline
        Waits for the Ikman data scraping pipeline to complete
        before proceeding with data merge.
        """,
    )

    # -------------------------------------------------------------------------
    # Data Processing Tasks
    # -------------------------------------------------------------------------

    # Task 0: Merge data from both sources
    task_merge_data = PythonOperator(
        task_id="merge_and_filter_yom",
        python_callable=merge_and_filter_yom,
        op_kwargs={
            "riyasewana_table": riyasewana_config.processed_table,
            "ikman_table": ikman_config.processed_table,
            "output_table": TABLES["input"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Merge and Filter Data
        - Merges data from Ikman and Riyasewana processed tables
        - Normalizes column names (price -> vehicle_price)
        - Filters records to YOM >= 2000
        - Creates the master_vehicle_data table
        """,
    )

    # Task 1: Load and clean data
    task_load_and_clean = PythonOperator(
        task_id="load_and_clean_data",
        python_callable=load_and_clean_data,
        op_kwargs={
            "input_table": TABLES["input"],
            "output_table": TABLES["cleaned"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Load and Clean Data
        - Cleans column headers (lowercase, strip whitespace)
        - Cleans data values in grouping columns
        - Converts price column to numeric
        - Drops rows with NaN values
        """,
    )

    # Task 2: Apply IQR filtering
    task_iqr_filter = PythonOperator(
        task_id="apply_iqr_filter",
        python_callable=apply_iqr_filter,
        op_kwargs={
            "input_table": TABLES["cleaned"],
            "output_table": TABLES["iqr_filtered"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Apply IQR Filter
        Removes price outliers using the IQR method:
        - Calculates Q1, Q3, and IQR
        - Removes values outside (Q1 - 1.8*IQR, Q3 + 1.8*IQR)
        """,
    )

    # Task 3: Group and aggregate
    task_group_aggregate = PythonOperator(
        task_id="group_and_aggregate",
        python_callable=group_and_aggregate,
        op_kwargs={
            "input_table": TABLES["iqr_filtered"],
            "output_table": TABLES["aggregated"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Group and Aggregate
        Groups vehicles by (make, model, yom, transmission, fuel_type) and:
        - Uses MEAN for groups with < 20 records
        - Uses MEDIAN for groups with >= 20 records
        """,
    )

    # Task 4: Apply text cleaning
    task_text_cleaning = PythonOperator(
        task_id="apply_text_cleaning",
        python_callable=apply_text_cleaning,
        op_kwargs={
            "input_table": TABLES["aggregated"],
            "output_table": TABLES["text_cleaned"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Apply Text Cleaning
        - Removes special characters and symbols
        - Cleans model names (removes make redundancy)
        - Converts all text to uppercase
        """,
    )

    # Task 5: Apply price filters
    task_price_filters = PythonOperator(
        task_id="apply_price_filters",
        python_callable=apply_price_filters,
        op_kwargs={
            "input_table": TABLES["text_cleaned"],
            "output_table": TABLES["price_filtered"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Apply Price Filters
        - Floor filter: Removes prices <= 2,000,000
        - Ceiling filters based on YOM:
            - YOM >= 2015: max 30,000,000
            - 2005 <= YOM < 2015: max 25,000,000
            - 2000 <= YOM < 2005: max 20,000,000
        """,
    )

    # Task 6: Save summary statistics
    task_save_summary = PythonOperator(
        task_id="save_summary_statistics",
        python_callable=save_summary_statistics,
        op_kwargs={
            "input_table": TABLES["price_filtered"],
            "output_table": TABLES["output"],
        },
        on_success_callback=success_email,
        on_failure_callback=failure_email,
        doc_md="""
        ### Save Summary Statistics
        Saves the final aggregated vehicle valuations to the
        `summery_statistics_table` for downstream consumption.
        """,
    )

    # -------------------------------------------------------------------------
    # Task Dependencies
    # -------------------------------------------------------------------------

    # Wait for both upstream pipelines before merging
    [wait_for_riyasewana, wait_for_ikman] >> task_merge_data

    # Sequential processing pipeline
    (
        task_merge_data
        >> task_load_and_clean
        >> task_iqr_filter
        >> task_group_aggregate
        >> task_text_cleaning
        >> task_price_filters
        >> task_save_summary
    )
