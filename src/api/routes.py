from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
import os
from dotenv import load_dotenv

from chatbot.core.document_processor import DocumentProcessor
from chatbot.core.chatbot_engine import ChatbotEngine
from . import schema

# Load environment variables
load_dotenv()

router = APIRouter()

# Get Google API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# Initialize components
document_processor = DocumentProcessor()
chatbot_engine = ChatbotEngine(google_api_key=GOOGLE_API_KEY)

# Try to load existing vectorstore on startup
try:
    if chatbot_engine.load_existing_vectorstore():
        print("✅ Loaded existing vectorstore")
    else:
        print("ℹ️ No existing vectorstore found")
except Exception as e:
    print(f"⚠️ Warning: Could not load existing vectorstore: {e}")

@router.get("/", response_model=schema.HealthResponse)
async def root():
    """Root endpoint"""
    return {"status": "Document Q&A API is running"}

@router.post("/upload-documents", response_model=schema.UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents for RAG"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        uploaded_files = []
        file_paths = []
        
        for file in files:
            if file.filename:
                # Validate file type
                if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported file type: {file.filename}"
                    )
                
                # Save file temporarily and process
                file_path = f"documents/{file.filename}"
                os.makedirs("documents", exist_ok=True)
                
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                uploaded_files.append(file.filename)
                file_paths.append(file_path)
        
        # Process documents using ChatbotEngine (this creates vectorstore)
        if chatbot_engine.load_documents(file_paths):
            return {
                "message": f"Successfully processed {len(uploaded_files)} documents and created vector database",
                "files": uploaded_files
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to process documents")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@router.post("/ask", response_model=schema.QuestionResponse)
async def ask_question(question: str = Form(...)):
    """Ask a question and get RAG-based answer"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get answer from chatbot engine
        result = chatbot_engine.chat(question)
        
        return {
            "question": question,
            "answer": result["response"],
            "sources": [source["source"] for source in result.get("sources", [])]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.get("/health", response_model=schema.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/status")
async def get_status():
    """Get current system status"""
    has_vectorstore = chatbot_engine.qa_chain is not None
    return {
        "has_documents": has_vectorstore,
        "vectorstore_loaded": has_vectorstore,
        "documents_directory": "documents/",
        "chroma_db_directory": "./chroma_db"
    }