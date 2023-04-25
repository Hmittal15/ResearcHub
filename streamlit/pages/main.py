import requests
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from dotenv import load_dotenv
import boto3
import os
import botocore



st.markdown("<h1 style='text-align: center;'>ResearcHub</h1>", unsafe_allow_html=True)
st.header("")

BASE_URL = "http://localhost:8090"


def researchub(my_token):

    # # update the value of language for the row with id = 1
    # c.execute("UPDATE springer SET document_type = '-', subject = '-', language = '-', url = '-', document_name = '-' WHERE language = 'TEST_LANGUAGE';")
    # c.execute("Commit;")

    # c.execute("DELETE FROM springer where url = '-';")
    # c.execute("Commit;")

    headers = {"Authorization": f"Bearer {my_token}"}

    tab1, tab2 = st.tabs(["SEARCH BY TITLE", "SEARCH BY OTHER FIELDS"])

    doc_list_response = (requests.get(BASE_URL + '/list-document-type', headers=headers)).json()
    doc_type_list = doc_list_response["doc_type_list"]

    with tab1:

        st.header("SEARCH BY TITLE")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            title_doc_type = st.selectbox(
                'DOCUMENT TYPE:', doc_type_list)
            
        with col2:

            title_sort = st.selectbox(
                'SORT BY:', ['-', 'Ascending', 'Descending'])

        st.header("")
        doc_name = st.text_input('DOCUMENT NAME :')




    with tab2:

        st.header("SEARCH BY OTHER FIELDS")


        col1, col2 = st.columns(2, gap="large")
        

        with col1:
            # List all the document types
            doc_type = st.selectbox(
                'DOCUMENT TYPE :', doc_type_list)

        subject_list_response = (requests.get(BASE_URL + '/list-subject', headers=headers)).json()
        subject_list = subject_list_response["subject_list"]

        with col2:
            # List all the unique subjects
            subject = st.selectbox(
                'SUBJECT :', subject_list)

        st.header("")

        col3, col4 = st.columns(2, gap="large")

        language_list_response = (requests.get(BASE_URL + '/list-language', headers=headers)).json()
        language_list = language_list_response["language_list"]

        with col3:

            language = st.selectbox(
                'LANGUAGE :', language_list)

        
        with col4:
            sort = st.selectbox(
                'SORT BY :', ['-', 'Ascending', 'Descending'])


        st.header("")


        col1, col2 = st.columns(2, gap="large")


        with col1:
            author_name = st.text_input('AUTHOR NAME :')
            #

        with col2:
            keyword = st.text_input('SEARCH BY KEYWORD :')
            #


        st.header("")

        if doc_type == '-' and subject == '-' and language == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer;")
        elif doc_type == '-' and subject == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where language = '{language}';")
        elif doc_type == '-' and language == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where subject = '{subject}';")
        elif subject == '-' and language == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}';")
        elif doc_type == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where subject = '{subject}' and language = '{language}';")
        elif subject == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and language = '{language}';")
        elif language == '-':
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and subject = '{subject}';")
        else:
            query = c.execute(f"SELECT DISTINCT document_name FROM springer where document_type = '{doc_type}' and subject = '{subject}' and language = '{language}';")

        docs_list = [row[0] for row in query]
        # docs_list.insert(0, '-')

        if sort == 'Ascending':
            docs_list.sort()
        elif sort == 'Descending':
            docs_list.sort(reverse=True)

        selected_doc = st.selectbox("SELECT REQUIRED DOCUMENT", docs_list)






    st.header("")

    if st.button('DOWNLOAD DOCUMENT'): 
        query = c.execute(f"SELECT DISTINCT url FROM springer where document_name = '{selected_doc}';")
        selected_url = [row[0] for row in query]
        st.write(selected_url[0])   
        # st.write('Download Link : ', download_link.split("?")[0])


    st.header("")
    st.header("")





    tab1, tab2, tab3, tab4 = st.tabs(["SUMMARIZE", "TRANSLATION", "RECOMMENDATION", "REFERENCE VIDEOS"])

    with tab1:
        st.header("Summarize :")
        summarize = st.text_area("Enter some text", "", height = 400)

        if st.button('SUMMARIZE'):   
            st.write("hi")  
            # st.write('Download Link : ', download_link.split("?")[0])
    
    with tab2:
        st.header("Translation :")
        translate_to = st.selectbox(
            'TRANSLATE TO :', 'hello')
        #     (station_list))
        translate = st.text_area("Enter some text2", "", height = 400)

        if st.button('TRANSLATE'):  
            st.write("hi")   
            # st.write('Download Link : ', download_link.split("?")[0])
    


    with tab3:
        st.header("Recommendation :")
        recommend = st.text_area("Enter some text3", "", height = 400)

        if st.button('RECOMMEND DOCUMENTS'):    
            st.write("hi") 
            # st.write('Download Link : ', download_link.split("?")[0])

    with tab4:
        st.header("Reference Videos :")
        ref_videos = st.text_area("Enter some text4", "", height = 400)
        if st.button('RECOMMEND VIDEOS'):
            st.write("hi") 
            # st.write('Download Link : ', download_link.split("?")[0])


if "access_token" not in st.session_state or st.session_state['access_token']=='':
    st.title("Please sign-in to access this feature!")
else:
    researchub(st.session_state["access_token"])