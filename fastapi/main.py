import os
import sqlite3
from fastapi import FastAPI, Response
from dotenv import load_dotenv
import boto3
import base_model
import basic_func
import pandas as pd
import streamlit as st
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import json
from datetime import datetime, timedelta
import io
from fastapi.responses import StreamingResponse

from basic_func import get_current_user



# # Connect to the database
# conn = sqlite3.connect('researchub.db')
# c = conn.cursor()

# # Define the data for the new row
# new_row_data = ('admin', 'admin', 'admin', 'admin', 'admin', 10000, 'admin')

# # Use an SQL INSERT statement to add the row
# c.execute('INSERT INTO users (fullname, email, username, password, plan, call_count, role) VALUES (?, ?, ?, ?, ?, ?, ?)', new_row_data)

# # Commit the changes to the database
# conn.commit()

# # Close the connection
# conn.close()




app =FastAPI()

load_dotenv()

s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

@app.post("/token", status_code=200, tags=["Authenticate"])
async def login_for_access_token(request: OAuth2PasswordRequestForm = Depends()):
    all_data=basic_func.get_users_data()
    for i in range(len(all_data)):
        if (all_data[i]['username']==request.username):
            my_dict=all_data[i]
    user=my_dict
    # user = basic_func.authenticate_user(data, input.username, input.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not basic_func.verify_password(user['password'], request.password):
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    access_token_expires = timedelta(minutes=basic_func.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = basic_func.create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=base_model.User, tags=["Authenticate"])
async def read_users_me(current_user: base_model.User = Depends(basic_func.get_current_active_user)):
    return current_user


@app.post("/add-user", tags=["CLI"])
async def add_user(username: str, password: str, email: str, full_name: str, plan: str, role: str) -> dict:

    basic_func.add_user(username, password, email, full_name, plan, role)

    return {"user" : "User added"}


@app.post("/check-user-exists", tags=["CLI"])
async def check_user_exists(username: str) -> dict:

    status = basic_func.check_user_exists(username)

    return {"user" : status}


