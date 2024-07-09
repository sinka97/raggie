import streamlit as st

from st_utils import (
    add_sidebar,
)

####################
#### STREAMLIT #####
####################


st.set_page_config(
    page_title="RAGGIE",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("🏠 Home Page")
st.info(
    "Welcome to the 🏠 Home Page. "
    "This is a continuing line. "
    "That should appear together.\n\n"
    "This should be in a new line.",
    icon="ℹ️",
)

add_sidebar()
