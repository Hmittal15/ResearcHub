import requests
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from dotenv import load_dotenv
import boto3
import os
import botocore

st.session_state.username = 'sruthi'
# st.session_state.encode_flag = 0

st.markdown("<h1 style='text-align: center;'>ResearcHub</h1>", unsafe_allow_html=True)
st.header("")

BASE_URL = "http://localhost:8090"

# conn = sqlite3.connect('metadata.db')
# c = conn.cursor()


# # update the value of language for the row with id = 1
# c.execute("UPDATE springer SET document_type = '-', subject = '-', language = '-', url = '-', document_name = '-' WHERE language = 'TEST_LANGUAGE';")
# c.execute("Commit;")

# c.execute("DELETE FROM springer where url = '-';")
# c.execute("Commit;")

tab1, tab2 = st.tabs(["SEARCH BY TITLE", "SEARCH BY OTHER FIELDS"])

# doc_list_response = (requests.get(BASE_URL + '/endpoint-calls')).json()
# doc_type_list = doc_list_response["doc_type_list"]

# st.write (doc_type_list)

if 'encode_flag' not in st.session_state:
    st.session_state.encode_flag=0

if 'doc_type' not in st.session_state:
    st.session_state.doc_type='-'

if 'subject' not in st.session_state:
    st.session_state.subject='-'

if 'language' not in st.session_state:
    st.session_state.language='-'

if 'sort' not in st.session_state:
    st.session_state.sort='-'

if 'author_name' not in st.session_state:
    st.session_state.author_name=''

if 'keyword' not in st.session_state:
    st.session_state.keyword=''


doc_list_response = (requests.get(BASE_URL + f'/list-filter?doc_type={st.session_state.doc_type}&subject={st.session_state.subject}&language={st.session_state.language}&sort={st.session_state.sort}&author_name={st.session_state.author_name}&keyword={st.session_state.keyword}')).json()
distinct_types = doc_list_response["filter_list"]["distinct_types"]

with tab1:

    st.header("SEARCH BY TITLE")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        title_doc_type = st.selectbox(
            'DOCUMENT TYPE:', distinct_types)
        
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
        st.session_state.doc_type = st.selectbox(
            'DOCUMENT TYPE :', distinct_types)

    # subject_list_response = (requests.post(BASE_URL + f'/list-subject?doc_type={doc_type}')).json()
    # subject_list = subject_list_response["subject_list"]

    with col2:

        distinct_subjs = doc_list_response["filter_list"]["distinct_subjs"]
        # List all the unique subjects
        st.session_state.subject = st.selectbox(
            'SUBJECT :', distinct_subjs)

    st.header("")

    col3, col4 = st.columns(2, gap="large")

    # language_list_response = (requests.post(BASE_URL + f'/list-language?doc_type={doc_type}&subject={subject}')).json()
    # language_list = language_list_response["language_list"]

    with col3:

        distinct_langs = doc_list_response["filter_list"]["distinct_langs"]
        st.session_state.language = st.selectbox(
            'LANGUAGE :', distinct_langs)

    
    with col4:
        st.session_state.sort = st.selectbox(
            'SORT BY :', ['-', 'Oldest First', 'Latest First'])


    st.header("")


    col1, col2 = st.columns(2, gap="large")


    with col1:
        st.session_state.author_name = st.text_input('AUTHOR NAME :')
        

    with col2:
        st.session_state.keyword = st.text_input('SEARCH BY KEYWORD :')
        


    st.header("")

    # if sort == 'Ascending':
    #     docs_list.sort()
    # elif sort == 'Descending':
    #     docs_list.sort(reverse=True)

    docs_list = doc_list_response["filter_list"]["docs_list"]
    selected_doc = ''
    selected_doc = st.selectbox("SELECT REQUIRED DOCUMENT", docs_list)






st.header("")

if st.button('DOWNLOAD DOCUMENT'): 
    download_document_response = (requests.post(BASE_URL + f'/download-url?selected_doc={selected_doc}&username={st.session_state.username}')).json()
    download_link = download_document_response["download_link"]
    st.write("Download Document : ", download_link.split("?")[0])

st.header("")
st.header("")

v_endpoint = 'any'
v_username = 'admin'
v_duration = 'none'

# endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={v_endpoint}&username={v_username}&duration={v_duration}')).json()
# endpoint_calls_count = endpoint_calls_response["endpoint_calls_count"]

# st.write(endpoint_calls_count)


tab1, tab2, tab3, tab4 = st.tabs(["SUMMARIZE", "TRANSLATION", "RECOMMENDATION", "SMART DOCS"])

with tab1:
    st.header("Summarize :")
    summary = ''

    if st.button('SUMMARIZE'):  
        if selected_doc != '': 
            summary_generation_response = (requests.post(BASE_URL + f'/summary-generation?user_doc_title={selected_doc}&username={st.session_state.username}')).json()
            summary = summary_generation_response["summary"]
            st.text_area("Summary", summary, height=400)
            
        else:
            st.error('Please select a document')

with tab2:
    st.header("Translation :")
    translate_to = st.selectbox(
        'TRANSLATE TO :', ['es', 'fr', 'it'])

    if st.button('TRANSLATE'):  
        if selected_doc != '': 
            translation_generation_response = (requests.post(BASE_URL + f'/translation-generation?filename={selected_doc}&username={st.session_state.username}&translate_to={translate_to}')).json()
            translation = translation_generation_response["translation"]
            if translation == "False":
                st.error("Unsupported document format. Please refer to the original doc.")
            else:
                st.write(translation)

            
        else:
            st.error('Please select a document')



with tab3:
    st.header("Recommendation :")

    if st.button('RECOMMEND DOCUMENTS'):
        if selected_doc != '':    
            recommendation_generation_response = (requests.post(BASE_URL + f'/recommendation-generation?user_doc_title={selected_doc}&username={st.session_state.username}')).json()
            recommendation = recommendation_generation_response["recommendation"] 
            st.dataframe(pd.DataFrame.from_dict(recommendation, orient='columns'))
            # st.table(pd.DataFrame.from_dict(recommendation, orient='columns'))
            # st.dataframe(recommendation)
            
        else:
            st.error('Please select a document')

with tab4:
    st.header("Smart Docs :")
    smart_doc_name = st.text_input('SMART DOC NAME :')
    
    
    if st.button('ENCODE DOCUMENT'):
        title_exists_response = (requests.post(BASE_URL + f'/check-title-exists?user_doc_title={smart_doc_name}')).json()
        title_exists = title_exists_response['answer']

        if title_exists:
            doc_encoding_response = (requests.post(BASE_URL + f'/vector-encoding-smart-doc?user_doc_title={smart_doc_name}&username={st.session_state.username}')).json()
            st.success("Document successfully encoded")
            st.session_state.encode_flag = 1
            
            
        else:
            st.error('Please provide the correct document name.')

    smart_doc_query = st.text_input('QUERY :')
    if st.button('QUERY DOCUMENT'):
        if st.session_state.encode_flag == 1:
            if smart_doc_query != '':               
                doc_query_response = (requests.post(BASE_URL + f'/doc-query-smart-doc?user_doc_title={smart_doc_query}&username={st.session_state.username}')).json()
                doc_query = doc_query_response['answer']
                st.write(doc_query)
            else:
                st.error("Please enter a query.")
        else:
            st.error("Please encode the document first")

        






