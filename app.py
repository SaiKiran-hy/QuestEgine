import streamlit as st
from dotenv import load_dotenv
import os
import time
from utils.file_handler import (
    handle_file_upload,
    extract_text_from_file,
    get_file_preview
)
from utils.question_answering import (
    setup_gemini_model,
    generate_answer,
    summarize_document,
    extract_key_points
)
from utils.visualizations import (
    generate_dataframe_preview,
    create_visualization
)
from utils.config import Config
from utils.text_processing import highlight_key_sections
import pandas as pd

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Quest Engine AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state
def init_session_state():
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}
    if "current_file" not in st.session_state:
        st.session_state.current_file = None
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if "model_status" not in st.session_state:
        st.session_state.model_status = "not_initialized"

init_session_state()

# Initialize Gemini model
if st.session_state.model_status == "not_initialized":
    try:
        st.session_state.gemini_model = setup_gemini_model()
        if st.session_state.gemini_model is not None:
            st.session_state.model_status = "initialized"
            st.success("App initialized successfully!")
        else:
            st.session_state.model_status = "failed"
            st.warning("Using fallback API mode - some features may be limited")
    except Exception as e:
        st.session_state.model_status = "failed"
        st.error(f"Failed to initialize Gemini model: {str(e)} - Using fallback API mode")

# Sidebar for file upload and navigation
with st.sidebar:
    st.title("📂 Document Analysis")
    st.markdown("Upload your documents and analyze their content with AI.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload files (PDF, CSV, DOCX, TXT)",
        type=["pdf", "csv", "docx", "txt"],
        accept_multiple_files=True
    )
    
    # Process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        file_info = handle_file_upload(uploaded_file)
                        st.session_state.uploaded_files[uploaded_file.name] = file_info
                        st.session_state.chat_history[uploaded_file.name] = []
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        # File selection dropdown
        file_names = list(st.session_state.uploaded_files.keys())
        selected_file = st.selectbox(
            "Select a file to analyze",
            file_names,
            index=file_names.index(st.session_state.current_file) if st.session_state.current_file else 0
        )
        
        if selected_file != st.session_state.current_file:
            st.session_state.current_file = selected_file
            st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app uses AI to analyze your documents and answer questions about their content.")
    
    # Add feedback link
    st.markdown("---")
    st.markdown("### Feedback")
    st.markdown("<a href='https://forms.gle/7vCLqrfDcyUZS7Ne7' target='_blank'>📝 Give your feedback</a>", unsafe_allow_html=True)
    
    # Model status indicator
    st.markdown("---")
    if st.session_state.model_status == "initialized":
        st.success("✓ Gemini model active")
    elif st.session_state.model_status == "failed":
        st.warning("⚠ Using fallback API mode")

# Main content area
if st.session_state.uploaded_files and st.session_state.current_file:
    current_file_info = st.session_state.uploaded_files[st.session_state.current_file]
    
    # Display file info and preview
    st.header(f"📄 {st.session_state.current_file}")
    st.caption(f"File type: {current_file_info['type']} | Size: {current_file_info['size']} KB")
    
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Preview", "Ask Questions", "Visualize", "Summary"])
    
    with tab1:
        # File preview section
        st.subheader("File Preview")
        preview_content = get_file_preview(current_file_info)
        
        if current_file_info["type"] == "csv":
            st.dataframe(preview_content, use_container_width=True)
        else:
            st.markdown(preview_content, unsafe_allow_html=True)
    
    with tab2:
        # Question answering section
        st.subheader("Ask Questions About the Document")
        
        # Display chat history
        chat_container = st.container(height=400, border=True)
        
        with chat_container:
            for message in st.session_state.chat_history[st.session_state.current_file]:
                if message["role"] == "user":
                    st.chat_message("user").markdown(f"*You:* {message['content']}")
                else:
                    st.chat_message("assistant").markdown(f"*AI:* {message['content']}")
        
        # User input
        question = st.chat_input("Ask a question about the document...")
        
        if question:
            # Add user question to chat history
            st.session_state.chat_history[st.session_state.current_file].append({
                "role": "user",
                "content": question
            })
            
            # Generate answer
            with st.spinner("Analyzing document..."):
                try:
                    answer = generate_answer(
                        st.session_state.gemini_model,
                        current_file_info["content"],
                        question,
                        st.session_state.current_file
                    )
                    
                    # Add AI response to chat history
                    st.session_state.chat_history[st.session_state.current_file].append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                    # Rerun to update the chat display
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
                    st.session_state.chat_history[st.session_state.current_file].append({
                        "role": "assistant",
                        "content": "Sorry, I encountered an error processing your request. Please try again."
                    })
                    st.rerun()
    
    with tab3:
        # Data visualization section (for CSV files)
        st.subheader("Data Visualization")
        
        if current_file_info["type"] == "csv":
            try:
                df = pd.read_csv(current_file_info["path"])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    chart_type = st.selectbox(
                        "Select chart type",
                        ["Bar", "Line", "Scatter", "Pie", "Histogram"]
                    )
                
                with col2:
                    if chart_type in ["Bar", "Line", "Scatter"]:
                        x_axis = st.selectbox("X-axis", df.columns)
                        y_axis = st.selectbox("Y-axis", df.columns)
                    elif chart_type == "Pie":
                        x_axis = st.selectbox("Category", df.columns)
                        y_axis = st.selectbox("Values", df.columns)
                    else:  # Histogram
                        x_axis = st.selectbox("Column", df.columns)
                        y_axis = None
                
                if st.button("Generate Visualization"):
                    try:
                        fig = create_visualization(
                            df,
                            chart_type.lower(),
                            x_axis,
                            y_axis if chart_type != "Histogram" else None
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating visualization: {str(e)}")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
        else:
            st.warning("Visualizations are only available for CSV files.")
    
    with tab4:
        # Document summary and key points
        st.subheader("Document Summary")
        
        with st.spinner("Generating summary..."):
            try:
                summary = summarize_document(
                    st.session_state.gemini_model,
                    current_file_info["content"]
                )
                st.markdown(summary)
            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")
        
        st.subheader("Key Points")
        
        with st.spinner("Extracting key points..."):
            try:
                key_points = extract_key_points(
                    st.session_state.gemini_model,
                    current_file_info["content"]
                )
                st.markdown(key_points)
            except Exception as e:
                st.error(f"Error extracting key points: {str(e)}")
        
        if current_file_info["type"] != "csv":
            st.subheader("Important Sections")
            try:
                highlighted_text = highlight_key_sections(current_file_info["content"])
                st.markdown(highlighted_text, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error highlighting text: {str(e)}")

else:
    # Welcome screen when no files are uploaded
    st.title("Quest Engine")
    st.markdown("""
    ### Upload your documents to get started
    This app allows you to:
    - Upload various file types (PDF, CSV, DOCX, TXT)
    - Preview file contents
    - Ask questions about the documents
    - Visualize data (for CSV files)
    - Get summaries and key points
    
    *How to use:*
    1. Upload one or more files using the sidebar
    2. Select a file to analyze
    3. Explore the different tabs to interact with your document
    """)
    
    # Replace the placeholder image with an SVG icon
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" rx="20" fill="#2b5876"/>
            <path d="M50 70L100 120L150 70" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
            <path d="M50 100L100 150L150 100" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
        </svg>
    </div>
    """, unsafe_allow_html=True)