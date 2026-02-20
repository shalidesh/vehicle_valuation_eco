"""
Utility functions for database operations and email notifications.
"""

import psycopg2
from psycopg2 import sql
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import pandas as pd
from airflow.utils.email import send_email

from components.logging_config import get_logger
from components.config import db_config, email_config

logger = get_logger(__name__)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling and cleanup.

    Yields:
        psycopg2.connection: Database connection object
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password
        )
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def check_table(table_name: str) -> bool:
    """
    Check if a table exists and clear its contents if it does.

    Args:
        table_name: Name of the table to check

    Returns:
        bool: True if table existed and was cleared, False otherwise
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table_name,)
            )
            exists = cur.fetchone()[0]

            if exists:
                cur.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table_name)))
                conn.commit()
                logger.info(f"Cleared existing table: {table_name}")
                return True

    return False


def read_table(table_name: str) -> Optional[pd.DataFrame]:
    """
    Read all records from a table into a DataFrame.

    Args:
        table_name: Name of the table to read

    Returns:
        Optional[pd.DataFrame]: DataFrame with table contents or None if table doesn't exist
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table_name,)
            )
            if not cur.fetchone()[0]:
                logger.warning(f"Table '{table_name}' does not exist")
                return None

            cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]

            df = pd.DataFrame(rows, columns=col_names)
            logger.info(f"Read {len(df)} records from table: {table_name}")
            return df


def create_table(table_name: str, columns: List[str]) -> None:
    """
    Create a table if it doesn't exist. Clears existing data if table exists.

    Args:
        table_name: Name of the table to create
        columns: List of column definitions (e.g., ["id INT", "name VARCHAR(255)"])
    """
    check_table(table_name)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', '.join(columns))
                )
                cur.execute(create_sql)
                conn.commit()
                logger.info(f"Created/verified table: {table_name}")

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cur.execute(
                    sql.SQL("DROP TYPE IF EXISTS {} CASCADE").format(sql.Identifier(table_name))
                )
                create_sql = sql.SQL("CREATE TABLE {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', '.join(columns))
                )
                cur.execute(create_sql)
                conn.commit()
                logger.info(f"Recreated table after type conflict: {table_name}")


def ensure_table_exists(table_name: str, columns: List[str]) -> None:
    """
    Create a table if it doesn't exist. Preserves existing data (no deletion).

    Args:
        table_name: Name of the table to create
        columns: List of column definitions (e.g., ["id INT", "name VARCHAR(255)"])
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', '.join(columns))
                )
                cur.execute(create_sql)
                conn.commit()
                logger.info(f"Ensured table exists (data preserved): {table_name}")

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                logger.warning(f"Table {table_name} already exists with different schema")


def populate_table(table_name: str, data: Dict[str, Any]) -> None:
    """
    Insert a single row into a table.

    Args:
        table_name: Name of the target table
        data: Dictionary mapping column names to values
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            columns = list(data.keys())
            values = list(data.values())

            insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(values))
            )

            cur.execute(insert_sql, values)
            conn.commit()


def bulk_insert(table_name: str, df: pd.DataFrame, batch_size: int = 1000) -> int:
    """
    Bulk insert DataFrame records into a table.

    Args:
        table_name: Name of the target table
        df: DataFrame with data to insert
        batch_size: Number of records to insert per batch

    Returns:
        int: Number of records inserted
    """
    if df.empty:
        logger.warning(f"No data to insert into {table_name}")
        return 0

    total_inserted = 0
    columns = list(df.columns)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                records = [tuple(row) for row in batch.values]

                cur.executemany(insert_sql, records)
                conn.commit()
                total_inserted += len(records)

                logger.debug(f"Inserted batch {i // batch_size + 1}: {len(records)} records")

    logger.info(f"Bulk inserted {total_inserted} records into {table_name}")
    return total_inserted


def success_email(context: Dict[str, Any]) -> None:
    """
    Send success notification email.

    Args:
        context: Airflow task context dictionary
    """
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id

    subject = f"[SUCCESS] Airflow Task: {dag_id}.{task_instance.task_id}"
    body = f"""
    <h3>Task Completed Successfully</h3>
    <table>
        <tr><td><b>DAG:</b></td><td>{dag_id}</td></tr>
        <tr><td><b>Task:</b></td><td>{task_instance.task_id}</td></tr>
        <tr><td><b>Execution Date:</b></td><td>{context['execution_date']}</td></tr>
        <tr><td><b>Log URL:</b></td><td><a href="{task_instance.log_url}">{task_instance.log_url}</a></td></tr>
    </table>
    """

    send_email(to=email_config.recipient, subject=subject, html_content=body)
    logger.info(f"Success email sent for task: {task_instance.task_id}")


def failure_email(context: Dict[str, Any]) -> None:
    """
    Send failure notification email.

    Args:
        context: Airflow task context dictionary
    """
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id
    exception = context.get('exception', 'Unknown error')

    subject = f"[FAILED] Airflow Task: {dag_id}.{task_instance.task_id}"
    body = f"""
    <h3 style="color: red;">Task Failed</h3>
    <table>
        <tr><td><b>DAG:</b></td><td>{dag_id}</td></tr>
        <tr><td><b>Task:</b></td><td>{task_instance.task_id}</td></tr>
        <tr><td><b>Execution Date:</b></td><td>{context['execution_date']}</td></tr>
        <tr><td><b>Error:</b></td><td>{exception}</td></tr>
        <tr><td><b>Log URL:</b></td><td><a href="{task_instance.log_url}">{task_instance.log_url}</a></td></tr>
    </table>
    """

    send_email(to=email_config.recipient, subject=subject, html_content=body)
    logger.error(f"Failure email sent for task: {task_instance.task_id}")
