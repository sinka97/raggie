"""Streamlit utils."""

import streamlit as st

def add_sidebar() -> None:
    with st.sidebar:
        st.text_area('label')