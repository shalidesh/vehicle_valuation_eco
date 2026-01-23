from airflow import DAG
from datetime import datetime, timedelta
from airflow.utils.email import send_email
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from components.post_links_extraction import scrape_links_ikman
from components.utils import success_email,failure_email
from components.post_data_extraction import scarpe_and_save_ikman
from components.data_preprocces import data_preprocces_ikman


default_args = {
    'owner': 'shalika_Deshan',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 2),
    'schedule_interval' : 'None',
    'email_on_failure': True,
    'email_on_success': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}

dag = DAG(
    dag_id="Vehicle_Data_scrape_Pipeline_Ikman_v02",
    default_args=default_args,
    schedule_interval="@daily"
)

scrape_post_links = PythonOperator(
    task_id='scrape_post_links_ikman',
    python_callable=scrape_links_ikman,
    on_success_callback = success_email,
    on_failure_callback = failure_email,
    provide_context = True,
    dag=dag,
)

scrape_vehicle_info_from_link = PythonOperator(
    task_id='scrape_vehicle_info_from_link_ikman',
    python_callable=scarpe_and_save_ikman,
    op_kwargs={'source_table': 'ikman_vehicle_post_links','data_table': 'ikman_post_data'}, 
    on_success_callback = success_email,
    on_failure_callback = failure_email,
    provide_context = True,
    dag=dag,
)

preprocess_data = PythonOperator(
    task_id='data_proprocessing_ikman',
    python_callable=data_preprocces_ikman,
    op_kwargs={'source_table': 'ikman_post_data','data_table': 'ikman_post_data_preprocced'}, 
    on_success_callback = success_email,
    on_failure_callback = failure_email,
    provide_context = True,
    dag=dag,
)

#Set the order of tasks
scrape_vehicle_info_from_link.set_upstream(scrape_post_links)
preprocess_data.set_upstream(scrape_vehicle_info_from_link)




