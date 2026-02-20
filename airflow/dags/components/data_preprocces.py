"""
Data preprocessing module for vehicle data.
Handles cleaning, transformation, and statistical analysis.
"""

import re
from datetime import datetime
from typing import Optional, List

import numpy as np
import pandas as pd

from components.logging_config import get_logger, TaskLogger
from components.config import stats_config, TABLE_SCHEMAS
from components.utils import create_table, populate_table, read_table, ensure_table_exists

logger = get_logger(__name__)


# ============================================================================
# Data Extraction Helpers
# ============================================================================

def extract_price(price: str) -> Optional[int]:
    """Extract numeric price from string."""
    numbers = re.findall(r'\d+', str(price).replace('Rs. ', '').replace(',', ''))
    return int(numbers[0]) if numbers else None


def extract_engine(engine_cap: str) -> Optional[int]:
    """Extract engine capacity in cc from string."""
    numbers = re.findall(r'\d+', str(engine_cap).replace(' cc', '').replace(',', ''))
    return int(numbers[0]) if numbers else None


def extract_mileage(mileage: str) -> Optional[int]:
    """Extract mileage in km from string."""
    numbers = re.findall(r'\d+', str(mileage).replace(' km', '').replace(',', ''))
    return int(numbers[0]) if numbers else None


def clean_model_name(model_name: str) -> str:
    """Clean and normalize model name."""
    return str(model_name).replace("-", "")


def extract_date(posted_text: str) -> Optional[str]:
    """Extract and format date from posted text."""
    current_year = datetime.now().year
    match = re.search(r'(\d{1,2}) (\w{3})', str(posted_text))
    if match:
        day, month_str = match.groups()
        try:
            date_obj = datetime.strptime(f"{day} {month_str} {current_year}", "%d %b %Y")
            return date_obj.strftime("%Y/%m/%d")
        except ValueError:
            return None
    return None


# ============================================================================
# Statistical Helpers
# ============================================================================

def conditional_agg(series: pd.Series) -> float:
    """
    Apply conditional aggregation logic.
    Uses mean for small groups, median for larger groups.
    """
    if len(series) < stats_config.min_records_for_median:
        return series.mean()
    return series.median()


def clean_model_redundancy(row: pd.Series) -> str:
    """Remove make name and duplicates from model string."""
    make = str(row['make']).strip().lower()
    model_str = str(row['model']).strip().lower()

    try:
        year_int = int(row['yom'])
        year_str = str(year_int)
    except:
        year_str = str(row['yom']).strip()
    
    words = model_str.split()
    cleaned_words = []
    seen = set()
        
    for word in words:
        # Skip if word is brand OR a repeat OR if word equals the year
        if word != make and word not in seen and word != year_str:
            cleaned_words.append(word)
            seen.add(word)

    return " ".join(cleaned_words)


def check_ceiling(row: pd.Series, value_col: str = 'Fixed_value') -> bool:
    """Check if price is within YOM-based ceiling limits."""
    try:
        yom = int(row['yom'])
        price = row[value_col]

        for min_yom, max_yom, max_price in stats_config.ceiling_rules:
            if min_yom <= yom < max_yom and price > max_price:
                return False
        return True
    except (ValueError, KeyError):
        return True

 # B. Apply Year-based Ceilings
def check_ceiling_raw(row):
    year = int(row['yom'])
    price = float(row['vehicle_price'])
    
    if year >= 2015 and price > 30000000:
        return False
    if 2005 <= year < 2015 and price > 25000000:
        return False
    if 2000 <= year < 2005 and price > 20000000:
        return False
    
    return True


# ============================================================================
# Ikman Data Preprocessing
# ============================================================================

