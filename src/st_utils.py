"""Streamlit utils."""
import uuid

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from rag_utils import upload_excel, embed_and_store_document, get_embedding_model

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

def main_page_sidebar():
    with st.sidebar:
        if "chromadb_ip" not in st.session_state or st.session_state.chromadb_ip == "":
            st.warning("ChromaDB not connected. Navigate to ⚙️ Config to connect.")
        else:
            chromadb_ip = st.session_state["chromadb_ip"]
            st.info(f"Connected to {st.session_state.chromadb_ip}.")
        # File uploader widget
        uploaded_file = st.file_uploader("Embed A Document", type=["xlsx","pdf","html"])

        if uploaded_file is not None:
            # Read and display the file content
            if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                with st.form('excel_upload'):
                    sheet_name = st.text_input("Enter sheet name")
                    submit_sheet_name = st.form_submit_button()
                    if submit_sheet_name:
                        dfs = upload_excel(uploaded_file,sheet_name)
                        st.write("Data preview:")
                        st.write(dfs[0].head())
                        st.session_state.dfs = dfs
            elif uploaded_file.type == "application/pdf":
                pdf_viewer(uploaded_file.getvalue(),width=250,height=350)
                with st.form('pdf_upload'):
                    col_name = st.text_input("Enter Collection Name")
                    submit_col_name = st.form_submit_button()
                    if submit_col_name:
                        st.write("Embedding PDF...please wait until it is completed.")
                        temp_file = f"./{str(uuid.uuid4())}.pdf"
                        with open(temp_file, "wb") as file:
                            file.write(uploaded_file.getvalue())
                        embed_fn = get_embedding_model(st.session_state["embedding_model_name"])
                        embed_and_store_document(chromadb_ip,temp_file,col_name,embed_fn)
                        st.success(f"Embedding completed for: {uploaded_file.name}")
                    
            else:
                st.write("Unsupported file type")

def config_sidebar() -> None:
    with st.sidebar:
        if "chromadb_ip" not in st.session_state or st.session_state.chromadb_ip == "":
            st.warning("ChromaDB is not connected.")
        else:
            st.info(f"ChromaDB is currently connected to: {st.session_state.chromadb_ip}.")
        if "llm_api_key" not in st.session_state or st.session_state.llm_api_key == "":
            st.warning("No LLM API key set. Please set API key to use.")
        else:
            st.info(f"LLM API key set, click on 👁 icon to verify.")

def store_configurations():
    # Update the session state with the form data
    st.session_state["chromadb_ip"] = st.session_state.get('_chromadb_ip', "")
    st.session_state["embedding_model_name"] = st.session_state.get('_embedding_model_name', "")
    st.session_state["llm_api_key"] = st.session_state.get('_llm_api_key', "")
    return "success"