"""Streamlit page showing whatever is needed."""
import streamlit as st
from st_utils import disable_deploy_button
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

disable_deploy_button()

st.markdown("""
### Get Started with Raggie
Simply ask a question to begin. Raggie currently has knowledge on the following topics:
- **Contract TRXX1 Monthly Security Reports**
- **IT001 Hardware Asset List**
- **IM8 Guide for Infrastructure Security (Non-S)**

*More topics will be added as development continues.*

### Using Raggie for Your Own Documents
Upload your document and then ask your question.

### Raggie's Capabilities
- Information Extraction
- Document Summarization
- Web Search
- Idea Generation
- And many more incredible AI features!

Raggie leverages the power of **Anthropic's Claude 3.5 Sonnet**.

### Contact Us
For further queries or to request additional knowledge topics for Raggie, please contact: [sinka97.dev@gmail.com](mailto:sinka97.dev@gmail.com)
""")