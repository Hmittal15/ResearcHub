import requests
import streamlit as st
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd




BASE_URL = "http://localhost:8090"

st.markdown("<h1 style='text-align: center;'>ANALYTICS</h1>", unsafe_allow_html=True)
st.header("")

dataframe_response = (requests.get(BASE_URL + f'/fetch-dataframe')).json()
dataframe = dataframe_response["dataframe"] 
df = pd.DataFrame.from_dict(dataframe, orient='columns')






plan_counts = df[df['plan'] != 'admin']['plan'].value_counts()


fig = go.Figure(data=[go.Pie(labels=plan_counts.index, values=plan_counts.values)])
fig.update_layout(title='Count of users by plan type')
st.plotly_chart(fig)




# assume df is the DataFrame containing the user data
role_counts = df[df['role'] != 'admin']['role'].value_counts()



fig = go.Figure(data=[go.Pie(labels=role_counts.index, values=role_counts.values)])
fig.update_layout(title='Count of users by role type')
st.plotly_chart(fig)

download = 'download-url'
summarize = 'summary-generation'
translate = 'translation-generation'
recommend = 'recommendation-generation'
smartdoc = 'doc-query-smart-doc'



endpoints = ['Download', 'Summarize', 'Translate', 'Recommend', 'SmartDoc']




tab1, tab2, tab3, tab4 = st.tabs(["LAST 1 HOUR", "LAST 24 HOURS", "LAST 1 WEEK", "LIFETIME"])

with tab1:
    st.header("Calls made in the last 1 hour :")

    duration = 'hour'


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={download}&username={st.session_state.username}&duration={duration}')).json()
    # download_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={summarize}&username={st.session_state.username}&duration={duration}')).json()
    # summarize_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={translate}&username={st.session_state.username}&duration={duration}')).json()
    # translate_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={recommend}&username={st.session_state.username}&duration={duration}')).json()
    # recommend_count = endpoint_calls_response["endpoint_calls_count"]

    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={smartdoc}&username={st.session_state.username}&duration={duration}')).json()
    # smartdoc_count = endpoint_calls_response["endpoint_calls_count"]


    # call_counts = [download_count, summarize_count, translate_count, recommend_count, smartdoc_count]

    # fig = go.Figure(data=[go.Bar(x=endpoints, y=call_counts)])
    # fig.update_layout(title='Count of requests by endpoint')
    # st.plotly_chart(fig)



with tab2:
    st.header("Calls made in the last 24 hours :")



    duration = 'day'


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={download}&username={st.session_state.username}&duration={duration}')).json()
    # download_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={summarize}&username={st.session_state.username}&duration={duration}')).json()
    # summarize_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={translate}&username={st.session_state.username}&duration={duration}')).json()
    # translate_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={recommend}&username={st.session_state.username}&duration={duration}')).json()
    # recommend_count = endpoint_calls_response["endpoint_calls_count"]

    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={smartdoc}&username={st.session_state.username}&duration={duration}')).json()
    # smartdoc_count = endpoint_calls_response["endpoint_calls_count"]

    # call_counts = [download_count, summarize_count, translate_count, recommend_count, smartdoc_count]

    # fig = go.Figure(data=[go.Bar(x=endpoints, y=call_counts)])
    # fig.update_layout(title='Count of requests by endpoint')
    # st.plotly_chart(fig)

   


with tab3:
    st.header("Calls made in the last 1 week :")



    duration = 'week'


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={download}&username={st.session_state.username}&duration={duration}')).json()
    # download_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={summarize}&username={st.session_state.username}&duration={duration}')).json()
    # summarize_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={translate}&username={st.session_state.username}&duration={duration}')).json()
    # translate_count = endpoint_calls_response["endpoint_calls_count"]


    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={recommend}&username={st.session_state.username}&duration={duration}')).json()
    # recommend_count = endpoint_calls_response["endpoint_calls_count"]

    # endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={smartdoc}&username={st.session_state.username}&duration={duration}')).json()
    # smartdoc_count = endpoint_calls_response["endpoint_calls_count"]


    # call_counts = [download_count, summarize_count, translate_count, recommend_count, smartdoc_count]

    # fig = go.Figure(data=[go.Bar(x=endpoints, y=call_counts)])
    # fig.update_layout(title='Count of requests by endpoint')
    # st.plotly_chart(fig)


with tab4:
    st.header("Calls made over the lifetime :")



    duration = 'none'


endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={download}&username={st.session_state.username}&duration={duration}')).json()
download_count = endpoint_calls_response["endpoint_calls_count"]


endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={summarize}&username={st.session_state.username}&duration={duration}')).json()
summarize_count = endpoint_calls_response["endpoint_calls_count"]


endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={translate}&username={st.session_state.username}&duration={duration}')).json()
translate_count = endpoint_calls_response["endpoint_calls_count"]


endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={recommend}&username={st.session_state.username}&duration={duration}')).json()
recommend_count = endpoint_calls_response["endpoint_calls_count"]

endpoint_calls_response = (requests.post(BASE_URL + f'/endpoint-calls?endpoint={smartdoc}&username={st.session_state.username}&duration={duration}')).json()
smartdoc_count = endpoint_calls_response["endpoint_calls_count"]



call_counts = [download_count, summarize_count, translate_count, recommend_count, smartdoc_count]

fig = go.Figure(data=[go.Bar(x=endpoints, y=call_counts)])
fig.update_layout(title='Count of requests by endpoint')
st.plotly_chart(fig)





# Convert call_time column to datetime and extract hour component
df['first_call'] = pd.to_datetime(df['first_call'])
df['hour'] = df['first_call'].dt.hour

# Create a pivot table with the count of calls for each endpoint and hour
pivot = pd.pivot_table(df, index='hour', values=['download', 'translate', 'summarize'], aggfunc='sum')

# Create a bar chart with separate traces for each endpoint
fig = go.Figure()
for endpoint in pivot.columns:
    fig.add_trace(go.Bar(x=pivot.index, y=pivot[endpoint], name=endpoint))

# Update the layout with title and axis labels
fig.update_layout(title='Number of calls by hour and endpoint',
                  xaxis_title='Hour',
                  yaxis_title='Number of calls')

# Display the chart in Streamlit
st.plotly_chart(fig)


# insert_data_query = '''
# INSERT INTO users (fullname, email, username, password, plan, call_count, role) VALUES 
#     ('pavi', 'pavi@gmail.com', 'pavi', 'pavi', 'Free', 0, 'Others'),
#     ('rachi', 'rachi@gmail.com', 'rachi', 'rachi', 'Gold', 0, 'Others'),
#     ('abi', 'abi@gmail.com', 'abi', 'abi', 'Platinum', 0, 'Working Individual'),
#     ('soni', 'soni@gmail.com', 'soni', 'soni', 'Gold', 0, 'Working Individual'),
#     ('achu', 'achu@gmail.com', 'achu', 'achu', 'Platinum', 0, 'Researcher')
# # '''




# update_row_query = '''
# UPDATE users SET call_count = 10 WHERE plan = 'Free'
# '''

# c.execute(update_row_query)












