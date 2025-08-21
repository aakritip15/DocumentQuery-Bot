import os
import tempfile
from typing import List, Optional
import PyPDF2
import docx2txt
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer

class DocumentProcessor:
    """Handles document loading, processing, and vector storage."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}
        )
        # self.embeddings = SentenceTransformer(
        #     "sentence-transformers/all-MiniLM-L6-v2"
        # )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore: Optional[Chroma] = None
        
    def load_text_from_file(self, file_path: str) -> str:
        """Load text content from various file formats."""
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            elif ext == '.pdf':
                return self._extract_pdf_text(file_path)
            elif ext == '.docx':
                return docx2txt.process(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise Exception(f"Error loading file {file_path}: {str(e)}")
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def process_documents(self, file_paths: List[str]) -> List[Document]:
        """Process multiple documents and return list of Document objects."""
        documents = []
        
        for file_path in file_paths:
            try:
                text = self.load_text_from_file(file_path)
                # Create chunks from the text
                chunks = self.text_splitter.split_text(text)
                
                # Convert chunks to Document objects
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": os.path.basename(file_path),
                            "chunk_id": i,
                            "file_path": file_path
                        }
                    )
                    documents.append(doc)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue
        
        return documents
    
    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """Create and persist vector store from documents."""
        if not documents:
            raise ValueError("No documents provided to create vectorstore")
            
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        return self.vectorstore
    
    def load_vectorstore(self) -> Optional[Chroma]:
        """Load existing vector store if available."""
        if os.path.exists(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                return self.vectorstore
            except Exception as e:
                print(f"Error loading vectorstore: {str(e)}")
                return None
        return None
    
    def get_vectorstore(self) -> Optional[Chroma]:
        """Get the current vectorstore instance."""
        return self.vectorstore