def data_preprocces_ikman(source_table: str, data_table: str, **kwargs) -> int:
    """
    Preprocess Ikman vehicle data.

    Args:
        source_table: Source table with raw data
        data_table: Target table for processed data

    Returns:
        int: Number of records processed
    """
    with TaskLogger(logger, "data_preprocces_ikman"):
        dataset = read_table(source_table)
        if dataset is None or dataset.empty:
            logger.warning(f"No data found in {source_table}")
            return 0

        initial_count = len(dataset)
        logger.info(f"Loaded {initial_count} records from {source_table}")

        # Filter invalid records
        dataset = dataset[dataset['make'] != '0']

        # Apply transformations
        dataset['model'] = dataset['model'].apply(clean_model_name)
        dataset['vehicle_price'] = dataset['vehicle_price'].apply(extract_price)
        dataset['engine_capacity'] = dataset['engine_capacity'].apply(extract_engine)
        dataset['mileage'] = dataset['mileage'].apply(extract_mileage)
        dataset['posted_date'] = dataset['posted_date'].apply(extract_date)

        # Remove records with missing price
        dataset = dataset.dropna(subset=['vehicle_price'])

        # Normalize text columns
        text_columns = ['model', 'make', 'trim_edition', 'yom', 'transmission', 'body_type', 'fuel_type']
        for col in text_columns:
            if col in dataset.columns:
                if col == 'trim_edition':
                    dataset[col] = dataset[col].fillna('').astype(str).str.upper()
                else:
                    dataset[col] = dataset[col].astype(str).str.upper()

        # Convert numeric columns to string
        for col in ['engine_capacity', 'mileage', 'posted_date']:
            if col in dataset.columns:
                dataset[col] = dataset[col].astype(str)

        dataset['scrape_date'] = datetime.now().strftime('%Y/%m/%d')

        # Combine model with trim edition
        dataset['model'] = np.where(
            (dataset['trim_edition'] != '0') & (dataset['trim_edition'] != ''),
            dataset['model'] + " " + dataset['trim_edition'],
            dataset['model']
        )

        # Select final columns
        final_cols = ['make', 'posted_date', 'scrape_date', 'model', 'yom',
                      'transmission', 'fuel_type', 'engine_capacity', 'vehicle_price']
        dataset = dataset[final_cols]

        # Create and populate table
        create_table(data_table, [
            "make VARCHAR(255)",
            "posted_date VARCHAR(255)",
            "scrape_date VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "engine_capacity VARCHAR(255)",
            "vehicle_price VARCHAR(255)"
        ])

        for _, row in dataset.iterrows():
            populate_table(data_table, row.to_dict())

        final_count = len(dataset)
        logger.info(f"Processed {final_count} records (filtered {initial_count - final_count})")
        return final_count


# ============================================================================
# Riyasewana Data Preprocessing
# ============================================================================

def data_preprocces_riyasewana(source_table: str, data_table: str, **kwargs) -> int:
    """
    Preprocess Riyasewana vehicle data.

    Args:
        source_table: Source table with raw data
        data_table: Target table for processed data

    Returns:
        int: Number of records processed
    """
    with TaskLogger(logger, "data_preprocces_riyasewana"):
        dataset = read_table(source_table)
        if dataset is None or dataset.empty:
            logger.warning(f"No data found in {source_table}")
            return 0

        initial_count = len(dataset)
        logger.info(f"Loaded {initial_count} records from {source_table}")

        # Filter negotiable prices
        dataset = dataset[dataset['price'] != 'Negotiable']

        # Extract numeric price
        dataset['price'] = dataset['price'].apply(extract_price)
        dataset = dataset.dropna(subset=['price'])

        # Normalize text columns
        for col in ['model', 'make', 'transmission', 'fuel_type']:
            if col in dataset.columns:
                dataset[col] = dataset[col].str.upper()

        dataset['posted_date'] = dataset['posted_date'].astype(str)
        dataset['scrape_date'] = datetime.now().strftime('%Y/%m/%d')

        # Select final columns
        final_cols = ['make', 'model', 'posted_date', 'scrape_date', 'mileage',
                      'yom', 'transmission', 'fuel_type', 'engine_capacity', 'price']
        dataset = dataset[final_cols]

        # Create and populate table
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

        for _, row in dataset.iterrows():
            populate_table(data_table, row.to_dict())

        final_count = len(dataset)
        logger.info(f"Processed {final_count} records (filtered {initial_count - final_count})")
        return final_count


# ============================================================================
# Master DB Creation Pipeline Tasks
# ============================================================================

