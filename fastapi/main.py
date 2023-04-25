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

    output = basic_func.add_user(username, password, email, full_name, plan, role)

    return {"user" : output}


@app.post("/check-user-exists", tags=["CLI"])
async def check_user_exists(username: str) -> dict:

    status = basic_func.check_user_exists(username)

    return {"user" : status}


@app.get("/list-document-type", tags=["Filters"])
def list_document_type():
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Establishes a connection to the goes database
    # c = basic_func.conn_metadata()

    # Lists the years present in goes database
    doc_type_list = basic_func.list_doc_type()

    # Clean up
    # basic_func.conn_close(c)

    basic_func.write_logs_researchub(message='listed doc types', endpoint='list_doc_type')


    return {'doc_type_list': doc_type_list }


@app.get("/endpoint-calls", tags=["Filters"])
def endpoint_calls():
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # # Establishes a connection to the goes database
    # c = basic_func.conn_metadata()

    # # Lists the years present in goes database
    # doc_type_list = basic_func.list_doc_type(c)

    # # Clean up
    # basic_func.conn_close(c)

    # basic_func.write_logs_researchub(message='listed doc types', endpoint='list_doc_type')

    doc_type_list = basic_func.get_endpoint_count_for_username()
    

    return {'doc_type_list': doc_type_list }


@app.post("/list-subject", tags=["Filters"])
def list_subject(doc_type:str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Establishes a connection to the goes database
    c = basic_func.conn_metadata()

    # Lists the years present in goes database
    subject_list = basic_func.list_subjects(c, doc_type)

    # Clean up
    basic_func.conn_close(c)

    return {'subject_list': subject_list }


@app.post("/list-language", tags=["Filters"])
def list_language(doc_type:str, subject:str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Establishes a connection to the goes database
    c = basic_func.conn_metadata()

    # Lists the years present in goes database
    language_list = basic_func.list_languages(c, doc_type, subject)

    # Clean up
    basic_func.conn_close(c)

    return {'language_list': language_list }


@app.post("/list-document", tags=["Filters"])
def list_document(doc_type:str, subject:str, sort_criteria:str):
    # get_current_user: base_model.User = Depends(get_current_user)) -> dict:

    # Establishes a connection to the goes database
    c = basic_func.conn_metadata()

    # Lists the years present in goes database
    document_list = basic_func.list_documents(c, doc_type, subject, sort_criteria)

    # Clean up
    basic_func.conn_close(c)

    return {'document_list': document_list }