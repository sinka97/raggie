"""Streamlit utils."""

import streamlit as st
import pandas as pd
from rag_utils import load_excel

def add_sidebar() -> None:
    with st.sidebar:
        st.text_area('label')

def main_page_sidebar():
    with st.sidebar:
        # File uploader widget
        uploaded_file = st.file_uploader("Embed A Document")

        if uploaded_file is not None:
            # Display file details
            st.write(f"Filename: {uploaded_file.name}")
            st.write(f"File type: {uploaded_file.type}")
            st.write(f"File size: {uploaded_file.size} bytes")

            # Read and display the file content
            if uploaded_file.type == "text/csv":
                sheet_name = st.text_input("Enter the sheet name")
                if st.button("Start Embedding"):
                    # dfs = load_excel(uploaded_file,sheet_name)
                    df = pd.read_csv(uploaded_file)
                    dfs = [df]
                    st.write("Data preview:")
                    st.write(dfs[0].head())
            elif uploaded_file.type == "image/png" or uploaded_file.type == "image/jpeg":
                from PIL import Image
                image = Image.open(uploaded_file)
                st.image(image, caption='Uploaded Image.', use_column_width=True)
            else:
                st.write("Unsupported file type")

def disable_deploy_button():
    st.markdown(
    r"""
    <style>
    .stDeployButton {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True
    )