def merge_and_filter_yom(riyasewana_table: str, ikman_table: str,
                          output_table: str, **kwargs) -> int:
    """
    Merge data from both sources and filter by YOM >= 2000.

    Args:
        riyasewana_table: Riyasewana processed data table
        ikman_table: Ikman processed data table
        output_table: Output table for merged data

    Returns:
        int: Number of records in merged dataset
    """
    with TaskLogger(logger, "merge_and_filter_yom"):
        df_riyasewana = read_table(riyasewana_table)
        df_ikman = read_table(ikman_table)

        if df_riyasewana is None:
            df_riyasewana = pd.DataFrame()
        if df_ikman is None:
            df_ikman = pd.DataFrame()

        logger.info(f"Riyasewana records: {len(df_riyasewana)}, Ikman records: {len(df_ikman)}")

        # Normalize price column name
        if 'price' in df_riyasewana.columns:
            df_riyasewana = df_riyasewana.rename(columns={'price': 'vehicle_price'})

        # Add mileage column if missing
        if 'mileage' not in df_ikman.columns and not df_ikman.empty:
            df_ikman['mileage'] = ''

        # Align columns
        common_cols = ['make', 'posted_date', 'scrape_date', 'model', 'yom',
                       'mileage', 'transmission', 'fuel_type', 'engine_capacity', 'vehicle_price']

        for df in [df_riyasewana, df_ikman]:
            if not df.empty:
                df_cols = [c for c in common_cols if c in df.columns]

        df_riyasewana = df_riyasewana[[c for c in common_cols if c in df_riyasewana.columns]] if not df_riyasewana.empty else pd.DataFrame()
        df_ikman = df_ikman[[c for c in common_cols if c in df_ikman.columns]] if not df_ikman.empty else pd.DataFrame()

        # Merge datasets
        dataset = pd.concat([df_riyasewana, df_ikman], ignore_index=True)

        # Filter by YOM
        dataset['yom'] = pd.to_numeric(dataset['yom'], errors='coerce')
        dataset = dataset.dropna(subset=['yom'])
        dataset = dataset[dataset['yom'] >= 2000]
        dataset['yom'] = dataset['yom'].astype(int).astype(str)

        logger.info(f"Merged dataset: {len(dataset)} records after YOM filter")

        # Create and populate table
        create_table(output_table, TABLE_SCHEMAS['master_vehicle'])

        for _, row in dataset.iterrows():
            populate_table(output_table, row.to_dict())

        return len(dataset)


