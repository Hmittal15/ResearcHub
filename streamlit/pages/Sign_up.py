
import streamlit as st
import requests



user_bucket_name = 'researchub'
subscription_tiers = ['free', 'gold', 'platinum']
BASE_URL = 'http://localhost:8090'


# Streamlit app
st.title('Sign-up Page')

# Collect user details

username = st.text_input('Username')
email = st.text_input('Email')
fullname = st.text_input('Full Name')
password = st.text_input('Password', type='password')
plan = st.selectbox('Plan Type', ['free', 'gold', 'platinum'])
role = st.selectbox('Role', ['Student', 'Working individual', 'Researcher', 'Others'])

# Handle form submission
if st.button('Sign up'):
    # Make a request to the endpoint to check if the username already exists
    username_response = (requests.post(BASE_URL + f'/check-user-exists?username={username}')).json()
    status = username_response["user"]

    if status:
        # Create user
        requests.post(BASE_URL + f'/add-user?username={username}&password={password}&email={email}&full_name={fullname}&plan={plan}&role={role}')

        st.success(f"User : {username} created successfully with Name : {fullname} and Subscription Plan : {plan}.")

    else:
        st.write("Username already exists.")
        # raise typer.Abort()

