"""Streamlit page showing whatever is needed."""
import streamlit as st
from st_utils import add_sidebar, disable_deploy_button
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
add_sidebar()

# User inputs for configuration
chromadb_ip = st.text_input("ChromaDB IP", "Enter the IP Address of ChromaDB Instance")
# TODO: Add additional embedding model support
options = ["sentence-transformers/all-mpnet-base-v2", "for future implementation"]
embedding_model_name = st.selectbox("Choose an option:", options)
# LLM API KEY
LLM_API_Token = st.text_input('LLM API Token', type='password')

# Save configurations to session state
st.session_state.chromadb_ip = chromadb_ip
st.session_state.embedding_model_name = embedding_model_name
st.session_state['llm_api_key']= LLM_API_Token

if st.button("Save Configuration"):
    st.success("Configuration saved!")
