"""Streamlit page showing whatever is needed."""
import streamlit as st
from st_utils import config_sidebar, disable_deploy_button, store_configurations

import chromadb
from chromadb.config import Settings

####################
#### STREAMLIT #####
####################

st.set_page_config(
    page_title="RAGGIE",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items=None,
)
st.title("⚙️ Configurations")

disable_deploy_button()
config_sidebar()

# Initialize session state keys if they don't exist
if "chromadb_ip" not in st.session_state:
    st.session_state["chromadb_ip"] = ""

if "embedding_model_name" not in st.session_state:
    st.session_state["embedding_model_name"] = "sentence-transformers/all-mpnet-base-v2"

if "llm_api_key" not in st.session_state:
    st.session_state["llm_api_key"] = ""

if "google_api_key" not in st.session_state:
    st.session_state["google_api_key"] = ""

with st.form('config'):
    # User inputs for configuration
    chromadb_ip = st.text_input(
        "ChromaDB IP",
        value=st.session_state["chromadb_ip"] if st.session_state["chromadb_ip"] else "Enter the IP Address of ChromaDB Instance",
        key='_chromadb_ip'
    )
    
    # TODO: Add additional embedding model support
    options = ["sentence-transformers/all-mpnet-base-v2", "for future implementation"]
    embedding_model_name = st.selectbox(
        "Choose an option:",
        options,
        key='_embedding_model_name',
        index=options.index(st.session_state["embedding_model_name"])
    )
    
    # LLM API KEY
    llm_api_key = st.text_input(
        'LLM API Token',
        value=st.session_state["llm_api_key"] if st.session_state["llm_api_key"] else "Enter your API Key",
        type='password',
        key="_llm_api_key"
    )

    google_api_key = st.text_input(
        'Google API Key',
        value=st.session_state["google_api_key"] if st.session_state["google_api_key"] else "Enter your API Key",
        type='password',
        key="_google_api_key"
    )
    
    submitted = st.form_submit_button("Save Configuration", on_click=store_configurations)
    if submitted:
        # Instantiate connection to client
        client = chromadb.HttpClient( 
            host=chromadb_ip, 
            port=8000, 
            ssl=False,
            settings=Settings(anonymized_telemetry=False)
        )
        # Check if connection is live
        try:
            client.heartbeat()
            st.success("Configuration saved!")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            
        
