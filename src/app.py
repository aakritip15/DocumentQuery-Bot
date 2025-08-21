import streamlit as st
import requests
import os
from typing import List
import tempfile

# FastAPI backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

def main():
    st.set_page_config(
        page_title="Document Q&A + Appointment Form",
        page_icon="��",
        layout="wide"
    )
    
    st.title("📚 Document Q&A + Appointment Form")
    
    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Document Q&A", "Book Appointment"]
    )
    
    if page == "Document Q&A":
        document_qa_page()
    else:
        appointment_page()

def document_qa_page():
    st.header("Document Q&A")
    
    # File upload section
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files for RAG processing"
    )
    
    if uploaded_files and st.button("🚀 Process Documents"):
        with st.spinner("Processing documents..."):
            try:
                # Prepare files for upload
                files_data = []
                for file in uploaded_files:
                    files_data.append(('files', (file.name, file.getvalue(), file.type)))
                
                # Upload to FastAPI backend
                response = requests.post(
                    f"{BACKEND_URL}/upload-documents",
                    files=files_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    st.write("**Processed files:**", result['files'])
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Error connecting to backend: {str(e)}")
    
    # Chat section
    st.subheader("💬 Ask Questions")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from FastAPI backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/ask",
                        data={"question": prompt}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result['answer']
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Error: {error_msg}")
                        
                except Exception as e:
                    error_msg = f"❌ Error connecting to backend: {str(e)}"
                    st.error(error_msg)

def appointment_page():
    st.header("📅 Book Appointment")
    st.info("This feature will be implemented in the next milestone!")
    
    # Placeholder for appointment form
    st.write("Coming soon: Conversational appointment booking form with date parsing!")

if __name__ == "__main__":
    main()