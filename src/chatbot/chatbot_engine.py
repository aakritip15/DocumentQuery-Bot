import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from .document_processor import DocumentProcessor


class ChatbotEngine:
    """Core chatbot engine for document-based Q&A."""
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        self.document_processor = DocumentProcessor()
        self.qa_chain: Optional[RetrievalQA] = None
        self.conversation_state = "general"  # general, collecting_info, booking_appointment
        
        # Initialize conversation memory
        self.user_info = {
            "name": None,
            "phone": None,
            "email": None
        }
        
        self.setup_prompt_template()
    
    def setup_prompt_template(self):
        """Setup the prompt template for the Q&A chain."""
        self.prompt_template = PromptTemplate(
            template="""You are a helpful AI assistant that can answer questions based on the provided documents and help users with appointment booking.

            Context from documents:
            {context}

            Human: {question}

            Instructions:
            1. If the question can be answered using the provided context, give a comprehensive answer based on the documents.
            2. If the user asks you to "call them", "contact them", or wants to "book an appointment", respond that you'd be happy to help and ask for their contact information (name, phone number, and email).
            3. Be conversational and helpful.
            4. If you cannot answer based on the context, say so politely.

            Assistant: """,
            input_variables=["context", "question"]
        )
    
    def load_documents(self, file_paths: List[str]) -> bool:
        """Load and process documents for the chatbot."""
        try:
            # Process documents
            documents = self.document_processor.process_documents(file_paths)
            
            if not documents:
                return False
            
            # Create vector store
            vectorstore = self.document_processor.create_vectorstore(documents)
            
            # Create retrieval QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            
            return True
            
        except Exception as e:
            print(f"Error loading documents: {str(e)}")
            return False
    
    def load_existing_vectorstore(self) -> bool:
        """Load existing vector store if available."""
        try:
            vectorstore = self.document_processor.load_vectorstore()
            if vectorstore:
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
                    return_source_documents=True,
                    chain_type_kwargs={"prompt": self.prompt_template}
                )
                return True
            return False
        except Exception as e:
            print(f"Error loading existing vectorstore: {str(e)}")
            return False
    
    def chat(self, message: str) -> Dict[str, Any]:
        """Process user message and return response."""
        if not self.qa_chain:
            return {
                "response": "Please upload some documents first so I can help answer your questions.",
                "sources": [],
                "needs_info": False
            }
        
        # Check if user is asking for contact/appointment
        contact_keywords = ["call me", "contact me", "book appointment", "schedule", "call", "reach out"]
        needs_contact = any(keyword in message.lower() for keyword in contact_keywords)
        
        try:
            # Get response from QA chain
            result = self.qa_chain({"query": message})
            
            response = result["result"]
            sources = []
            
            # Extract source information
            if "source_documents" in result:
                sources = [
                    {
                        "source": doc.metadata.get("source", "Unknown"),
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    for doc in result["source_documents"]
                ]
            
            return {
                "response": response,
                "sources": sources,
                "needs_info": needs_contact
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "needs_info": False
            }
    
    def get_conversation_state(self) -> str:
        """Get current conversation state."""
        return self.conversation_state
    
    def set_conversation_state(self, state: str):
        """Set conversation state."""
        self.conversation_state = state
    
    def update_user_info(self, field: str, value: str):
        """Update user information."""
        if field in self.user_info:
            self.user_info[field] = value
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return self.user_info.copy()
    
    def reset_user_info(self):
        """Reset user information."""
        self.user_info = {
            "name": None,
            "phone": None,
            "email": None
        }