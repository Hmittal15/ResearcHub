import boto3
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
from airflow.models import Variable
import requests
import re

import sqlite3
import json
import csv
import pandas as pd
from sqlalchemy import create_engine
import pinecone
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import OnlinePDFLoader



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



dag = DAG('researchub_dag',
          default_args=default_args,
          schedule_interval='0 5 * * *',
          catchup=False
          )





def subject_records(**context):    
    subs = ['\"Computational Intelligence\"','Mathematics','Physics','\"Computer Science\"','Nanotechnology','Engineering','Energy',
           '\"Earth Sciences\"','Geography','History','\"Health Informatics\"','\"Artificial Intelligence\"',
           '\"Pattern Recognition\"','\"Data Engineering\"','Immunology']
    sub_records = {key:{} for key in subs}
    # fetching articles for each subject 
    for k,v in sub_records.items():
        sub_records[k]['articles']=[]
        count = 1
        response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Journal', s=1, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
        total = response['result'][0]['total']
        total = int(total)
        count = 1
        while (count<=total and len(sub_records[k]['articles'])<10):
            print((count<=total and len(sub_records[k]['articles'])<10))
            print(len(sub_records[k]['articles']))
            response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Journal', s=count, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
            records = response['records']
            for record in records:
                if len(sub_records[k]['articles'])>=10:
                    break
                test = record['url'][1]['value']
                print(test)
                if requests.get(test):
                    print(requests.get(test))
                    sub_records[k]['articles'].append(record)

            count+=100
    # fetching ConferencePaper for each subject
    for k,v in sub_records.items():
        print(k)
        sub_records[k]['ConferencePapers']=[]
        count = 1
        response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Book', s=1, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
        total = response['result'][0]['total']
        total = int(total)
        count = 1
        while (count<=total and len(sub_records[k]['ConferencePapers'])<10):
            print((count<=total and len(sub_records[k]['ConferencePapers'])<10))
            print(len(sub_records[k]['ConferencePapers']))
            response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Book', s=count, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
            records = response['records']
            for record in records:
                if len(sub_records[k]['ConferencePapers'])>=10:
                    break
                if record['contentType'] == 'Chapter ConferencePaper':
                    print("Chapter ConferencePaper")
                    test = record['url'][1]['value']
                    print(test)
                    if requests.get(test):
                        print(requests.get(test))
                        sub_records[k]['ConferencePapers'].append(record)
            count+=100
            
    # fetching Books for each subject
    for k,v in sub_records.items():
        print(k)
        pub_name=[]
        sub_records[k]['Books']=[]
        count = 1
        response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Book', s=1, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
        total = response['result'][0]['total']
        total = int(total)
        count = 1
        while (count<=total and len(sub_records[k]['Books'])<10):
            print((count<=total and len(sub_records[k]['Books'])<10))
            print(len(sub_records[k]['Books']))
            response = requests.get('http://api.springernature.com/meta/v2/json?q=(subject:{subject} AND type:{tp} AND openaccess:true)&p=100&s={s}&api_key={api_key}'.format(subject=k, tp = 'Book', s=count, api_key='495c83e9c1f32a78c3ef25bd2d14127d')).json()
            records = response['records']
            for record in records:
                if len(sub_records[k]['Books'])>=10:
                    break
                if record['contentType'] == 'Chapter':
                    print("Chapter")
                    test = record['url'][1]['value']
                    print(test)
                    test = re.sub(r"_[^_]*$", "", test)
                    print(test)
                    if record["publicationName"] not in pub_name:
                        print(record["publicationName"])
                        if requests.get(test):
                            print(requests.get(test))
                            sub_records[k]['Books'].append(record)
                            pub_name.append(record["publicationName"])
            count+=100    

    context['ti'].xcom_push(key='sub_records', value=sub_records)
    return sub_records


