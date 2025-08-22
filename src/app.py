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
    if prompt := st.chat_input("Ask a question about your documents or request a booking..."):
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

                        # If the assistant indicates it needs info, show form prompt
                        if result.get("needs_info"):
                            form_prompt = result.get("form_prompt")
                            if form_prompt:
                                st.info(form_prompt)
                                st.session_state.messages.append({"role": "assistant", "content": form_prompt})

                        # If form completed, display summary
                        if result.get("form_complete"):
                            data = result.get("form_data", {})
                            st.success("Appointment details collected:")
                            st.json(data)
                    else:
                        error_msg = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Error: {error_msg}")
                        
                except Exception as e:
                    error_msg = f"❌ Error connecting to backend: {str(e)}"
                    st.error(error_msg)

def appointment_page():
    st.header("📅 Book Appointment")
    st.subheader("Your Appointments")

    # Try both possible locations
    candidates = [
        os.path.join(os.getcwd(), "appointments", "bookings.jsonl"),
        os.path.join(os.getcwd(), "src", "appointments", "bookings.jsonl"),
    ]

    bookings_path = None
    for p in candidates:
        if os.path.exists(p):
            bookings_path = p
            break

    if not bookings_path:
        st.info("No bookings found yet.")
        st.caption("Bookings will appear here after you complete the chat-based appointment form.")
        return

    # Load JSONL
    records = []
    try:
        with open(bookings_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json
                    rec = json.loads(line)
                    records.append(rec)
                except Exception:
                    continue
    except Exception as e:
        st.error(f"Failed to read bookings: {e}")
        return

    if not records:
        st.info("No bookings found in the file yet.")
        return

    # Simple filters
    with st.expander("Filters", expanded=False):
        name_filter = st.text_input("Filter by name contains")
        email_filter = st.text_input("Filter by email contains")
        date_filter = st.text_input("Filter by date (YYYY-MM-DD)")

    def match(rec):
        ok = True
        if name_filter:
            ok = ok and (name_filter.lower() in str(rec.get("name", "")).lower())
        if email_filter:
            ok = ok and (email_filter.lower() in str(rec.get("email", "")).lower())
        if date_filter:
            ok = ok and (date_filter in str(rec.get("preferred_datetime", "")))
        return ok

    filtered = [r for r in records if match(r)]

    # Sort newest first by created_utc if available
    try:
        filtered.sort(key=lambda r: r.get("created_utc", ""), reverse=True)
    except Exception:
        pass

    # Display
    for rec in filtered:
        with st.container(border=True):
            st.write(f"**Confirmation**: {rec.get('id', 'N/A')}")
            st.write(f"**Name**: {rec.get('name', '')}")
            st.write(f"**Phone**: {rec.get('phone', '')}")
            st.write(f"**Email**: {rec.get('email', '')}")
            st.write(f"**Preferred**: {rec.get('preferred_datetime', '')}")
            notes = rec.get('notes')
            if notes:
                st.write(f"**Notes**: {notes}")
            st.caption(f"Created: {rec.get('created_utc', '')}")

if __name__ == "__main__":
    main()