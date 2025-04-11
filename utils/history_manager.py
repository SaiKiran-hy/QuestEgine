import streamlit as st
import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self):
        self.history_dir = "data/history"
        self.bookmarks_file = f"{self.history_dir}/bookmarks.json"
        self.templates_dir = f"{self.history_dir}/templates"
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        self.load_bookmarks()

    def load_bookmarks(self):
        """Load saved bookmarks."""
        if os.path.exists(self.bookmarks_file):
            with open(self.bookmarks_file, 'r') as f:
                st.session_state.bookmarks = json.load(f)
        else:
            st.session_state.bookmarks = []

    def save_bookmark(self, document_info, analysis_info):
        """Save a bookmark for the current document and analysis."""
        bookmark = {
            'id': len(st.session_state.bookmarks),
            'timestamp': datetime.now().isoformat(),
            'document': document_info,
            'analysis': analysis_info
        }
        st.session_state.bookmarks.append(bookmark)
        
        with open(self.bookmarks_file, 'w') as f:
            json.dump(st.session_state.bookmarks, f)
        
        return bookmark['id']

    def remove_bookmark(self, bookmark_id):
        """Remove a saved bookmark."""
        st.session_state.bookmarks = [b for b in st.session_state.bookmarks 
                                    if b['id'] != bookmark_id]
        with open(self.bookmarks_file, 'w') as f:
            json.dump(st.session_state.bookmarks, f)

    def save_analysis_session(self, session_data):
        """Save the current analysis session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.history_dir}/session_{session_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(session_data, f)
        
        return session_id

    def load_analysis_session(self, session_id):
        """Load a saved analysis session."""
        filename = f"{self.history_dir}/session_{session_id}.json"
        with open(filename, 'r') as f:
            return json.load(f)

    def save_query_template(self, template_name, query_config):
        """Save a query template for future use."""
        filename = f"{self.templates_dir}/{template_name}.json"
        with open(filename, 'w') as f:
            json.dump(query_config, f)

    def load_query_template(self, template_name):
        """Load a saved query template."""
        filename = f"{self.templates_dir}/{template_name}.json"
        with open(filename, 'r') as f:
            return json.load(f)

    def get_processing_history(self, document_id):
        """Get the processing history for a specific document."""
        history_file = f"{self.history_dir}/doc_{document_id}_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return []

    def add_to_processing_history(self, document_id, action_data):
        """Add an action to the document's processing history."""
        history_file = f"{self.history_dir}/doc_{document_id}_history.json"
        history = self.get_processing_history(document_id)
        
        action_data['timestamp'] = datetime.now().isoformat()
        history.append(action_data)
        
        with open(history_file, 'w') as f:
            json.dump(history, f)

    def get_favorite_queries(self):
        """Get saved favorite queries."""
        queries_file = f"{self.history_dir}/favorite_queries.json"
        if os.path.exists(queries_file):
            with open(queries_file, 'r') as f:
                return json.load(f)
        return []

    def add_favorite_query(self, query_data):
        """Add a query to favorites."""
        queries = self.get_favorite_queries()
        query_data['id'] = len(queries)
        query_data['timestamp'] = datetime.now().isoformat()
        queries.append(query_data)
        
        queries_file = f"{self.history_dir}/favorite_queries.json"
        with open(queries_file, 'w') as f:
            json.dump(queries, f)