def populate_table_and_csv(**context):
    
    sub_records = context['ti'].xcom_pull(key='sub_records')

    #download db file from s3
    s3client.download_file('researchub', 'researchub.db', 'researchub.db')

    #--creation of the table SPRINGER--
    #Connecting to sqlite
    conn = sqlite3.connect('researchub.db')
    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    #Doping EMPLOYEE table if already exists.
    cursor.execute("DROP TABLE IF EXISTS springer_metadata")
    #Creating table as per requirement
    sql ='''CREATE TABLE springer_metadata(
       CATEGORY CHAR(1000) NOT NULL,
       TYPE CHAR(1000) NOT NULL,
       TITLE CHAR(1000) NOT NULL,
       LANGUAGE CHAR(1000) NOT NULL,
       DATE CHAR(1000) NOT NULL,
       ID CHAR(1000) NOT NULL,
       AUTHORS CHAR(1000) NOT NULL,
       DOC_URL CHAR(1000) NOT NULL,
       ABSTRACT CHAR(1000),
       KEYWORDS CHAR(1000)
    )'''
    cursor.execute(sql)
    
    #--Inserting data for ConferencePapers--
    #Connecting to sqlite
    conn = sqlite3.connect('researchub.db')
    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    #query
    sql = '''INSERT INTO springer_metadata(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS)
    VALUES(?,?,?,?,?,?,?,?,?,?);'''
    #storing metada data for conference papers
    for k,v in sub_records.items():
        records = sub_records[k]['ConferencePapers']
        if '"' in k:
            k = k.replace('"','')
        for record in records:
            CATEGORY = k
            TYPE = 'ConferencePapers'
            TITLE = record['title']
            LANGUAGE = record['language']
            DATE = record['publicationDate']
            ID = record['identifier']
            AUTHORS = [creator['creator'] for creator in record['creators']] 
            AUTHORS = json.dumps(AUTHORS)
            DOC_URL = record['url'][1]['value']
            ABSTRACT = record['abstract']
            if 'keyword' in record:
                KEYWORDS = record['keyword']
                KEYWORDS = json.dumps(KEYWORDS)

            else:
                KEYWORDS=''
            cursor.execute(sql,(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS))

    # Commit your changes in the database
    conn.commit()

    #Closing the connection
    conn.close()
    
    #--inserting data for articles--
    #Connecting to sqlite
    conn = sqlite3.connect('researchub.db')
    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    #query
    sql = '''INSERT INTO springer_metadata(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS)
    VALUES(?,?,?,?,?,?,?,?,?,?);'''
    #storing metada data for conference papers
    for k,v in sub_records.items():
        records = sub_records[k]['articles']
        if '"' in k:
            k = k.replace('"','')
        for record in records:
            CATEGORY = k
            TYPE = 'Article'
            TITLE = record['title']
            LANGUAGE = record['language']
            DATE = record['publicationDate']
            ID = record['identifier']
            AUTHORS = [creator['creator'] for creator in record['creators']] 
            AUTHORS = json.dumps(AUTHORS)
            DOC_URL = record['url'][1]['value']
            ABSTRACT = record['abstract']
            if 'keyword' in record:
                KEYWORDS = record['keyword']
                KEYWORDS = json.dumps(KEYWORDS)

            else:
                KEYWORDS=''
            cursor.execute(sql,(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS))

    # Commit your changes in the database
    conn.commit()

    #Closing the connection
    conn.close()

    #inserting data for Books

    #Connecting to sqlite
    conn = sqlite3.connect('researchub.db')
    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    #query
    sql = '''INSERT INTO springer_metadata(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS)
    VALUES(?,?,?,?,?,?,?,?,?,?);'''
    #storing metada data for conference papers
    for k,v in sub_records.items():
        records = sub_records[k]['Books']
        if '"' in k:
            k = k.replace('"','')
        for record in records:
            CATEGORY = k
            TYPE = 'Book'
            TITLE = record['title']
            LANGUAGE = record['language']
            DATE = record['publicationDate']
            ID = record['identifier']
            AUTHORS = [creator['creator'] for creator in record['creators']] 
            AUTHORS = json.dumps(AUTHORS)
            DOC_URL = record['url'][1]['value']
            DOC_URL = re.sub(r"_[^_]*$", "", DOC_URL)
            ABSTRACT = record['abstract']
            if 'keyword' in record:
                KEYWORDS = record['keyword']
                KEYWORDS = json.dumps(KEYWORDS)

            else:
                KEYWORDS=''
            cursor.execute(sql,(CATEGORY,TYPE,TITLE,LANGUAGE,DATE,ID,AUTHORS,DOC_URL,ABSTRACT,KEYWORDS))

    # Commit your changes in the database
    conn.commit()

    #Closing the connection
    conn.close()
    
    print("creating csv")
    #--Converting to csv--
    # Connect to the database
    conn = sqlite3.connect('researchub.db')

    # Create a cursor object
    cursor = conn.cursor()

    # Execute a SELECT query
    cursor.execute('SELECT * FROM springer_metadata')

    # Fetch all rows of the query result
    rows = cursor.fetchall()
    
    # Open a CSV file for writing
    with open('springer_metadata.csv', 'w', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)

        # Write the header row
        writer.writerow([description[0] for description in cursor.description])

        # Write the data rows
        for row in rows:
            writer.writerow(row)

    # Close the database connection
    conn.close()
    print("uploading_db to s3")
    s3client.upload_file('researchub.db','researchub','researchub.db')
    print("uploading_csv to s3")
    object_key = 'data' + '/' + 'springer_metadata.csv'

    s3client.upload_file('springer_metadata.csv','greatexpectations',object_key)




# This process will be automated through DAG to upsert new records in vector database on daily basis
def vector_encoding():
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    user_bucket = Variable.get('USER_BUCKET_NAME')

    table_name="springer_metadata"
    db_name="researchub.db"
    db_engine=create_engine("sqlite:///" + db_name)

    s3client.download_file(user_bucket, db_name, db_name)
    df = pd.read_sql_table(table_name, con=db_engine)

    pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))
    index_name="doc-recommend"
    index = pinecone.Index(index_name)

    embedding_list = []
    counter = 0
    for i, row in df.iterrows():
        try:
            loader = OnlinePDFLoader(row['DOC_URL'])
            data = loader.load()
            embedding_list.append((
                re.sub('[^A-Za-z0-9]+', '', row['TITLE']),
                model.encode(str(data) + "Following is the abstract for this document. " + row['ABSTRACT'] + "Following are the crucial keywords which are described in this document. " + row['KEYWORDS']).tolist(),
                {'title': row['TITLE']}
            ))
        # if len(embedding_list)==50 or len(embedding_list)==len(df):
            index.upsert(vectors=embedding_list)
            embedding_list = []
        except:
            exception_row = row['TITLE']
            with db_engine.connect() as conn:
                conn.execute(f'DELETE FROM {table_name} where TITLE = "{exception_row}"')
            counter += 1
            print(exception_row)
            continue
    if counter !=0 :
        s3client.upload_file('researchub.db', user_bucket, 'researchub.db')        
    os.remove(db_name)


with dag:

    subject = PythonOperator(
        task_id='subject_records',
        python_callable=subject_records,
        dag=dag
    )

    populate = PythonOperator(
        task_id='populate_table_and_csv',
        python_callable=populate_table_and_csv,
        dag=dag
    )


    vector = PythonOperator(
        task_id='vector_encoding',
        python_callable=vector_encoding,
        dag=dag
    )

  


subject >> populate
populate >> vector
