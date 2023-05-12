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
    st.title("Welcome to ResearcHub!")
    st.write("ResearcHub is a one-stop solution for any research enthusiast! We have consolidated all the research papers, journals, book PDFs, all at one place. It also provides several convenience features such as summarization, translation, and recommendations for the user selected documents. The application also allows users to query the document itself for any specific information, instead of skimming through long documents. This project aims to make it easier for users to retrieve and analyze academic documents by providing a range of features to enhance the user's experience and increase the accessibility of the documents.")

    st.subheader("Existing user? Please Log-in from the left pane.")
    st.subheader("New user? Please Sign-up from the left pane.")
    
def main():
    homePage()

if __name__ == "__main__":
    main()
    # st.text(st.session_state["access_token"])