@app.get("/list-filter", tags=["Filters"])
def list_filter(doc_type, subject, language, sort, author_name, keyword,
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    filter_list = basic_func.list_filters(doc_type, subject, language, sort, author_name, keyword)

    return {'filter_list': filter_list }


# @app.post("/endpoint-calls", tags=["Filters"])
# def endpoint_calls(endpoint = 'any', username = 'admin', duration = 'none'):

#     endpoint_calls_count = basic_func.get_endpoint_count_for_username(endpoint, username, duration)
    
#     return {'endpoint_calls_count': endpoint_calls_count }


@app.post("/download-url", tags=["Filters"])
def list_document(selected_doc : str, username = 'user-test',
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Generates the link to download the selected document
    download_link = basic_func.download_document(selected_doc, username)

    return {'download_link': download_link }


@app.post("/summary-generation", tags=["Filters"])
def summary_generation(user_doc_title : str, username = 'user-test',
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    summary = basic_func.generate_summary(user_doc_title, username) 

    return {'summary': summary }


@app.post("/translation-generation", tags=["Filters"])
def translation_generation(filename : str, username : str, translate_to : str,
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    translation = basic_func.generate_translation(filename, username, translate_to)

    return {'translation': translation }


@app.post("/recommendation-generation", tags=["Filters"])
def recommendation_generation(user_doc_title : str, username = 'user-test',
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    recommendation = basic_func.generate_recommendation(user_doc_title, username)

    return {'recommendation': recommendation }


@app.post("/initialize-vec-db", tags=["Filters"])
def initialize_vec_db(get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    basic_func.initialize_vector_db()

    return {'out': 'Done' }


@app.post("/initialize-doc-query-vec-db", tags=["Filters"])
def initialize_doc_query_vec_db(get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    basic_func.initialize_doc_query_vector()

    return {'out': 'Done' }


@app.post("/vector-encoding-smart-doc", tags=["Filters"])
def vector_enc_smart_doc(user_doc_title : str,
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    recommendation = basic_func.vector_encoding_smart_doc(user_doc_title)

    return {'recommendation': recommendation }


@app.post("/doc-query-smart-doc", tags=["Filters"])
def doc_query_smart_doc(user_doc_title : str, username = 'user-test',
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    answer = basic_func.doc_query(user_doc_title, username)

    return {'answer': answer }


@app.post("/check-title-exists", tags=["Filters"])
def check_title_exists(user_doc_title : str,
                       get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    answer = basic_func.check_if_title_exists(user_doc_title)

    return {'answer': answer }

@app.post("/check-users-api-record", tags=["CLI"])
async def check_users_api_record(username: str) -> dict:

    status = basic_func.check_users_api_record(username)

    return {"user" : status}

@app.post("/fetch-titles-from-name", tags=["Filters"])
def fetch_title_name(doc_type, sort, partial_name):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    filter_lists = basic_func.fetch_titles_from_name(doc_type, sort, partial_name)

    return {'filter_lists': filter_lists }
    

@app.post("/update-users-api-record", tags=["CLI"])
def update_users_api_record(url: str, response: str, username: str) -> dict:

    status = basic_func.update_users_api_record(url, response, username)

    return {"user" : status}


@app.post("/update-password", tags=["CLI"])
def update_password(username: str, password: str) -> dict:

    basic_func.update_password(username, password)

    return {"user" : 'status'}


@app.post("/update-plan", tags=["CLI"])
def update_plan(username: str, new_plan: str) -> dict:

    basic_func.update_plan(username, new_plan)

    return {"user" : 'status'}


@app.post("/app-api-record", tags=["CLI"])
def app_api_record():

    bucket_name = "researchub"
    file_name = 'researchub.db'
   

    s3client.download_file(bucket_name, file_name, file_name)
    # s3client.download_file(bucket_name, file_name_2, file_name_2)

    conn = sqlite3.connect(file_name)
    app_api_df = pd.read_sql_query("SELECT * FROM app_api_record", conn)

    # Close database connection and delete local file
    conn.close()

    # Connect to the SQLite database
    # conn = sqlite3.connect('app_api_record.db')

    # Retrieve the data from the database
    # df = pd.read_sql_query("SELECT username, first_call FROM app_api_record", conn)
    # df.head()
    # Convert the DataFrame to a CSV string
    csv_string = app_api_df.to_csv(index=False)

    # Use io.BytesIO to create an in-memory file-like object
    # that can be read by Streamlit
    csv_bytes = io.BytesIO(csv_string.encode())

    # Use the StreamingResponse class to send the file-like object
    # as a streaming response
    
    return StreamingResponse(csv_bytes, media_type='text/csv')


@app.post("/user-api-record", tags=["CLI"])
async def user_api_record() -> dict:


    bucket_name = "researchub"
    file_name = 'researchub.db'
   

    s3client.download_file(bucket_name, file_name, file_name)
    # s3client.download_file(bucket_name, file_name_2, file_name_2)

    conn = sqlite3.connect(file_name)
    users_api_df = pd.read_sql_query("SELECT * FROM users_api_record", conn)

    # Close database connection and delete local file
    conn.close()


    # Connect to the SQLite database
    # conn = sqlite3.connect('user_api_record.db')

    # Retrieve the data from the database
    # df = pd.read_sql_query("SELECT username, first_call FROM user_api_record", conn)

    # Convert the DataFrame to a CSV string
    csv_string = users_api_df.to_csv(index=False)

    # Use io.BytesIO to create an in-memory file-like object
    # that can be read by Streamlit
    csv_bytes = io.BytesIO(csv_string.encode())

    # Use the StreamingResponse class to send the file-like object
    # as a streaming response
    return StreamingResponse(csv_bytes, media_type='text/csv')

@app.get("/fetch-dataframe", tags=["Filters"])
def fetch_dataframes():
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    dataframe = basic_func.fetch_dataframe()

    return {'dataframe': dataframe }