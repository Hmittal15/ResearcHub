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

from basic_func import get_current_user

app =FastAPI()

load_dotenv()

s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

goes18_bucket = 'noaa-goes18'
user_bucket_name = os.environ.get('USER_BUCKET_NAME')
nexrad_bucket = 'noaa-nexrad-level2'

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
async def add_user(username: str, password: str, email: str, full_name: str, plan: str,
                   get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    basic_func.add_user(username, password, email, full_name, plan)

    return {"user" : "User added"}


@app.post("/check-user-exists", tags=["CLI"])
async def check_user_exists(username: str,
                            get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    status = basic_func.check_user_exists(username)

    return {"user" : status}


@app.get("/list-filter", tags=["Filters"])
def list_filter(doc_type, subject, language, sort, author_name, keyword):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    filter_list = basic_func.list_filters(doc_type, subject, language, sort, author_name, keyword)

    return {'filter_list': filter_list }


@app.post("/endpoint-calls", tags=["Filters"])
def endpoint_calls(endpoint = 'any', username = 'admin', duration = 'none'):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    endpoint_calls_count = basic_func.get_endpoint_count_for_username(endpoint, username, duration)
    
    return {'endpoint_calls_count': endpoint_calls_count }


@app.post("/download-url", tags=["Filters"])
def list_document(selected_doc : str, username = 'user-test'):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Generates the link to download the selected document
    download_link = basic_func.download_document(selected_doc, username)

    return {'download_link': download_link }


@app.post("/summary-generation", tags=["Filters"])
def summary_generation(user_doc_title : str, username = 'user-test'):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    summary = basic_func.generate_summary(user_doc_title, username) 

    return {'summary': summary }


@app.post("/translation-generation", tags=["Filters"])
def translation_generation(filename : str, username : str, translate_to : str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    translation = basic_func.generate_translation(filename, username, translate_to)

    return {'translation': translation }


@app.post("/recommendation-generation", tags=["Filters"])
def recommendation_generation(user_doc_title : str, username = 'user-test'):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    recommendation = basic_func.generate_recommendation(user_doc_title, username)

    return {'recommendation': recommendation }


@app.post("/initialize-vec-db", tags=["Filters"])
def initialize_vec_db():
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    basic_func.initialize_vector_db()

    return {'out': 'Done' }


@app.post("/initialize-doc-query-vec-db", tags=["Filters"])
def initialize_doc_query_vec_db():
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    basic_func.initialize_doc_query_vector()

    return {'out': 'Done' }


@app.post("/vector-encoding-smart-doc", tags=["Filters"])
def vector_enc_smart_doc(user_doc_title : str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    recommendation = basic_func.vector_encoding_smart_doc(user_doc_title)

    return {'recommendation': recommendation }


@app.post("/doc-query-smart-doc", tags=["Filters"])
def doc_query_smart_doc(user_doc_title : str, username = 'user-test'):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    answer = basic_func.doc_query(user_doc_title, username)

    return {'answer': answer }


@app.post("/check-title-exists", tags=["Filters"])
def check_title_exists(user_doc_title : str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Lists the years present in goes database
    answer = basic_func.check_if_title_exists(user_doc_title)

    return {'answer': answer }