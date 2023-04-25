import streamlit as st
from requests.exceptions import HTTPError
import time

st.set_page_config(
    page_title="Researchub",
    page_icon="👋",
)

is_user_logged_in = False

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

# define the Streamlit home page
def homePage():
    st.title("Welcome to NOAA dashboard!")
    st.subheader("Existing user? Please Log-in from the left pane.")
    st.subheader("New user? Please sign-up from the left pane.")
    
def main():
    homePage()

if __name__ == "__main__":
    main()
    st.text(st.session_state["access_token"])