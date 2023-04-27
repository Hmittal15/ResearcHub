
import streamlit as st
import sqlite3
import requests

BASE_URL = 'http://localhost:8090'


tab1, tab2 = st.tabs(["Forgot Password", "Change Plan"])

with tab1:
    st.header("Change Password")
    # Create input fields for username and new password
    username = st.text_input("Username")
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
    username = st.text_input('Enter username')
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
          
