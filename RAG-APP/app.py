import os
import tempfile
import time

import chromadb
import streamlit as st
import httpx
import ollama
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from streamlit.runtime.uploaded_file_manager import UploadedFile

system_prompt = """
you are an AI assistant tasked with providing helpful and accurate responses
"""

def process_document(uploaded_file: UploadedFile) -> list[Document]:
    temp_file = tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False)
    temp_file.write(uploaded_file.read())

    loader = PyMuPDFLoader(temp_file.name)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=125,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )
    all_splits = text_splitter.split_documents(docs)
    return all_splits

def get_vector_collection() -> chromadb.Collection:
    ollama_ef = OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text:latest"
    )

    chroma_client = chromadb.PersistentClient(path="./demo-rag-chroma")
    return chroma_client.get_or_create_collection(
        name="rag_app",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"},
    )

def add_to_vector_collection(all_splits: list[Document], file_name: str):
    collection = get_vector_collection()
    documents, metadatas, ids = [], [], []

    for idx, split in enumerate(all_splits):
        documents.append(split.page_content)
        metadatas.append(split.metadata)
        ids.append(f"{file_name}_{idx}")

    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )
    st.success("Data added to the vector store!")

def query_collection(prompt: str, n_results: int = 10, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            collection = get_vector_collection()
            results = collection.query(query_texts=[prompt], n_results=n_results)
            return results
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            if attempt < max_retries - 1:
                st.warning(f"Connection timeout. Retrying... (Attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                st.error("Failed to query vector collection. Please try again later.")
                return None

def call_llm(context: str, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model="llama3.2:3b",
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}, Question: {prompt}",
                    },
                ],
            )
            full_response = ""
            for chunk in response:
                if chunk["done"] is False:
                    full_response += chunk["message"]["content"]
                    yield chunk["message"]["content"]
                else:
                    break
            return full_response
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            if attempt < max_retries - 1:
                st.warning(f"LLM connection timeout. Retrying... (Attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                st.error("Failed to get response from the language model. Please try again.")
                return None




def main():
    st.set_page_config(page_title="RAG Question Answer")
    
    with st.sidebar:
        uploaded_file = st.file_uploader(
            "** Upload PDF files for QnA ** ", type=["pdf"], accept_multiple_files=False
        )

        process = st.button("⚡️ Process")

        if uploaded_file and process:
            normalize_uploaded_file_name = uploaded_file.name.translate(
                str.maketrans({"-": "_", ".": "_", " ": "_"})
            )
            all_splits = process_document(uploaded_file)
            add_to_vector_collection(all_splits, normalize_uploaded_file_name)

    st.header(" RAG Question Answer")

    prompt = st.text_area(" ** Ask a question related to your document :** ")
    ask = st.button("🔥 Ask")

    if ask and prompt:
        results = query_collection(prompt)
        if results:
            context = results.get("documents")[0]
            response = call_llm(context=context, prompt=prompt)
            if response:
                st.write_stream(response)

if __name__ == "__main__":
    main()
