import psycopg2
import os
import pandas as pd
from datetime import datetime
from airflow.utils.email import send_email
# from dotenv import load_dotenv
# load_dotenv()

# host = os.getenv("HOST")
# port = os.getenv("PORT")
# database = os.getenv("DATABASE")
# user = os.getenv("USER")
# password = os.getenv("PASSWORD")

host = "postgres"
port = "5432"  
database = "airflow_db"
user= "airflow"
password= "airflow"


def check_table(table_name):
    with psycopg2.connect(host=host, port=port, database=database, user=user, password=password) as conn:
        with conn.cursor() as cur:
            # Check if table exists
            cur.execute(f"select * from information_schema.tables where table_name='{table_name}'")
            if bool(cur.rowcount):
                # If table exists, delete all records
                cur.execute(f"delete from {table_name}")

def read_table(table_name):
    with psycopg2.connect(host=host, port=port, database=database, user=user, password=password) as conn:
        with conn.cursor() as cur:
            # Check if the table exists
            cur.execute(f"SELECT * FROM information_schema.tables WHERE table_name='{table_name}'")
            if cur.rowcount > 0:
                # Fetch the records from the table
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                
                # Get column names
                col_names = [desc[0] for desc in cur.description]
                
                # Convert to a DataFrame
                df = pd.DataFrame(rows, columns=col_names)
                
                return df 
    return None
                

# Establish db connection and create table
def create_table(table_name, columns):
    with psycopg2.connect(host=host, port=port, database=database, user=user, password=password) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                create table if not exists {table_name}(
                {','.join(columns)})""")
            

# Insert data into db
def populate_table(table_name, data):
    with psycopg2.connect(host=host, port=port, database=database, user=user, password=password) as conn:
        with conn.cursor() as cur:
            # Extract columns and values from the dictionary
            columns = ", ".join(data.keys())
            values_placeholder = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholder})"
            
            # Execute the query with the dictionary values
            cur.execute(query, tuple(data.values()))

            # Commit the transaction
            conn.commit()



def success_email(context):
    task_instance = context['task_instance']
    task_status = 'Success' 
    subject = f'Airflow Task {task_instance.task_id} {task_status}'
    body = f'The task {task_instance.task_id} completed with status : {task_status}. \n\n'\
        f'The task execution date is: {context["execution_date"]}\n'\
        f'Log url: {task_instance.log_url}\n\n'
    to_email = 'deshanariyarathna@gmail.com' #recepient mail
    send_email(to = to_email, subject = subject, html_content = body)

def failure_email(context):
    task_instance = context['task_instance']
    task_status = 'Failed'
    subject = f'Airflow Task {task_instance.task_id} {task_status}'
    body = f'The task {task_instance.task_id} completed with status : {task_status}. \n\n'\
        f'The task execution date is: {context["execution_date"]}\n'\
        f'Log url: {task_instance.log_url}\n\n'
    to_email = 'deshanariyarathna@gmail.com' #recepient mail
    send_email(to = to_email, subject = subject, html_content = body)

                    