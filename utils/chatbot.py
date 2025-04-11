import streamlit as st
from .question_answering import generate_answer

def show_chat_interface():
    """
    Display the global chat interface for interacting with the AI assistant.
    """
    st.title("🤖 Global Chat")
    st.markdown("Ask me anything about your documents or have a general conversation.")

    # Initialize chat history for global chat if not exists
    if "global_chat_history" not in st.session_state:
        st.session_state.global_chat_history = []

    # Display chat history
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for message in st.session_state.global_chat_history:
            if message["role"] == "user":
                st.chat_message("user").markdown(f"**You:** {message['content']}")
            else:
                st.chat_message("assistant").markdown(f"**AI:** {message['content']}")

    # User input
    question = st.chat_input("Ask a question...")

    if question:
        # Add user question to chat history
        st.session_state.global_chat_history.append({
            "role": "user",
            "content": question
        })

        try:
            # Generate response using the model
            response = generate_answer(
                st.session_state.gemini_model,
                question,
                context="This is a global chat conversation without specific document context."
            )

            # Add AI response to chat history
            st.session_state.global_chat_history.append({
                "role": "assistant",
                "content": response
            })
            st.rerun()

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            st.session_state.global_chat_history.append({
                "role": "assistant",
                "content": "Sorry, I encountered an error processing your request. Please try again."
            })
            st.rerun()
