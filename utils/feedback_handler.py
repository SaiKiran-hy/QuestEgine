# utils/feedback_handler.py

import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

class FeedbackHandler:
    def __init__(self):
        self.questions = [
            "How would you rate the overall usability of the app? (1-5)",
            "How satisfied are you with the document analysis features? (1-5)",
            "How accurate were the AI-generated answers to your questions? (1-5)",
            "How useful were the document summaries and key points? (1-5)",
            "How intuitive was the user interface? (1-5)",
            "How would you rate the visualization capabilities? (1-5)",
            "How likely are you to recommend this app to others? (1-5)",
            "What features would you like to see added to the app?",
            "What aspects of the app need improvement?",
            "Any additional comments or suggestions?"
        ]
        
    def create_feedback_form(self):
        """Create and display the feedback form"""
        st.header("📝 We Value Your Feedback")
        st.markdown("Please take a moment to share your thoughts about Quest Engine")
        
        with st.form("feedback_form"):
            # User info
            user_email = st.text_input("Email (optional)")
            user_role = st.selectbox(
                "What best describes your role?",
                ["Student", "Researcher", "Data Analyst", "Manager", "Developer", "Educator", "Other"]
            )
            
            # Rating questions
            ratings = {}
            for i, question in enumerate(self.questions[:7]):  # First 7 questions are ratings
                ratings[f"rating_{i+1}"] = st.slider(
                    question, 
                    min_value=1, 
                    max_value=5, 
                    value=3,
                    key=f"rating_q{i+1}"
                )
            
            # Open-ended questions
            feature_requests = st.text_area(self.questions[7])  # What features would you like to see added
            improvement_suggestions = st.text_area(self.questions[8])  # What aspects need improvement
            additional_comments = st.text_area(self.questions[9])  # Additional comments
            
            # Submit button
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                try:
                    # Collect feedback data
                    feedback_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "email": user_email,
                        "role": user_role,
                    }
                    
                    # Add ratings
                    for i, question in enumerate(self.questions[:7]):
                        feedback_data[f"q{i+1}_rating"] = ratings[f"rating_{i+1}"]
                    
                    # Add text responses
                    feedback_data["feature_requests"] = feature_requests
                    feedback_data["improvement_suggestions"] = improvement_suggestions
                    feedback_data["additional_comments"] = additional_comments
                    
                    # Send to Google Sheets
                    success = self.submit_to_google_sheet(feedback_data)
                    
                    if success:
                        st.success("Thank you for your feedback! We appreciate your input.")
                        # Return True to indicate successful submission
                        return True
                    else:
                        st.error("There was an issue submitting your feedback. Please try again later.")
                        return False
                        
                except Exception as e:
                    st.error(f"Error submitting feedback: {str(e)}")
                    return False
            
            return False
    
    def submit_to_google_sheet(self, feedback_data):
        """Submit feedback data to Google Sheet"""
        try:
            # Create a connection object using the service account credentials
            # Note: You'll need to set up a Google service account and save the credentials
            # in a file like 'google_credentials.json' and add it to your project
            credentials = service_account.Credentials.from_service_account_file(
                'google_credentials.json',
                scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            )
            
            # Connect to Google Sheets
            gc = gspread.authorize(credentials)
            
            # Open the Google Sheet - replace with your Google Sheet ID
            sheet = gc.open_by_key('YOUR_GOOGLE_SHEET_ID').sheet1
            
            # Prepare data row
            row_data = [
                feedback_data["timestamp"],
                feedback_data["email"],
                feedback_data["role"],
                feedback_data["q1_rating"],
                feedback_data["q2_rating"],
                feedback_data["q3_rating"],
                feedback_data["q4_rating"],
                feedback_data["q5_rating"],
                feedback_data["q6_rating"],
                feedback_data["q7_rating"],
                feedback_data["feature_requests"],
                feedback_data["improvement_suggestions"],
                feedback_data["additional_comments"]
            ]
            
            # Append the data
            sheet.append_row(row_data)
            
            # Save feedback to local storage as backup
            self.save_local_backup(feedback_data)
            
            return True
            
        except Exception as e:
            st.error(f"Error connecting to Google Sheets: {str(e)}")
            # Still save locally as backup
            self.save_local_backup(feedback_data)
            return False
    
    def save_local_backup(self, feedback_data):
        """Save feedback to local CSV as backup"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([feedback_data])
            
            # Create or append to CSV
            try:
                existing_df = pd.read_csv('feedback_backup.csv')
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_csv('feedback_backup.csv', index=False)
            except FileNotFoundError:
                df.to_csv('feedback_backup.csv', index=False)
                
        except Exception as e:
            st.warning(f"Could not save local backup: {str(e)}")