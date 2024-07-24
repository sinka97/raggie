import streamlit as st
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_community import GoogleSearchAPIWrapper

from rag_data_model import QuestionType, GradeQuestion
from rag_utils import load_col_from_chroma, upload_excel

def question_check(state, config, llm):
    # Prompt
    system = """You are a grader assessing whether the user is asking a question that requires more information from the internet or not. \n 
        If the user's input is a question you cannot answer with your current information, grade it as yes. \n
        If the user's input is question that can be answered with your current information, grade it as no. \n
        If the user's input is not a question, grade it as no. \n
        Give a binary score 'yes' or 'no' score to indicate whether the input is a question that requires more information from the internet or not."""
    general_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "User's input: {question}"),
        ]
    )
    structured_llm_grader = llm.with_structured_output(GradeQuestion)
    general_grader = general_prompt | structured_llm_grader
    question = state["question"]
    score = general_grader.invoke({"question": question}, config=config)
    grade = score.binary_score
    if grade == "yes":
        print("---GRADE: QUESTION---")
        return {"question": question, "isQuestion": "yes"}
    else:
        print("---GRADE: NOT QUESTION---")
        return {"question": question, "isQuestion": "no"}

def retrieve(state, config, llm, general_llm, chromadb_ip, embed_fn, dfs):
    print("---RETRIEVE---")
    # Fetch Question from Graph State
    question = state["question"]
    # Load documents
    monthly_report_retriever = load_col_from_chroma(chromadb_ip, "Monthly_Security_Reports", embed_fn).as_retriever()
    im8_retriever = load_col_from_chroma(chromadb_ip, "IM8", embed_fn).as_retriever()
    # Load excel and initialize dataframe agent
    # TODO: replace excel file with correct file after everything is figured out
    # dfs = load_col_from_chroma(excel_file='excel_file',sheet_name='sheet_name')
    dfAgent = create_pandas_dataframe_agent(general_llm, dfs, agent_type="tool-calling", verbose=True,allow_dangerous_code=True)
 
    # Prompt
    system = """You are a categorizer assessing whether the user's input is related to any 1 of 4 categories of data. \n 
        The 4 categories are: 'TRXX1 Monthly Reports', 'IT001 Assets Lists', 'IM8' , or 'Others' \n
        The TRXX1 Monthly Reports are monthly reports which pertain to the Operation and Maintenance of CCTV1 \n
        The IT001 Assets Lists contains the names, descriptions, locations, etc for all assets in the IT001 Project\n
        IM8 are guides for Infocomm Technology & Smart Services which have to be complied to. They contain policies, standards and guidelines for subjects such as Infrastructure Security.\n
        If the user's input is none of the above 3 categories, it is classified as 'Others'. \n
        Give an output of either 'TRXX1 Monthly Reports', 'IT001 Assets Lists', 'IM8', or 'Others' to indicate the category of the input."""
    general_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "User's input: {question}"),
        ]
    )
    structured_llm_qType = llm.with_structured_output(QuestionType)
    qType_grader = general_prompt | structured_llm_qType
    qtype = qType_grader.invoke({"question": question}, config=config)    
    if qtype.questionType == "TRXX1 Monthly Reports":
        documents = []
        documents.extend(monthly_report_retriever.invoke(question, config=config))
        print("---RETRIEVED TRXX1 Monthly Reports---")
    elif qtype.questionType == "IT001 Assets Lists":
        documents = []
        documents.append(dfAgent.invoke({"input":question}, config=config)["output"])
        print("---RETRIEVED IT001 Assets Lists---")
    elif qtype.questionType == "IM8":
        documents = []
        documents.append(im8_retriever.invoke(question, config=config))
        print("---RETRIEVED IM8---")
    return {"documents": documents, "question": question}

def generate(state, config, general_llm):
    print("---GENERATE---")
    # Fetch Question and Documents from Graph State
    question = state["question"]
    documents = state["documents"]

    # Prompt
    prompt = hub.pull("rlm/rag-prompt")
    rag_chain = prompt | general_llm | StrOutputParser()
    if state["web_search"] == "no":
        # RAG generation
        generation = rag_chain.invoke({"context": documents, "question": question},config=config)
        return {"documents": documents, "question": question, "generation": generation}
    else: 
        if state['isQuestion'] == 'yes':
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "Based on the given web search results, answer the user's question."),
                    ("human", "Web search results: \n\n {documents} \n\n User question: {question}"),
                ]
            )
            chain = prompt | general_llm | StrOutputParser()
            generation = chain.invoke({"documents": documents, "question": question},config=config)
            return {"documents": documents, "question": question, "generation": generation}
        else:
            generation = general_llm.invoke(question,config=config)
            return {"question": question, "generation": generation}

def grade_documents(state, config, llm):
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    web_search = "yes"

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
    structured_llm_grader = llm.with_structured_output(GradeQuestion)
    retrieval_grader = grade_prompt | structured_llm_grader
    if documents == []:
        print("---NO DOCUMENTS RETRIEVED---")
    # Score each doc
    filtered_docs = []
    for d in documents:
        try:
            score = retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
                ,config=config
            )
        except:
            score = retrieval_grader.invoke(
                {"question": question, "document": d}
                ,config=config
            )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    if filtered_docs != []:
        web_search = "no"
    return {"documents": filtered_docs, "question": question, "web_search": web_search}

def web_search(state, config):
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    # Web search
    search = GoogleSearchAPIWrapper(k=3) #k is the number of results to return
    search_tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    web_results = search_tool.invoke({"query": question},config=config)
    documents.append(web_results)

    return {"documents": documents, "question": question}

def general_answer(state, config, llm):
    question = state["question"]
    answer = llm.invoke(question, config=config)
    return {"question": question, "generation": answer}

