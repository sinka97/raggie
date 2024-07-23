# Overwrite Old pysqlite3
import sys
if 'pysqlite3' in sys.modules:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
import pandas as pd

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyMuPDFLoader


def get_embedding_model(model_name=None,device=None,normalize=False):
    # Only accepts HuggingFace Model Names -- TODO: Change to accept any models?
    if not model_name:
        model_name="sentence-transformers/all-mpnet-base-v2"
    if not device:
        model_kwargs = {'device': 'cpu'}
    else:
        model_kwargs = {'device': device}
    encode_kwargs = {'normalize_embeddings': normalize}
    embed_fn = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    return embed_fn

def embed_and_store_document(chromadb_ip,file_name,collection_name,embed_fn):
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
    except Exception as e:
        return "error", f"An unexpected error occurred: {e}"
    text_splitter = SemanticChunker(embed_fn)
    pdf_data = PyMuPDFLoader(file_name, extract_images=True).load()
    splits = text_splitter.split_documents(pdf_data)
    Chroma.from_documents(splits, client=client, collection_name=collection_name, embedding=embed_fn)
    return "success", f"Document stored to remote chromadb collection: {collection_name}."

def load_col_from_chroma(chromadb_ip, collection_name, embed_fn):
    # Instantiate connection to client
    client = chromadb.HttpClient( 
        host=chromadb_ip, 
        port=8000, 
        ssl=False, 
        headers=None, 
        settings=Settings(allow_reset=False, anonymized_telemetry=False), 
        tenant=DEFAULT_TENANT, 
        database=DEFAULT_DATABASE, 
    )
    # Check if collection exists
    try:
        client.get_or_create_collection(collection_name)
    except Exception as e:
        return "error", f"An unexpected error occurred: {e}"
    col = Chroma(client=client, embedding_function=embed_fn, collection_name=collection_name)
    return col

def upload_excel(excel_file,sheet_name):
    dfDict = pd.read_excel(excel_file, sheet_name=sheet_name)
    dfs = []
    dfs.append(dfDict)
    return dfs