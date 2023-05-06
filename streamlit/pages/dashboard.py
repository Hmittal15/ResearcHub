import requests
import streamlit as st
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd




if 'access_token' not in st.session_state:
    st.session_state.access_token = ''

if 'username' not in st.session_state:
    st.session_state.username = ''

if 'password' not in st.session_state:
    st.session_state.password = ''

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'disable_login' not in st.session_state:
    st.session_state.disable_login = False

if 'disable_logout' not in st.session_state:
    st.session_state.disable_logout = True

username = st.session_state.username

if "access_token" not in st.session_state or st.session_state['access_token']=='':
    st.title("Please sign-in to access this feature!")
else:





    BASE_URL = "http://34.75.99.189/:8090"

    st.markdown("<h1 style='text-align: center;'>ANALYTICS</h1>", unsafe_allow_html=True)
    st.header("")

    dataframe_response = (requests.get(BASE_URL + f'/fetch-dataframe')).json()
    df_users = dataframe_response["dataframe"]["df_users"] 
    df_users = pd.DataFrame.from_dict(df_users, orient='columns')

    df_app_api_record = dataframe_response["dataframe"]["df_app_api_record"] 
    df_app_api_record = pd.DataFrame.from_dict(df_app_api_record, orient='columns')

    df_users_api_record = dataframe_response["dataframe"]["df_users_api_record"]
    df_users_api_record = pd.DataFrame.from_dict(df_users_api_record, orient='columns')
    
    # Concatenate the two tables
    df_combined = pd.concat([df_app_api_record, df_users_api_record],  ignore_index=True)



    if(username!='admin'):

        st.header("")
        plan = df_users_api_record.loc[df_users_api_record['username'] == username, 'plan'].values[0]
        calls_made = df_users_api_record.loc[df_users_api_record['username'] == username, 'total_count'].values[0]
        calls_available = (df_users_api_record.loc[df_users_api_record['username'] == username, 'max_count'].values[0] - calls_made)
  

        col1, col2, col3 = st.columns(3)
        col1.metric("PLAN :", plan)
        col2.metric("CALLS MADE :", calls_made)
        col3.metric("CALLS LEFT :", calls_available)
        st.header("")
        st.header("")

        df_filtered_app = df_app_api_record[df_app_api_record['username'] == username]
        df_filtered_user = df_users_api_record[df_users_api_record['username'] == username]

        # Calculate the total number of success and failure calls
        total_success_calls = (df_filtered_app['success'].sum() + df_filtered_user['success'].sum())
        total_failure_calls = (df_filtered_app['failure'].sum() + df_filtered_user['failure'].sum())

        st.header("Percentage of Success and Failure Calls :")
        st.header("")
        # Create the pie chart using Plotly
        fig = go.Figure(data=[go.Pie(labels=['Success', 'Failure'], values=[total_success_calls, total_failure_calls])])


        # Generate the pie chart and display it
        st.plotly_chart(fig)

        st.header("")





        st.header("")

        st.header("Total Calls by Hour Range :")
        st.header("")
        # Filter the data by username and extract the hour range from the 'first_call' column
        df_filtered = df_combined[df_combined['username'] == username]
        df_filtered['hour_range'] = pd.to_datetime(df_filtered['first_call']).dt.hour

        # Group the data by hour range and count the number of calls
        grouped_data = df_filtered.groupby('hour_range')['total_count'].sum()

        # Reindex the data to include all hour ranges and fill missing values with 0
        grouped_data = grouped_data.reindex(range(24)).fillna(0).reset_index()

        # Create the line graph using Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=grouped_data['hour_range'], y=grouped_data['total_count'], mode='lines+markers'))

        # Set the title and axis labels
        fig.update_layout(xaxis_title='Hour Range', yaxis_title='Total Calls', xaxis_range=[1, 24], yaxis_range=[0, grouped_data['total_count'].max()])

        # Generate the line graph and display it
        st.plotly_chart(fig)

        st.header("")

        st.header("")

        # Filter data for a specific user
        user_data_one_hour = df_users_api_record[df_users_api_record['username'] == username]


        one_hour_download_calls = user_data_one_hour['doc_download'].sum()
        one_hour_summary_calls = user_data_one_hour['summary_generation'].sum()
        one_hour_translation_calls = user_data_one_hour['translation_generation'].sum()
        one_hour_recommendation_calls = user_data_one_hour['recommendation_generation'].sum()
        one_hour_smartdoc_calls = user_data_one_hour['smart_doc'].sum()




        tab1, tab2, tab3, tab4 = st.tabs(["LAST 1 HOUR", "LAST 24 HOURS", "LAST 1 WEEK", "LIFETIME"])

        with tab1:
            st.header("")
            st.header("Calls made in the last 1 hour :")


            y_values = [one_hour_download_calls, one_hour_summary_calls, one_hour_translation_calls, one_hour_recommendation_calls, one_hour_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)






        with tab2:
            st.header("")
            st.header("Calls made in the last 24 hours :")

            
            # Filter data for a specific user
 
            user_data = df_app_api_record[(df_app_api_record['username'] == username) & (pd.to_datetime(df_app_api_record['first_call']) > pd.Timestamp.now() - pd.Timedelta(hours=24))]



            total_download_calls = (user_data['doc_download'].sum() + one_hour_download_calls)
            total_summary_calls = (user_data['summary_generation'].sum() + one_hour_summary_calls)
            total_translation_calls = (user_data['translation_generation'].sum() + one_hour_translation_calls)
            total_recommendation_calls = (user_data['recommendation_generation'].sum() + one_hour_recommendation_calls)
            total_smartdoc_calls = (user_data['smart_doc'].sum() + one_hour_smartdoc_calls)

            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)






        


        with tab3:
            st.header("")
            st.header("Calls made in the last 1 week :")



        
            # Filter data for a specific user

            user_data = df_app_api_record[(df_app_api_record['username'] == username) & (pd.to_datetime(df_app_api_record['first_call']) > pd.Timestamp.now() - pd.Timedelta(hours=168))]


            total_download_calls = (user_data['doc_download'].sum() + one_hour_download_calls)
            total_summary_calls = (user_data['summary_generation'].sum() + one_hour_summary_calls)
            total_translation_calls = (user_data['translation_generation'].sum() + one_hour_translation_calls)
            total_recommendation_calls = (user_data['recommendation_generation'].sum() + one_hour_recommendation_calls)
            total_smartdoc_calls = (user_data['smart_doc'].sum() + one_hour_smartdoc_calls)

            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)





        with tab4:
            st.header("")
            st.header("Calls made over the lifetime :")


            # Filter data for a specific user
    
            user_data = df_app_api_record[df_app_api_record['username'] == username]


            total_download_calls = (user_data['doc_download'].sum() + one_hour_download_calls)
            total_summary_calls = (user_data['summary_generation'].sum() + one_hour_summary_calls)
            total_translation_calls = (user_data['translation_generation'].sum() + one_hour_translation_calls)
            total_recommendation_calls = (user_data['recommendation_generation'].sum() + one_hour_recommendation_calls)
            total_smartdoc_calls = (user_data['smart_doc'].sum() + one_hour_smartdoc_calls)


            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)



    else:
        # admin

        # pie chart based on different plans
        plan_counts = df_users[df_users['plan'] != 'admin']['plan'].value_counts()


        fig = go.Figure(data=[go.Pie(labels=plan_counts.index, values=plan_counts.values)])
        fig.update_layout(title='PERCENTAGE OF USERS BASED ON PLAN TYPE')
        st.plotly_chart(fig)


        # pie chart based on different roles

        role_counts = df_users[df_users['role'] != 'admin']['role'].value_counts()



        fig = go.Figure(data=[go.Pie(labels=role_counts.index, values=role_counts.values)])
        fig.update_layout(title='PERCENTAGE OF USERS BASED ON ROLES')
        st.plotly_chart(fig)

        st.header("")


        # pie chart based on success vs failure calls
    
        # Calculate the total number of success and failure calls
        users_success_calls = (df_app_api_record['success'].sum() + df_app_api_record['success'].sum())
        users_failure_calls = (df_users_api_record['failure'].sum() + df_users_api_record['failure'].sum())

        # Create the pie chart using Plotly
        fig = go.Figure(data=[go.Pie(labels=['Success', 'Failure'], values=[users_success_calls, users_failure_calls])])

        # Set the title
        fig.update_layout(title=f'PERCENTAGE OF SUCCESS VS FAILURE CALLS FOR ALL USERS')

        # Generate the pie chart and display it
        st.plotly_chart(fig)

        st.header("")


        # List of users sorted by total calls made
        st.header("LIST OF USERS SORTED BY TOTAL CALLS MADE:")
        st.header("")
        



        # Group the data by username and sum the total_count_calls
        df_aggregated = df_combined.groupby('username')['total_count'].sum().reset_index()
                
        # Sort the table in descending order of the total_calls_count column
        df_aggregated = df_aggregated.sort_values(by='total_count', ascending=False)

                
        # Rename the columns
        df_aggregated = df_aggregated.rename(columns={'username': 'Username', 'total_count': 'Total Calls Made'})


        # Display the table using Streamlit
        st.dataframe(df_aggregated)


        
        st.header("")
        st.header("")

        st.header("TOTAL CALLS BY HOUR RANGE FOR ALL USERS")


        
        # Line Graph to Group the data by username and hour range, and sum the call counts
        grouped_data = df_combined.groupby(['username', pd.to_datetime(df_combined['first_call']).dt.hour])['total_count'].sum().reset_index()
    


        # Create the line graph using Plotly
        fig = go.Figure()
        for username in grouped_data['username'].unique():
            df_filtered = grouped_data[grouped_data['username'] == username]

            
            fig.add_trace(go.Scatter(x=df_filtered['first_call'], y=df_filtered['total_count'], mode='lines+markers', name=username))

        # Set the title and axis labels
        fig.update_layout(xaxis_title='Hour Range', yaxis_title='Total Calls', xaxis_range=[0,24], yaxis_range=[0, grouped_data['total_count'].max()])

        # Generate the line graph and display it
        st.plotly_chart(fig)

        st.header("")
        st.header("")

        # Total calls based on individual endpoints

        one_hour_total_download_calls = df_users_api_record['doc_download'].sum()
        one_hour_total_summary_calls = df_users_api_record['summary_generation'].sum()
        one_hour_total_translation_calls = df_users_api_record['translation_generation'].sum()
        one_hour_total_recommendation_calls = df_users_api_record['recommendation_generation'].sum()
        one_hour_total_smartdoc_calls = df_users_api_record['smart_doc'].sum()




        tab1, tab2, tab3, tab4 = st.tabs(["LAST 1 HOUR", "LAST 24 HOURS", "LAST 1 WEEK", "LIFETIME"])

        with tab1:
            st.header("")
            st.header("Calls made in the last 1 hour :")


            y_values = [one_hour_total_download_calls, one_hour_total_summary_calls, one_hour_total_translation_calls, one_hour_total_recommendation_calls, one_hour_total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)



        with tab2:
            st.header("")
            st.header("Calls made in the last 24 hours :")

            
            # Filter data for a specific user
 
            user_data = df_app_api_record[(pd.to_datetime(df_app_api_record['first_call']) > pd.Timestamp.now() - pd.Timedelta(hours=24))]



            total_download_calls = (user_data['doc_download'].sum() + one_hour_total_download_calls)
            total_summary_calls = (user_data['summary_generation'].sum() + one_hour_total_summary_calls)
            total_translation_calls = (user_data['translation_generation'].sum() + one_hour_total_translation_calls)
            total_recommendation_calls = (user_data['recommendation_generation'].sum() + one_hour_total_recommendation_calls)
            total_smartdoc_calls = (user_data['smart_doc'].sum() + one_hour_total_smartdoc_calls)

            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)




        with tab3:
            st.header("")
            st.header("Calls made in the last 1 week :")

        
            # Filter data for a specific user

            user_data = df_app_api_record[(pd.to_datetime(df_app_api_record['first_call']) > pd.Timestamp.now() - pd.Timedelta(hours=168))]


            total_download_calls = (user_data['doc_download'].sum() + one_hour_total_download_calls)
            total_summary_calls = (user_data['summary_generation'].sum() + one_hour_total_summary_calls)
            total_translation_calls = (user_data['translation_generation'].sum() + one_hour_total_translation_calls)
            total_recommendation_calls = (user_data['recommendation_generation'].sum() + one_hour_total_recommendation_calls)
            total_smartdoc_calls = (user_data['smart_doc'].sum() + one_hour_total_smartdoc_calls)

            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)


        with tab4:
            st.header("")
            st.header("Calls made over the lifetime :")



            total_download_calls = (df_app_api_record['doc_download'].sum() + one_hour_total_download_calls)
            total_summary_calls = (df_app_api_record['summary_generation'].sum() + one_hour_total_summary_calls)
            total_translation_calls = (df_app_api_record['translation_generation'].sum() + one_hour_total_translation_calls)
            total_recommendation_calls = (df_app_api_record['recommendation_generation'].sum() + one_hour_total_recommendation_calls)
            total_smartdoc_calls = (df_app_api_record['smart_doc'].sum() + one_hour_total_smartdoc_calls)


            y_values = [total_download_calls, total_summary_calls, total_translation_calls, total_recommendation_calls, total_smartdoc_calls]
            # Define the x-axis labels
            x_labels = ['Download_Calls', 'Summarize_Calls', 'Translate_Calls', 'Recommendation_Calls', 'SmartDoc_Calls']



            # Create the bar graph using Plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(x=x_labels, y=y_values))

            # Set the title and axis labels
            fig.update_layout(yaxis_title='Count of Calls')

            # Show the graph
            st.plotly_chart(fig)


