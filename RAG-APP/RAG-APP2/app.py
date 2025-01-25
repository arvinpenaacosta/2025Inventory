from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# LangChain and related imports
from langchain_ollama import OllamaLLM
from warnings import filterwarnings
filterwarnings("ignore", category=DeprecationWarning)
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate


import os

# Application setup
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration
FOLDER_PATH = "db"
PDF_FOLDER = "pdf"
os.makedirs(PDF_FOLDER, exist_ok=True)

# LangChain Components
cached_llm = OllamaLLM(model="llama3.2:3b")
embedding = FastEmbedEmbeddings()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, 
    chunk_overlap=80, 
    length_function=len, 
    is_separator_regex=False
)

raw_prompt = PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input}
           Context: {context}
           Answer:
    [/INST]
"""
)

# Pydantic Models
class QueryModel(BaseModel):
    query: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index3.html", {"request": request})

@app.post("/ai")
async def ai_post(query_data: QueryModel):
    try:
        response = cached_llm.invoke(query_data.query)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask_pdf")
async def ask_pdf_post(query_data: QueryModel):
    try:
        vector_store = Chroma(persist_directory=FOLDER_PATH, embedding_function=embedding)
        
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 20,
                "score_threshold": 0.1,
            },
        )

        document_chain = create_stuff_documents_chain(cached_llm, raw_prompt)
        chain = create_retrieval_chain(retriever, document_chain)

        result = chain.invoke({"input": query_data.query})

        sources = [
            {"source": doc.metadata["source"], "page_content": doc.page_content}
            for doc in result["context"]
        ]

        return {"answer": result["answer"], "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/pdf")
async def pdf_post(file: UploadFile = File(...)):
    try:
        # Ensure file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        file_path = os.path.join(PDF_FOLDER, file.filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Load and process PDF
        loader = PDFPlumberLoader(file_path)
        docs = loader.load_and_split()
        
        chunks = text_splitter.split_documents(docs)

        # Create vector store
        vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=embedding, 
            persist_directory=FOLDER_PATH
        )
        vector_store.persist()

        return {
            "status": "Successfully Uploaded",
            "filename": file.filename,
            "doc_len": len(docs),
            "chunks": len(chunks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=8856)



# Run with: uvicorn app1:app  --reload
