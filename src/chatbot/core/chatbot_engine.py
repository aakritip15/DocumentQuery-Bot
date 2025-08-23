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
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash", debug: bool = False):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="result")
        self.debug = debug

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
            2. If the user asks about booking appointments, scheduling, or contact information, respond that you'd be happy to help and ask for their contact details.
            3. Be conversational, helpful, and professional.
            4. If you cannot answer based on the context, say so politely and suggest they ask a different question.
            5. If the question seems related to appointments or contact, mention that you can help with scheduling.
            6. Keep responses concise but informative.

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
    
    def _detect_intent(self, message: str) -> str:
        """Use LLM to intelligently detect user intent."""
        intent_prompt = f"""
        Analyze the following user message and classify the intent into one of these categories:
        
        - "qa": User wants to ask a question about documents or get information
        - "appointment": User wants to book an appointment, schedule something, or provide contact information
        - "contact": User wants to be contacted, called, or wants to share their contact details
        
        User message: "{message}"
        
        Respond with only the category (qa, appointment, or contact):
        """
        
        if self.debug:
            print(f"🔍 Intent detection prompt: {intent_prompt}")
        
        try:
            response = self.llm.invoke(intent_prompt)
            intent = response.content.strip().lower()
            
            if self.debug:
                print(f"🤖 LLM intent response: '{intent}'")
            
            # Validate the response
            if intent in ["qa", "appointment", "contact"]:
                if self.debug:
                    print(f"✅ Intent detected: {intent}")
                return intent
            else:
                # Fallback to keyword-based detection if LLM response is unexpected
                if self.debug:
                    print(f"⚠️ Unexpected LLM response, falling back to keyword detection")
                contact_keywords = [
                    "call me", "contact me", "book appointment", "schedule", 
                    "call", "reach out", "appointment", "phone number", "email me",
                    "book", "reserve", "make appointment", "set up meeting"
                ]
                if any(keyword in message.lower() for keyword in contact_keywords):
                    if self.debug:
                        print(f"🔑 Keyword fallback detected: appointment")
                    return "appointment"
                if self.debug:
                    print(f"🔑 Keyword fallback detected: qa")
                return "qa"
                
        except Exception as e:
            if self.debug:
                print(f"❌ Error in intent detection: {e}")
            # Fallback to keyword-based detection
            contact_keywords = [
                "call me", "contact me", "book appointment", "schedule", 
                "call", "reach out", "appointment", "phone number", "email me",
                "book", "reserve", "make appointment", "set up meeting"
            ]
            if any(keyword in message.lower() for keyword in contact_keywords):
                if self.debug:
                    print(f"🔑 Error fallback detected: appointment")
                return "appointment"
            if self.debug:
                print(f"🔑 Error fallback detected: qa")
            return "qa"

    def chat(self, message: str, history: Optional[list] = None) -> Dict[str, Any]:
        """Process user message and return response. Optionally use chat history."""
        # If we do not yet have a retriever and we are not in a form, ask to upload
        if not self.qa_chain and not self.in_form:
            return {
                "response": "Please upload some documents first so I can help answer your questions.",
                "sources": [],
                "needs_info": False,
            }

        # Use LLM to intelligently detect intent
        intent = self._detect_intent(message)
        
        if self.debug:
            print(f"🎯 Detected intent: {intent}")
            print(f"📝 Current form state: in_form={self.in_form}")
        
        # If already in form flow or intent detected, run form conversation instead of QA
        if self.in_form or intent in ["appointment", "contact"]:
            if self.debug:
                print(f"🔄 Switching to form mode (intent: {intent}, in_form: {self.in_form})")
            
            form_started_now = False
            if not self.in_form:
                # Start the form flow
                self.in_form = True
                form_started_now = True
                first_prompt = self.form.start()
                if self.debug:
                    print(f"🚀 Form started with prompt: {first_prompt}")
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
        if self.debug:
            print(f"📚 Staying in QA mode for intent: {intent}")
        
        try:
            # Format history for prompt
            history_text = ""
            if history:
                history_text = "\n".join(
                    f"{h['role'].capitalize()}: {h['content']}" for h in history if 'role' in h and 'content' in h
                )
            
            # For RetrievalQA, we only pass the query
            # If you want to include chat history context, you'd need to modify the query
            enhanced_query = message
            if history_text:
                enhanced_query = f"Context from previous conversation: {history_text}\n\nCurrent question: {message}"
            
            if self.debug:
                print(f"🔍 Enhanced query: {enhanced_query[:100]}...")
            
            result = self.qa_chain.invoke({
                "query": enhanced_query,
            })
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
    
    def reset_form(self):
        """Reset the form state and return to QA mode."""
        if self.debug:
            print(f"🔄 Resetting form state")
        self.in_form = False
        self.form.reset()
        return {
            "response": "Form reset. I'm ready to answer questions about your documents.",
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