"""Streamlit page showing whatever is needed."""
import streamlit as st
from st_utils import add_sidebar, disable_deploy_button
####################
#### STREAMLIT #####
####################


st.set_page_config(
    page_title="RAGGIE",
    page_icon="📌",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("📌 How to use Raggie")

add_sidebar()
disable_deploy_button()
