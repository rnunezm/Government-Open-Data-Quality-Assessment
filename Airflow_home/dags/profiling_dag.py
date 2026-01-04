import os
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

# Añadir raíz al PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),"../../"))
sys.path.insert(0, PROJECT_ROOT)

from scripts.ingest import process_latest

default_args = {
    "owner":"ruben",
    "start_date": datetime(2024,1,1),
    "retries":0
}

with DAG(
    dag_id="data_profiling",
    schedule=None,
    default_args=default_args,
    catchup=False
) as dag:

    #run_profiling = PythonOperator(
     #   task_id="run_profile",
      #  python_callable=process_latest
    #)

     # --- Inicio y fin simbólicos ---
    start = DummyOperator(task_id="start")
    end = DummyOperator(task_id="end")

    # --- Paso 1: Perfilado de datos ---
    profiling_task = PythonOperator(
        task_id="run_profile",
        python_callable=process_latest
    )

    # --- Paso 2: Validación de datos (Dummy) ---
    validate_task = DummyOperator(task_id="validate_data")

    # --- Paso 3: Notificación final (Dummy) ---
    notify_task = DummyOperator(task_id="notify_completion")

    # --- Definir dependencias ---
    start >> profiling_task >> validate_task >> notify_task >> end