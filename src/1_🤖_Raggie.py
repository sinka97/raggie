import streamlit as st
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AIMessage

from functools import partial

from rag_graph_state import GraphState
from rag_graph_node import *
from rag_graph_edge import *

from st_utils import main_page_sidebar, disable_deploy_button

st.set_page_config(
    page_title="RAGGIE",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items=None,
)
st.image('./src/lta_logo_2024.png')
st.title("🤖 Raggie Demo")
st.markdown("<h3 style='font-size:20px;'>Retrieval-Augmented Generation for Grasping Information Efficiently</h3>", unsafe_allow_html=True)

disable_deploy_button()
main_page_sidebar()

## START
if 'llm_api_key' in st.session_state:
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=st.session_state['llm_api_key'], temperature=0.1)
    general_llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=st.session_state['llm_api_key'], temperature=0.1)

    workflow = StateGraph(GraphState)
    # Define the nodes
    workflow.add_node("retrieve", partial(retrieve,llm,general_llm))  # retrieve
    workflow.add_node("grade_documents", partial(grade_documents,llm))  # grade documents
    workflow.add_node("generate", partial(generate,general_llm))  # generatae
    # workflow.add_node("transform_query", transform_query)  # transform_query
    workflow.add_node("web_search_node", web_search)  # web search
    workflow.add_node("general_answer", partial(general_answer,llm))
    workflow.add_node("question_check", partial(question_check,llm))

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