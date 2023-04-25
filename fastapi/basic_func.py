import hashlib
import json
import re
import logging
import sqlite3
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import boto3
import os
import botocore
import time
import requests
import pandas as pd
import csv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import base_model
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import create_engine

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# create a SQLAlchemy engine to connect to the database
database_file_name = "researchub.db"
engine = create_engine('sqlite:///' + database_file_name, echo=True)

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "fa5296715ded673b98da4a16672646ca2184ef4634fdedfeebfad085615b1ddc"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()

final_df = 0

# LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()

# logging.basicConfig(
#     format='%(asctime)s %(levelname)-8s %(message)s',
#     level = LOGLEVEL,
#     datefmt='%Y-%m-%d %H:%M:%S')

#Establish connection to client
s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )


#Establish connection to logs
clientlogs = boto3.client('logs', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )



# Checks if the passed file exists in the specified bucket
def check_if_file_exists_in_s3_bucket(bucket_name, file_name):
    try:
        s3client.head_object(Bucket=bucket_name, Key=file_name)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise


#Generating logs with given message in cloudwatch
def write_logs_researchub(message : str, endpoint : str, username='user-test'):
    log_group_name = "researchub"
    log_stream_name = "endpoint-logs"

    # # Check if log group exists
    # response = clientlogs.describe_log_groups(
    #     logGroupNamePrefix=log_group_name
    # )
    # if not any(log_group['logGroupName'] == log_group_name for log_group in response['logGroups']):
    #     # Create log group if it does not exist
    #     clientlogs.create_log_group(
    #         logGroupName=log_group_name
    #     )

    # # Check if log stream exists
    # response = clientlogs.describe_log_streams(
    #     logGroupName=log_group_name,
    #     logStreamNamePrefix=log_stream_name
    # )
    # if not any(log_stream['logStreamName'] == log_stream_name for log_stream in response['logStreams']):
    #     # Create log stream if it does not exist
    #     clientlogs.create_log_stream(
    #         logGroupName=log_group_name,
    #         logStreamName=log_stream_name
    #     )

    # Write log event to log stream
    log_message = f"[{username}] [{endpoint}] {message}"
    print(log_message)
    clientlogs.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=[
            {
                'timestamp': int(time.time() * 1e3),
                'message': log_message
            }
        ]
    )
    


# Copies the specified file from source bucket to destination bucket 
def copy_to_public_bucket(src_bucket_name, src_object_key, dest_bucket_name, dest_object_key):
    copy_source = {
        'Bucket': src_bucket_name,
        'Key': src_object_key
    }
    s3client.copy_object(Bucket=dest_bucket_name, CopySource=copy_source, Key=dest_object_key)



def get_users_data():
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))

    cursor = db.cursor()
    cursor.execute('''select * from users''')

    # Fetch all the rows as a list of tuples
    rows = cursor.fetchall()

    # Convert the rows to a list of dictionaries
    data = []
    for row in rows:
        # Create a dictionary with keys corresponding to the table column names
        record = {
            "username": row[0],
            "full_name": row[1],
            "email": row[2],
            "password": row[3]
        }
        data.append(record)

    os.remove('researchub.db')

    return data

def verify_password(hashed_password, plain_password):
    return pwd_context.verify(plain_password, hashed_password)

def bcrypt(password: str):
        return pwd_context.hash(password)

def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    my_dict={}
    for i in range(len(db)):
        if (db[i]['username']==username):
            data=get_users_data()
            my_dict=data[i]
    if my_dict:
        return base_model.UserInDB(**my_dict)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = base_model.TokenData(username=username)
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

