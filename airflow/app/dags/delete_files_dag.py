import boto3
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
from airflow.models import Variable




load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
USER_BUCKET_NAME = Variable.get('USER_BUCKET_NAME')


s3client = boto3.client(
    's3',
    aws_access_key_id=Variable.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=Variable.get('AWS_SECRET_KEY')

)


s3 = boto3.resource('s3', 
                    region_name = 'us-east-1',
                    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                    aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
)



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 22),
    'retries': 0
}



dag = DAG('delete_files_dag',
          default_args=default_args,
          schedule_interval='0 1 * * *',
          catchup=False
          )



def delete_files_from_s3():
    response_docs = s3client.list_objects_v2(Bucket='researchub', Prefix='documents/')
    for obj in response_docs['Contents'][1:]:
        s3client.delete_objects(Bucket='researchub', Delete={'Objects': [{'Key': obj['Key']}]})


with dag:

    delete = PythonOperator(
        task_id='delete_files_from_s3',
        python_callable=delete_files_from_s3,
        dag=dag
    )


