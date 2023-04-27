import streamlit as st
from requests.exceptions import HTTPError
import time
import requests

my_token = st.session_state["access_token"]

def login():

    st.title("Please provide login details!")
    username = st.text_input ("Username", st.session_state.username, placeholder="Username")
    password = st.text_input ("Password", st.session_state.password, placeholder="Password", type='password')

    login_placeholder = st.empty()
    login_button = login_placeholder.button('Login', disabled = st.session_state.disable_login, key='1')

    logout_placeholder = st.empty()
    logout_button = logout_placeholder.button('Logout', disabled = st.session_state.disable_logout, key='3')

    logtxtbox = st.empty()

    if "access_token" not in st.session_state or st.session_state['access_token']=='':
        st.session_state.disable_login = False
        st.session_state.logged_in = False
        st.session_state.disable_logout = True

        logtxtbox = st.empty()

        if login_button:
            st.session_state.username = username
            st.session_state.password = password
            url = "http://localhost:8090/token"
            json_data = {"username": st.session_state.username, "password": st.session_state.password}

            response = requests.post(url, data=json_data, auth=("client_id", "client_secret"))        
            if response.status_code == 200:
                st.success("Logged in as {}".format(username))
                st.session_state["access_token"] = response.json()["access_token"]
                my_token = st.session_state["access_token"]

                st.session_state.disable_login = True
                login_placeholder.button('Login', disabled = st.session_state.disable_login, key='2')
                st.session_state.logged_in = True
                st.session_state.disable_logout = False
                logout_placeholder.button("Logout", disabled=st.session_state.disable_logout, key='4')

            else:
                st.error("Invalid username or password")
                my_token = ''

    else:

        logtxtbox.text("Logged in as {}".format(username))

        st.session_state.disable_login = True
        st.session_state.logged_in = True
        st.session_state.disable_logout = False

        if logout_button:
            st.session_state.disable_login = False
            login_placeholder.button('Login', disabled = st.session_state.disable_login, key='5')
            st.session_state.logged_in = False
            st.session_state.disable_logout = True
            logout_placeholder.button("Logout", disabled=st.session_state.disable_logout, key='6')
            st.session_state.username = ''
            st.session_state.password = ''
            st.session_state["access_token"] = ''
            my_token = st.session_state["access_token"]

            logtxtbox.text("")

    with st.sidebar:
        if "access_token" in st.session_state and st.session_state["access_token"] != '':
            st.write(f'Welcome: {st.session_state.username}')
        else:
            st.write('Guest user')

if __name__=="__main__":
    login()