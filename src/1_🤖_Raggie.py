import os
import streamlit as st
from langgraph.graph import END, StateGraph
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AIMessage

from rag_graph_state import GraphState
from rag_graph_node import *
from rag_graph_edge import *
from rag_utils import get_embedding_model

import pandas as pd

from st_utils import main_page_sidebar, disable_deploy_button

st.set_page_config(
    page_title="RAGGIE",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items=None,
)

st.title("🤖 Raggie Demo")
st.markdown("<h3 style='font-size:20px;'>Retrieval-Augmented Generation for Grasping Information Efficiently</h3>", unsafe_allow_html=True)

disable_deploy_button()
main_page_sidebar()

## START
if 'llm_api_key' in st.session_state and st.session_state.llm_api_key != "" and 'agent' not in st.session_state:
    chromadb_ip = st.session_state.chromadb_ip
    embed_fn = get_embedding_model(model_name=st.session_state.embedding_model_name)
    if 'dfs' in st.session_state:
        dfs = st.session_state.dfs
    else:
        dfDict = pd.read_excel('./IT001-RPT.xlsx', sheet_name='IT001-Hardware')
        dfs = []
        dfs.append(dfDict)

    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=st.session_state['llm_api_key'], temperature=0.1)
    general_llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=st.session_state['llm_api_key'], temperature=0.1)
    os.environ["GOOGLE_API_KEY"] = st.session_state["google_api_key"]

    workflow = StateGraph(GraphState)
    # Define the nodes
    workflow.add_node("retrieve", lambda state,config: retrieve(state,config,llm,general_llm,chromadb_ip,embed_fn, dfs))
    workflow.add_node("grade_documents", lambda state,config: grade_documents(state,config,llm))
    workflow.add_node("generate", lambda state,config: generate(state,config,general_llm))
    workflow.add_node("web_search_node", web_search)
    workflow.add_node("general_answer", lambda state,config: general_answer(state,config,llm))
    workflow.add_node("question_check", lambda state,config: question_check(state,config,llm))

    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "noGenerate": "question_check",
            "generate": "generate",
        },
    )
    # workflow.add_edge("transform_query", "web_search_node")
    workflow.add_edge("general_answer", "generate")
    workflow.add_conditional_edges(
        "question_check",
        check_if_question,
        {
            "no": "general_answer",
            "yes": "web_search_node",
        },
    )
    workflow.add_edge("web_search_node", "generate")
    workflow.add_edge("generate", END)

    memory = SqliteSaver.from_conn_string(":memory:")
    st.session_state['agent'] = workflow.compile(checkpointer=memory) #create react agent
    print("---AGENT CREATED---")

# Initialize the conversation list in session state
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []

def generate_response(input_text):
    if 'agent' not in st.session_state:  # Check if agent_executor is in session_state
        st.error('Please enter your API Key.')
        return
    config = {"configurable": {"thread_id": "1"}}
    result = st.session_state['agent'].invoke({"question":input_text}, config=config)
    response = result['generation']
    if isinstance(response, AIMessage):
        print(result['documents'])
        st.info(response.pretty_repr())
    else:
        print(result['documents'])
        st.info(response)


    # Append the input and response to the conversation list
    st.session_state['conversation'].append(('User', input_text))
    st.session_state['conversation'].append(('Bot', response))

with st.form('my_form'):
    text = st.text_area('Ask Raggie:', 'Enter a question here.')
    submitted = st.form_submit_button('Submit')
    if submitted:
        generate_response(text)

# Display the conversation
for speaker, message in st.session_state['conversation']:
    st.write(f"{speaker}: {message}")

with st.columns(3)[1]:
    st.image('./src/lta_logo_2024.png', use_column_width=True)