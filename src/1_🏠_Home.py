import os
from langchain_huggingface import HuggingFaceEmbeddings
#from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_chroma import Chroma
from langchain_google_community import GoogleSearchAPIWrapper
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from typing import List
from typing_extensions import TypedDict
from langchain.schema import Document
from langgraph.graph import END, StateGraph
from langchain.tools.retriever import create_retriever_tool
from langchain_experimental.text_splitter import SemanticChunker
import streamlit as st

load_dotenv()

os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
# os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
#os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

model_name = "sentence-transformers/all-mpnet-base-v2" #"sentence-transformers/all-mpnet-base-v2, magorshunov/layoutlm-invoices"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
hf = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

text_splitter = SemanticChunker(hf)

if not os.path.exists("chroma_db"):
    docs = []
    pdfData1 = PyMuPDFLoader('C:/Users/bluea/Desktop/LTA/data/Monthly_Security_Report_March_24.pdf', extract_images=True).load()
    pdfData2 = PyMuPDFLoader('C:/Users/bluea/Desktop/LTA/data/Monthly_Security_Report_Feb_24.pdf', extract_images=True).load()
    docs.extend(pdfData1)
    docs.extend(pdfData2)
    splits = text_splitter.split_documents(docs)
    db = Chroma.from_documents(splits, hf, persist_directory="chroma_db", collection_name="Monthly_Security_Reports")
else:
    db = Chroma(persist_directory="chroma_db", embedding_function=hf,collection_name="Monthly_Security_Reports")
retriever = db.as_retriever()

# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


if 'llm_api_key' in st.session_state:
    # LLM with function call
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1, google_api_key=st.session_state['llm_api_key'])
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    # Prompt
    system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
        If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )

    # Retrieval Grader
    retrieval_grader = grade_prompt | structured_llm_grader
    prompt = hub.pull("rlm/rag-prompt")
    # Generate
    rag_chain = prompt | llm | StrOutputParser()

    # Question Rewriter
    system = """You a question re-writer that converts an input question to a better version that is optimized \n 
        for web search. Look at the input and try to reason about the underlying semantic intent / meaning."""
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Here is the initial question: \n\n {question} \n Formulate an improved question.",
            ),
        ]
    )

    question_rewriter = re_write_prompt | llm | StrOutputParser()

    ### Build Google Search Tool ###
    search = GoogleSearchAPIWrapper(k=3) #k is the number of results to return
    search_tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    ### Build retriever tool ###
    retriever_tool = create_retriever_tool(
        retriever,
        "pdf_retriever",
        "Searches and returns excerpts from the pdf.",
    )

    # tools = [retriever_tool,search_tool]

    ### Graph State and Nodes ###
    class GraphState(TypedDict):
        """
        Represents the state of our graph.

        Attributes:
            question: question
            generation: LLM generation
            web_search: whether to add search
            documents: list of documents
        """

        question: str
        generation: str
        web_search: str
        documents: List[str]

    def retrieve(state):
        print("---RETRIEVE---")
        question = state["question"]

        # Retrieval
        documents = retriever.invoke(question)
        return {"documents": documents, "question": question}


    def generate(state):
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]

        # RAG generation
        generation = rag_chain.invoke({"context": documents, "question": question})
        return {"documents": documents, "question": question, "generation": generation}


    def grade_documents(state):
        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        question = state["question"]
        documents = state["documents"]

        # Score each doc
        filtered_docs = []
        web_search = "No"
        for d in documents:
            score = retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
            )
            grade = score.binary_score
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                web_search = "Yes"
                continue
        if filtered_docs != []:
            web_search = "No"
        return {"documents": filtered_docs, "question": question, "web_search": web_search}


    def transform_query(state):
        print("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]

        # Re-write question
        better_question = question_rewriter.invoke({"question": question})
        return {"documents": documents, "question": better_question}


    def web_search(state):
        print("---WEB SEARCH---")
        question = state["question"]
        documents = state["documents"]

        # Web search
        web_results = search_tool.invoke({"query": question})
        documents.append(web_results)

        return {"documents": documents, "question": question}

    ### Edges
    def decide_to_generate(state):
        print("---ASSESS GRADED DOCUMENTS---")
        web_search = state["web_search"]

        if web_search == "Yes":
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
            )
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"
        
    ###                                 Build Graph                         ###
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("retrieve", retrieve)  # retrieve
    workflow.add_node("grade_documents", grade_documents)  # grade documents
    workflow.add_node("generate", generate)  # generatae
    workflow.add_node("transform_query", transform_query)  # transform_query
    workflow.add_node("web_search_node", web_search)  # web search

    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "web_search_node")
    workflow.add_edge("web_search_node", "generate")
    workflow.add_edge("generate", END)

    st.session_state['agent'] = workflow.compile() #create react agent

#streamlit code
st.image('lta_logo_2024.png')
st.title('LTA Chatbot Demo')

with st.sidebar.form('my_sidebar_form'):
    LLM_API_Token = st.text_input('LLM API Token', type='password')
    sidebar_submitted = st.form_submit_button('Submit')

if sidebar_submitted:
    st.session_state['llm_api_key']= LLM_API_Token
    

# Initialize the conversation list in session state
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []

def generate_response(input_text):
    if 'agent' not in st.session_state:  # Check if agent_executor is in session_state
        st.error('Please enter your API Key.')
        return
    result = st.session_state['agent'].invoke({"question":input_text})
    response = result['generation']
    st.info(response)

    # Append the input and response to the conversation list
    st.session_state['conversation'].append(('User', input_text))
    st.session_state['conversation'].append(('Bot', response))

with st.form('my_form'):
    text = st.text_area('Enter text:', 'Enter a question here.')
    submitted = st.form_submit_button('Submit')
    if submitted:
        generate_response(text)

# Display the conversation
for speaker, message in st.session_state['conversation']:
    st.write(f"{speaker}: {message}")