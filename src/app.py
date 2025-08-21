import streamlit as st
import os
from dotenv import load_dotenv
import tempfile
from chatbot.core.chatbot_engine import ChatbotEngine

# import ChatbotEngine 

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Document Chatbot",
    page_icon="🤖",
    layout="wide"
)

def initialize_chatbot():
    """Initialize chatbot with API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Please set your GOOGLE_API_KEY in the .env file")
        return None
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatbotEngine(api_key)
        st.session_state.messages = []
        st.session_state.documents_loaded = False
    
    return st.session_state.chatbot

def handle_file_upload(chatbot, uploaded_files):
    """Handle file uploads and process documents."""
    if uploaded_files:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        
        # Save uploaded files temporarily
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(temp_path)
        
        # Process documents
        with st.spinner("Processing documents..."):
            success = chatbot.load_documents(file_paths)
            
        # Clean up temporary files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except:
                pass
        os.rmdir(temp_dir)
        
        if success:
            st.success("Documents processed successfully!")
            st.session_state.documents_loaded = True
            return True
        else:
            st.error("Failed to process documents. Please check the file formats.")
            return False
    return False

def main():
    st.title("🤖 AI Document Chatbot")
    st.markdown("Upload documents and ask questions about them!")
    
    # Initialize chatbot
    chatbot = initialize_chatbot()
    if not chatbot:
        return
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['txt', 'pdf', 'docx'],
            help="Upload PDF, DOCX, or TXT files"
        )
        
        if st.button("Process Documents"):
            if uploaded_files:
                handle_file_upload(chatbot, uploaded_files)
            else:
                st.warning("Please select files to upload.")
        
        # Try to load existing vectorstore
        if not st.session_state.documents_loaded:
            if st.button("Load Existing Documents"):
                with st.spinner("Loading existing documents..."):
                    success = chatbot.load_existing_vectorstore()
                    if success:
                        st.success("Existing documents loaded!")
                        st.session_state.documents_loaded = True
                    else:
                        st.info("No existing documents found.")
        
        # Show document status
        if st.session_state.documents_loaded:
            st.success("✅ Documents loaded")
        else:
            st.info("📤 Upload documents to start")
    
    # Chat interface
    st.header("💬 Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"]):
                        st.write(f"**Source {i+1}:** {source['source']}")
                        st.write(f"*{source['content']}*")
                        st.divider()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.chat(prompt)
                
            st.write(response["response"])
            
            # Show sources if available
            if response["sources"]:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(response["sources"]):
                        st.write(f"**Source {i+1}:** {source['source']}")
                        st.write(f"*{source['content']}*")
                        st.divider()
            
            # Add assistant response to messages
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response["response"],
                "sources": response["sources"]
            })

if __name__ == "__main__":
    main()