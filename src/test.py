import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from langchain_chroma import Chroma
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from rag_utils import get_embedding_model



model_name="sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embed_fn = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

chromadb_ip = "13.250.4.143"
file_name = "./3f6e6a9d-9cd3-4f0b-8e68-fb894d4d40f5.pdf"
collection_name = "test_data_2"
client = chromadb.HttpClient( 
    host=chromadb_ip, 
    port=8000, 
    ssl=False,
    settings=Settings(), 
    tenant=DEFAULT_TENANT,
    database=DEFAULT_DATABASE
    )
chromadb.get_or_create_collection("test_data_2")
text_splitter = SemanticChunker(embed_fn)
docs = []
pdf_data = PyMuPDFLoader(file_name, extract_images=True).load()
docs.extend(pdf_data)
splits = text_splitter.split_documents(docs)
Chroma.from_documents(splits, client=client, collection_name=collection_name, embedding=embed_fn)