def load_and_clean_data(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 1: Load and clean data (headers and values).

    Args:
        input_table: Input table with raw data
        output_table: Output table for cleaned data

    Returns:
        int: Number of cleaned records
    """
    with TaskLogger(logger, "load_and_clean_data"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        # Clean column headers
        df.columns = df.columns.str.strip().str.lower()
        logger.info("Cleaned column names to lowercase")

        cleaned_grouping_cols = [col.strip().lower() for col in stats_config.grouping_cols]
        cleaned_target_col = stats_config.target_col.strip().lower()

        # Clean data values
        for col in cleaned_grouping_cols:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().str.lower()

        # Ensure target column is numeric
        df[cleaned_target_col] = pd.to_numeric(df[cleaned_target_col], errors='coerce')

        # Drop NaN rows
        df.dropna(subset=cleaned_grouping_cols + [cleaned_target_col], inplace=True)

        logger.info(f"Records after cleaning and NaN removal: {len(df)}")

        # Save to intermediate table
        create_table(output_table, [
            "make VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "vehicle_price FLOAT"
        ])

        df = df[['make', 'model', 'yom', 'transmission', 'fuel_type', 'vehicle_price']]
        for _, row in df.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(df)} cleaned records to {output_table}")
        return len(df)


def apply_iqr_filter(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 2: Apply IQR filtering to remove outliers.

    Args:
        input_table: Input table with cleaned data
        output_table: Output table for filtered data

    Returns:
        int: Number of records after filtering
    """
    with TaskLogger(logger, "apply_iqr_filter"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        cleaned_target_col = stats_config.target_col.strip().lower()
        initial_count = len(df)

        if initial_count > 0:
            q1 = df[cleaned_target_col].quantile(0.25)
            q3 = df[cleaned_target_col].quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - stats_config.iqr_multiplier * iqr
            upper_bound = q3 + stats_config.iqr_multiplier * iqr

            df_filtered = df[
                (df[cleaned_target_col] >= lower_bound) &
                (df[cleaned_target_col] <= upper_bound)
            ].copy()

            records_removed = initial_count - len(df_filtered)

            logger.info(f"IQR Filtering - Q1: {q1:,.2f}, Q3: {q3:,.2f}, IQR: {iqr:,.2f}")
            logger.info(f"Bounds - Lower: {lower_bound:,.2f}, Upper: {upper_bound:,.2f}")
            logger.info(f"Records removed as outliers: {records_removed}")

            df = df_filtered

        # Save to intermediate table
        create_table(output_table, [
            "make VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "vehicle_price FLOAT"
        ])

        for _, row in df.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(df)} records after IQR filtering to {output_table}")
        return len(df)


def group_and_aggregate(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 3: Group data and apply conditional aggregation.

    Args:
        input_table: Input table with filtered data
        output_table: Output table for aggregated data

    Returns:
        int: Number of aggregated groups
    """
    with TaskLogger(logger, "group_and_aggregate"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        if len(df) > 0:
            logger.info("\n--- Applying Price Ceiling Logic (BEFORE aggregation) ---")
            initial_count_pre_ceiling = len(df)
            
            # A. Apply Floor Logic (> 2M)
            floor_mask = df['vehicle_price'] > 2000000
            removed_by_floor = initial_count_pre_ceiling - floor_mask.sum()
            df = df[floor_mask].copy()
            
        
            ceiling_mask = df.apply(check_ceiling_raw, axis=1)
            removed_by_ceiling = len(df) - ceiling_mask.sum()
            df = df[ceiling_mask].copy()
            
            logger.info(f"Records removed (Price < 2,000,000): {removed_by_floor}")
            logger.info(f"Records removed (Year-based Ceilings): {removed_by_ceiling}")
            logger.info(f"Records remaining for aggregation: {len(df)}\n")

        # Check if there are still records after filtering
        if len(df) == 0:
            logger.warning("No records remaining after filtering for aggregation.")
            return None

        cleaned_grouping_cols = [col.strip().lower() for col in stats_config.grouping_cols]
        cleaned_target_col = stats_config.target_col.strip().lower()

        logger.info(f"Grouping by {cleaned_grouping_cols}")

        consolidated_values = df.groupby(cleaned_grouping_cols).agg(
            Record_Count=(cleaned_grouping_cols[0], 'size'),
            **{stats_config.consolidated_col: pd.NamedAgg(
                column=cleaned_target_col,
                aggfunc=conditional_agg
            )}
        ).reset_index()

        consolidated_values['Aggregation_Method'] = np.where(
            consolidated_values['Record_Count'] < stats_config.min_records_for_median,
            'MEAN',
            'MEDIAN'
        )

        logger.info(f"Created {len(consolidated_values)} aggregated groups")

        # Save to intermediate table
        create_table(output_table, [
            "make VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "record_count INT",
            "fixed_value FLOAT",
            "aggregation_method VARCHAR(255)"
        ])

        consolidated_values = consolidated_values.rename(columns={
            'Record_Count': 'record_count',
            'Fixed_value': 'fixed_value',
            'Aggregation_Method': 'aggregation_method'
        })

        for _, row in consolidated_values.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(consolidated_values)} aggregated records to {output_table}")
        return len(consolidated_values)


def apply_text_cleaning(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 4: Apply text cleaning and normalization.

    Args:
        input_table: Input table with aggregated data
        output_table: Output table for cleaned data

    Returns:
        int: Number of records after cleaning
    """
    with TaskLogger(logger, "apply_text_cleaning"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        cleaned_grouping_cols = [col.strip().lower() for col in stats_config.grouping_cols]

        # Clean symbols
        for col in cleaned_grouping_cols:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].str.replace(r'[-/]', ' ', regex=True)
                df[col] = df[col].str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()

        # Clean model redundancy
        logger.info("Cleaning model names: removing makes, symbols, and duplicates")
        df['model'] = df.apply(clean_model_redundancy, axis=1)

        # Convert to uppercase
        cols_to_uppercase = cleaned_grouping_cols + ['aggregation_method']
        for col in cols_to_uppercase:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].str.upper()

        logger.info(f"Text cleaning complete for {len(df)} records")

        # Save to intermediate table
        create_table(output_table, [
            "make VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "record_count INT",
            "fixed_value FLOAT",
            "aggregation_method VARCHAR(255)"
        ])

        for _, row in df.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(df)} text-cleaned records to {output_table}")
        return len(df)


