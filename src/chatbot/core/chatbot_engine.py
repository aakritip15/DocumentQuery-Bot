import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain,RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from .document_processor import DocumentProcessor
from ..form.conversational_form import ConversationalForm
from ..agent.tool_agent import ToolAgent
from langchain.memory import ConversationBufferMemory

class ChatbotEngine:
    """Core chatbot engine for document-based Q&A."""
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="result")


        self.document_processor = DocumentProcessor()
        # self.qa_chain: Optional[ConversationalRetrievalChain] = None
        self.qa_chain: Optional[RetrievalQA] = None
        self.conversation_state = "general"  # general, collecting_info, booking_appointment
        self.tools = ToolAgent()
        self.form: ConversationalForm = ConversationalForm(tools=self.tools)
        self.in_form: bool = False
        
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
            5. However, if you can answer based on the history of the conversation, do so.

            Assistant: """,
            input_variables=["context", "question"],  

        )
    
    def load_uploaded_files(self, files: List[tuple]) -> bool:
        """Load and process uploaded files for the chatbot.
        
        Args:
            files: List of tuples containing (filename, file_content_bytes)
        """
        try:
            # Process documents directly from file content
            documents = self.document_processor.process_uploaded_files(files)
            
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
                chain_type_kwargs={"prompt": self.prompt_template},
                memory = self.memory,
            )
            
            return True
            
        except Exception as e:
            print(f"Error loading documents: {str(e)}")
            return False
    
    def chat(self, message: str) -> Dict[str, Any]:
        """Process user message and return response."""
        # If we do not yet have a retriever and we are not in a form, ask to upload
        if not self.qa_chain and not self.in_form:
            return {
                "response": "Please upload some documents first so I can help answer your questions.",
                "sources": [],
                "needs_info": False,
            }

        # Detect contact/appointment intent
        contact_keywords = [
            "call me",
            "contact me",
            "book appointment",
            "schedule",
            "call",
            "reach out",
            "appointment",
            "phone number",
            "email me",
        ]
        needs_contact = any(keyword in message.lower() for keyword in contact_keywords)

        # If already in form flow or intent detected, run form conversation instead of QA
        if self.in_form or needs_contact:
            form_started_now = False
            if not self.in_form:
                # Start the form flow
                self.in_form = True
                form_started_now = True
                first_prompt = self.form.start()
                return {
                    "response": "I can help schedule that. I'll need a few details.",
                    "sources": [],
                    "needs_info": True,
                    "form_prompt": first_prompt,
                    "form_complete": False,
                }

            # We are in the middle of the form
            reply, next_prompt = self.form.handle_input(message)
            if self.form.is_complete():
                data = self.form.get_data()
                # Keep a copy in user_info
                self.user_info.update({
                    "name": data.get("name"),
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                })
                # Auto-book via tool agent
                confirmation_id = None
                try:
                    confirmation_id = self.tools.tool_book_appointment(data)
                except Exception:
                    confirmation_id = None
                self.in_form = False
                return {
                    "response": (
                        "Thanks! I have all the details and will proceed with booking." if not confirmation_id
                        else f"Your appointment is booked. Confirmation: {confirmation_id}"
                    ),
                    "sources": [],
                    "needs_info": False,
                    "form_complete": True,
                    "form_data": data,
                }

            return {
                "response": reply,
                "sources": [],
                "needs_info": True,
                "form_prompt": next_prompt,
                "form_complete": False,
            }

        # Normal QA flow
        try:
            result = self.qa_chain({"query": message})
            response = result["result"]
            sources = []
            if "source_documents" in result:
                sources = [
                    {
                        "source": doc.metadata.get("source", "Unknown"),
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    }
                    for doc in result["source_documents"]
                ]
            return {
                "response": response,
                "sources": sources,
                "needs_info": False,
            }
        except Exception as e:
            return {
                "response": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "needs_info": False,
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