async def get_current_active_user(current_user: base_model.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def add_user(username, password, email, full_name, plan, role):

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    cursor = db.cursor()
    
    # Hashing the password
    password_hash = pwd_context.hash(password)

    # call_count=0

    if "free" in plan:
        call_count = 10
    elif "gold" in plan:
        call_count = 15
    elif "platinum" in plan:
        call_count = 20

    # Inserting the details into users table
    cursor.execute("INSERT INTO users (username, fullname, password, email, plan, call_count, role) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (username, full_name, password_hash, email, plan, call_count, role))
    
    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')
    os.remove('researchub.db')
    return(f"User {username} created successfully with name {full_name} and subscription tier {plan}.")


# Define function to check if user already exists in database
def check_user_exists(username):

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    result = cursor.fetchone()

    db.close()
    os.remove('researchub.db')
    if bool(result):
        return False
    else:
        return True
    
# Define function to update password in database
def update_password(username, password):

    # Hashing the password
    password_hash = pwd_context.hash(password)

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    c = db.cursor()

    c.execute("UPDATE users SET password=? WHERE username=?", (password_hash, username))

    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')

    os.remove('researchub.db')


# Define function to update password in database
def update_plan(username, new_plan):

    # Connect to database
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    c = db.cursor()

    if "free" in new_plan:
        call_count = 10
    elif "gold" in new_plan:
        call_count = 15
    elif "platinum" in new_plan:
        call_count = 20

    c.execute("UPDATE users SET plan=?, call_count=? WHERE username=?", (new_plan, call_count, username))

    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')

    os.remove('researchub.db')

# Gather all the appropriate options to be listed in the selection box
def list_doc_type():

    with engine.connect() as conn:
        query = conn.execute("SELECT DISTINCT document_type FROM springer;")

    document_types = [row[0] for row in query]
    document_types.insert(0, '-')
    
    return document_types


# Gather all the appropriate subjects to be listed in the selection box
def list_subjects(doc_type):
    with engine.connect() as conn:
        if doc_type == '-':
            query = conn.execute(f"SELECT DISTINCT subject FROM springer;")
        else:
            query = conn.execute(f"SELECT DISTINCT subject FROM springer where document_type = '{doc_type}';")
    distinct_subs = []

    # Separate comma separated subjects and get all the unique subjects present
    for row in query:
        list_of_subs = row[0].split(',')

        for i in range(len(list_of_subs)):
            list_of_subs[i] = list_of_subs[i].lstrip('  ').title()
            if list_of_subs[i] not in distinct_subs:
                distinct_subs.append(list_of_subs[i])

    distinct_subs.insert(0, '-')
    return distinct_subs


# Gather all the appropriate languages to be listed in the selection box
def list_languages(doc_type, subject):
    with engine.connect() as conn:
        if doc_type == '-' and subject == '-':
            query = conn.execute(f"SELECT DISTINCT language FROM springer;")
        elif doc_type == '-':
            query = conn.execute(f"SELECT DISTINCT language FROM springer where subject = '{subject}';")
        elif subject == '-':
            query = conn.execute(f"SELECT DISTINCT language FROM springer where document_type = '{doc_type}';")
        else:
            query = conn.execute(f"SELECT DISTINCT language FROM springer where document_type = '{doc_type}' and subject = '{subject}';")

    languages = [row[0] for row in query]
    languages.insert(0, '-')
    return languages


# Gather all the appropriate documents to be listed in the selection box
def list_documents(doc_type, subject, language, sort_criteria):
    with engine.connect() as conn:
        if doc_type == '-' and subject == '-' and language == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer;")
        elif doc_type == '-' and subject == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where language = '{language}';")
        elif doc_type == '-' and language == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where subject = '{subject}';")
        elif subject == '-' and language == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}';")
        elif doc_type == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where subject = '{subject}' and language = '{language}';")
        elif subject == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and language = '{language}';")
        elif language == '-':
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and subject = '{subject}';")
        else:
            query = conn.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and subject = '{subject}' and language = '{language}';")

    docs_list = [row[0] for row in query]
    # docs_list.insert(0, '-')

    if sort_criteria == 'Ascending':
        docs_list.sort()
    elif sort_criteria == 'Descending':
        docs_list.sort(reverse=True)
        
    return docs_list



# Retrieving the log events for a given username
def get_endpoint_count_for_username(endpoint = 'any', username = 'user-test', duration = 'none'):
    # Declare timeframe based on the given duration
    if duration == 'hour':
        timeframe = 1
    elif duration == 'day':
        timeframe = 24
    elif duration == 'week':
        timeframe = 24*7
    elif duration == 'month':
        timeframe = 24*30
    

    # Define the start and end times for the query
    end_time = int(time.time() * 1000)
    if duration != 'none':
        start_time = end_time - (timeframe * 60 * 60 * 1000) 
    else:
        start_time = 0

    # Query logs to get the number of calls made
    if endpoint != 'any':
        query = f"fields @timestamp, @message | stats count() | filter @message like /{username}/ and @message like /{endpoint}/"
    else:
        query = f"fields @timestamp, @message | stats count() | filter @message like /{username}/"

    response = clientlogs.start_query(
        logGroupName='researchub',
        startTime=start_time,
        endTime=end_time,
        queryString=query,
        limit=10000
    )

    # Get the query id to check status
    query_id = response['queryId']
    status = None

    # Wait till the query is completed
    while status == None or status == 'Running':
        status = clientlogs.get_query_results(
            queryId=query_id
        )['status']
        time.sleep(1)

    # Get the result of the query
    results = clientlogs.get_query_results(queryId=query_id)['results']

    # Return the result if retrieved or return 0
    if len(results) > 0:
        endpoint_count = int(results[0]['value'])
        return endpoint_count
    else:
        return 0
    

# Check whether user has calls
def rate_limiting(username : str):
    calls_made = get_endpoint_count_for_username(username=username, duration='hour')

    # Get the plan's call count from users db
    

    if calls_made < '''call count from users db''':
        return True
    else:
        return False
    

# Clean up
async def conn_close(c):
    c.close()  