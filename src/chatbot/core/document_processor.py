import os
from typing import List, Optional, Union
import PyPDF2
import docx2txt
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


class DocumentProcessor:
    """Handles document loading, processing, and vector storage."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore: Optional[Chroma] = None
        
    def process_file_content(self, file_content: bytes, filename: str) -> str:
        """Process file content directly from bytes without saving to disk."""
        _, ext = os.path.splitext(filename.lower())
        
        try:
            if ext == '.txt':
                return file_content.decode('utf-8')
            elif ext == '.pdf':
                return self._extract_pdf_text_from_bytes(file_content)
            elif ext == '.docx':
                return docx2txt.process(BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise Exception(f"Error processing file {filename}: {str(e)}")
    
    def _extract_pdf_text_from_bytes(self, pdf_content: bytes) -> str:
        """Extract text from PDF content in bytes."""
        text = ""
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def process_uploaded_files(self, files: List[tuple]) -> List[Document]:
        """Process multiple uploaded files and return list of Document objects.
        
        Args:
            files: List of tuples containing (filename, file_content_bytes)
        """
        documents = []
        
        for filename, file_content in files:
            try:
                text = self.process_file_content(file_content, filename)
                # Create chunks from the text
                chunks = self.text_splitter.split_text(text)
                
                # Convert chunks to Document objects
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": filename,
                            "chunk_id": i
                        }
                    )
                    documents.append(doc)
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
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
    
    def get_vectorstore(self) -> Optional[Chroma]:
        """Get the current vectorstore instance."""
        return self.vectorstore