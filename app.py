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
    extract_key_points,
    generate_questions
)
from utils.visualizations import (
    generate_dataframe_preview,
    create_visualization
)
from utils.config import Config
from utils.text_processing import highlight_key_sections
import pandas as pd
import tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

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
    # Removed active_tab from session state as it's causing issues

init_session_state()

# Function to convert CSV to PDF
def convert_csv_to_pdf(df, filename):
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title = Paragraph(f"CSV Data: {filename}", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Add description
    description = Paragraph("This PDF contains the data from the CSV file in a tabular format", styles['Normal'])
    elements.append(description)
    elements.append(Spacer(1, 20))
    
    # Prepare data for table
    # Limit rows to prevent extremely large PDFs
    max_rows = 100
    if len(df) > max_rows:
        data_preview = df.head(max_rows).values.tolist()
        preview_note = Paragraph(f"Note: Showing first {max_rows} rows of {len(df)} total rows", styles['Italic'])
        elements.append(preview_note)
        elements.append(Spacer(1, 10))
    else:
        data_preview = df.values.tolist()
    
    # Add headers
    data = [df.columns.tolist()] + data_preview
    
    # Create table
    table = Table(data)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    # Add row coloring for readability
    for row in range(1, len(data)):
        if row % 2 == 0:
            style.add('BACKGROUND', (0, row), (-1, row), colors.whitesmoke)
    
    table.setStyle(style)
    
    # Add table to elements
    elements.append(table)
    
    # Add dataset statistics
    elements.append(Spacer(1, 30))
    stats_title = Paragraph("Dataset Statistics", styles['Heading2'])
    elements.append(stats_title)
    elements.append(Spacer(1, 10))
    
    # Get basic statistics for numeric columns
    try:
        numeric_stats = df.describe().reset_index()
        numeric_stats = numeric_stats.rename(columns={'index': 'Statistic'})
        stats_data = [numeric_stats.columns.tolist()]
        stats_data.extend(numeric_stats.values.tolist())
        
        stats_table = Table(stats_data)
        stats_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        stats_table.setStyle(stats_style)
        elements.append(stats_table)
    except Exception as e:
        elements.append(Paragraph(f"Could not generate statistics: {str(e)}", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

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
        error_message = str(e)
        if "API_KEY_INVALID" in error_message or "API key expired" in error_message:
            st.error("❌ API key expired or invalid. Please check your .env file and update your GOOGLE_API_KEY.")
            st.info("You can get a new API key from https://aistudio.google.com/app/apikey")
        else:
            st.error(f"Failed to initialize Gemini model: {error_message} - Using fallback API mode")

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
        st.success("✓ Quest Engine active")
    elif st.session_state.model_status == "failed":
        st.warning("⚠ AI features limited - API key issue")

# Main content area
if st.session_state.uploaded_files and st.session_state.current_file:
    current_file_info = st.session_state.uploaded_files[st.session_state.current_file]
    
    # Display file info and preview
    st.header(f"📄 {st.session_state.current_file}")
    st.caption(f"File type: {current_file_info['type']} | Size: {current_file_info['size']} KB")
    
    # Tabs for different functionalities 
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Preview", "Ask Questions", "Visualize", "Summary", "Generated Questions", "Export as PDF"])
    
    # Removed the problematic active_tab_index setting
    
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
                    st.chat_message("assistant").markdown(f"*QuestEngine:* {message['content']}")
        
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
                    if st.session_state.model_status == "failed":
                        raise Exception("API key issue - Please check your Google API key in the .env file")
                        
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
                    error_message = str(e)
                    if "API_KEY_INVALID" in error_message or "API key expired" in error_message:
                        error_display = "API key expired or invalid. Please update your API key in the .env file."
                    else:
                        error_display = f"Error generating answer: {error_message}"
                    
                    st.session_state.chat_history[st.session_state.current_file].append({
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {error_display}"
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
        
        if st.button("Generate Summary", key="generate_summary"):
            with st.spinner("Generating summary..."):
                try:
                    if st.session_state.model_status == "failed":
                        st.error("API key issue - Please check your Google API key in the .env file")
                    else:
                        summary = summarize_document(
                            st.session_state.gemini_model,
                            current_file_info["content"]
                        )
                        st.markdown(summary)
                        
                        # Add download button for summary
                        if summary:
                            summary_filename = f"{st.session_state.current_file.split('.')[0]}_summary.txt"
                            st.download_button(
                                label="📥 Download Summary",
                                data=summary,
                                file_name=summary_filename,
                                mime="text/plain"
                            )
                except Exception as e:
                    error_message = str(e)
                    if "API_KEY_INVALID" in error_message or "API key expired" in error_message:
                        st.error("API key expired or invalid. Please update your API key in the .env file.")
                    else:
                        st.error(f"Error generating summary: {error_message}")
        
        st.subheader("Key Points")
        
        if st.button("Extract Key Points", key="extract_key_points"):
            with st.spinner("Extracting key points..."):
                try:
                    if st.session_state.model_status == "failed":
                        st.error("API key issue - Please check your Google API key in the .env file")
                    else:
                        key_points = extract_key_points(
                            st.session_state.gemini_model,
                            current_file_info["content"]
                        )
                        st.markdown(key_points)
                except Exception as e:
                    error_message = str(e)
                    if "API_KEY_INVALID" in error_message or "API key expired" in error_message:
                        st.error("API key expired or invalid. Please update your API key in the .env file.")
                    else:
                        st.error(f"Error extracting key points: {error_message}")
        
        if current_file_info["type"] != "csv":
            st.subheader("Important Sections")
            if st.button("Highlight Important Sections", key="highlight_sections"):
                try:
                    highlighted_text = highlight_key_sections(current_file_info["content"])
                    st.markdown(highlighted_text, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error highlighting text: {str(e)}")
    
    with tab5:
        # Generated Questions tab with Ask button removed
        st.subheader("Questions Generated from Document")
        
        if st.button("Generate Questions"):
            with st.spinner("Generating questions from document..."):
                try:
                    if st.session_state.model_status == "failed":
                        st.error("API key issue - Please check your Google API key in the .env file")
                    else:
                        questions = generate_questions(
                            st.session_state.gemini_model,
                            current_file_info["content"]
                        )
                        
                        if questions:
                            for i, question in enumerate(questions, 1):
                                st.write(f"**{i}.** {question}")
                            
                            # Add download button for generated questions
                            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
                            questions_filename = f"{st.session_state.current_file.split('.')[0]}_questions.txt"
                            st.download_button(
                                label="📥 Download Questions",
                                data=questions_text,
                                file_name=questions_filename,
                                mime="text/plain"
                            )
                except Exception as e:
                    error_message = str(e)
                    if "API_KEY_INVALID" in error_message or "API key expired" in error_message:
                        st.error("API key expired or invalid. Please update your API key in the .env file.")
                    else:
                        st.error(f"Error generating questions: {error_message}")
    
    with tab6:
        # Export as PDF section
        st.subheader("Export as PDF")
        
        if current_file_info["type"] == "csv":
            st.info("Convert your CSV data to a formatted PDF document for better readability.")
            
            # Options for PDF customization
            st.subheader("PDF Export Options")
            
            col1, col2 = st.columns(2)
            with col1:
                include_stats = st.checkbox("Include statistics", value=True)
            with col2:
                max_rows = st.number_input("Maximum rows to include (0 for all)", 
                                          min_value=0, max_value=1000, value=100)
            
            if st.button("Generate PDF"):
                with st.spinner("Creating PDF document..."):
                    try:
                        # Read CSV file
                        df = pd.read_csv(current_file_info["path"])
                        
                        # Generate PDF
                        pdf_buffer = convert_csv_to_pdf(df, st.session_state.current_file)
                        
                        # Display success message
                        st.success("PDF generated successfully!")
                        
                        # Provide download button
                        pdf_filename = f"{st.session_state.current_file.split('.')[0]}.pdf"
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_buffer,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                        
                        # Display preview info
                        st.info("The PDF contains a formatted table of your CSV data with headers, row styling, and basic statistics.")
                        
                    except Exception as e:
                        st.error(f"Error creating PDF: {str(e)}")
        else:
            st.warning("PDF export is currently only available for CSV files.")
            st.info("Upload a CSV file to use this feature.")

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
    - Generate questions from documents
    - Download summaries and generated questions
    - Export CSV data as formatted PDF documents
    
    *How to use:*
    1. Upload one or more files using the sidebar
    2. Select a file to analyze
    3. Explore the different tabs to interact with your document
    """)