import streamlit as st
import sqlite3
import requests

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

def edit_page(my_token):
    BASE_URL = 'http://34.75.99.189:8090'

    tab1, tab2 = st.tabs(["Forgot Password", "Change Plan"])

    with tab1:
        st.header("Change Password")
        # Create input fields for username and new password
        username = st.session_state.username
        password = st.text_input("New Password", type="password")

        # Create button to update password
        if st.button("Update Password"):
            # Check if username and password fields are not empty
            if username and password:

                # Make a request to the endpoint to check if the username already exists
                username_response = (requests.post(BASE_URL + f'/check-user-exists?username={username}')).json()
                status = username_response["user"]

                if status:
                    st.text(f"User {username} not found in database")
                    
                else:

                    # Call function to update password in database
                    requests.post(BASE_URL + f'/update-password?username={username}&password={password}')
                    st.success("Password updated successfully!")
            else:
                st.error("Please enter both username and new password")
    

    with tab2:
        
        st.header("Change Plan")

        # Get the username and new plan from the user
        username = st.session_state.username
        new_plan = st.selectbox('Select new plan', ['free', 'gold', 'platinum'])
        
        if st.button('Upgrade Plan'):
            if username and new_plan:

                # Make a request to the endpoint to check if the username already exists
                username_response = (requests.post(BASE_URL + f'/check-user-exists?username={username}')).json()
                status = username_response["user"]

                if status:
                    st.text(f"User {username} not found in database")
                    
                else:
                    requests.post(BASE_URL + f'/update-plan?username={username}&new_plan={new_plan}')
                    st.text(f"{username}'s plan has been updated to {new_plan}")
            else:
                st.error("Please enter both username and new plan")
          
if "access_token" not in st.session_state or st.session_state['access_token']=='':
    st.title("Please sign-in to access this feature!")
else:
    edit_page(st.session_state["access_token"])