def apply_price_filters(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 5: Apply floor and ceiling price filters.

    Args:
        input_table: Input table with text-cleaned data
        output_table: Output table for filtered data

    Returns:
        int: Number of records after filtering
    """
    with TaskLogger(logger, "apply_price_filters"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        initial_count = len(df)

        # Apply floor filter
        floor_mask = df['fixed_value'] > stats_config.price_floor
        removed_by_floor = initial_count - floor_mask.sum()
        df = df[floor_mask].copy()

        # Apply ceiling filter
        def check_ceiling_filter(row):
            return check_ceiling(row, value_col='fixed_value')

        ceiling_mask = df.apply(check_ceiling_filter, axis=1)
        removed_by_ceiling = len(df) - ceiling_mask.sum()
        df = df[ceiling_mask].copy()

        logger.info(f"Removed by floor (< {stats_config.price_floor:,}): {removed_by_floor}")
        logger.info(f"Removed by YOM-based ceilings: {removed_by_ceiling}")
        logger.info(f"Records remaining: {len(df)}")

        # Save to intermediate table
        create_table(output_table, [
            "make VARCHAR(255)",
            "model VARCHAR(255)",
            "yom VARCHAR(255)",
            "transmission VARCHAR(255)",
            "fuel_type VARCHAR(255)",
            "record_count INT",
            "fixed_value FLOAT",
            "aggregation_method VARCHAR(255)"
        ])

        for _, row in df.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(df)} filtered records to {output_table}")
        return len(df)


def save_summary_statistics(input_table: str, output_table: str, **kwargs) -> int:
    """
    Task 6: Save final results to summary statistics table.

    Args:
        input_table: Input table with final filtered data
        output_table: Output summary table

    Returns:
        int: Number of records saved
    """
    with TaskLogger(logger, "save_summary_statistics"):
        df = read_table(input_table)
        if df is None or df.empty:
            logger.warning(f"No data found in {input_table}")
            return 0

        # Rename and select final columns
        df = df.rename(columns={'fixed_value': 'average_price'})

        # Add updated_date column with current date
        df['updated_date'] = datetime.now().strftime('%Y/%m/%d')

        df = df[['make', 'model', 'yom', 'transmission', 'fuel_type', 'average_price', 'updated_date']]

        # Ensure summary table exists (preserves historical data)
        ensure_table_exists(output_table, TABLE_SCHEMAS['summary_statistics'])

        for _, row in df.iterrows():
            populate_table(output_table, row.to_dict())

        logger.info(f"Saved {len(df)} records to summary table: {output_table}")
        return len(df)


# Backward compatibility wrapper
def add_statical_methods(input_table: str, output_table: str = 'summery_statistics_table', **kwargs) -> int:
    """
    Original monolithic function for backward compatibility.
    Executes all pipeline steps sequentially.
    """
    with TaskLogger(logger, "add_statical_methods"):
        # Intermediate tables
        cleaned_table = 'temp_cleaned_data'
        iqr_filtered_table = 'temp_iqr_filtered'
        aggregated_table = 'temp_aggregated'
        text_cleaned_table = 'temp_text_cleaned'
        price_filtered_table = 'temp_price_filtered'

        load_and_clean_data(input_table, cleaned_table)
        apply_iqr_filter(cleaned_table, iqr_filtered_table)
        group_and_aggregate(iqr_filtered_table, aggregated_table)
        apply_text_cleaning(aggregated_table, text_cleaned_table)
        apply_price_filters(text_cleaned_table, price_filtered_table)
        return save_summary_statistics(price_filtered_table, output_table)
