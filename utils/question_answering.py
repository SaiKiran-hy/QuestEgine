import google.generativeai as genai
from utils.config import Config
from typing import Optional
import tiktoken
import requests
import json
import re

def setup_gemini_model():
    """Initialize and return the Gemini model with fallback to free endpoint."""
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        return genai.GenerativeModel(Config.MODEL_NAME)
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        return None

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def chunk_text(text: str, max_tokens: int = Config.MAX_TOKENS) -> list:
    """Split text into chunks that are within the token limit."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for token in tokens:
        if current_token_count + 1 > max_tokens:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = [token]
            current_token_count = 1
        else:
            current_chunk.append(token)
            current_token_count += 1
    
    if current_chunk:
        chunks.append(encoding.decode(current_chunk))
    
    return chunks

def generate_answer_with_fallback(prompt: str) -> str:
    """Generate answer using free API endpoint if direct model fails."""
    try:
        url = f"{Config.BASE_URL}{Config.MODEL_NAME}:generateContent?key={Config.GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "Sorry, I couldn't generate a response. Please try again."
    except Exception as e:
        return f"API Error: {str(e)}"

def generate_answer(model, document_text: str, question: str, filename: Optional[str] = None) -> str:
    """Generate an answer to a question about the document content."""
    try:
        # Chunk the document if it's too large
        if count_tokens(document_text) > Config.MAX_TOKENS:
            chunks = chunk_text(document_text)
            responses = []
            
            for chunk in chunks:
                prompt = f"""
                Document Analysis Task:
                File: {filename}
                Content Portion:
                {chunk}
                
                Question: {question}
                
                Please provide a concise answer based on the document content.
                If the answer isn't in this portion, say so.
                """
                
                if model:
                    response = model.generate_content(prompt)
                    responses.append(response.text)
                else:
                    responses.append(generate_answer_with_fallback(prompt))
            
            # Combine responses
            combined_response = "\n\n".join(responses)
            
            # Summarize the combined responses
            summary_prompt = f"""
            Combine these partial answers into one coherent response:
            
            {combined_response}
            
            Question: {question}
            
            Provide a single, clear answer that combines the most relevant information.
            """
            
            if model:
                final_response = model.generate_content(summary_prompt)
                return final_response.text
            return generate_answer_with_fallback(summary_prompt)
        else:
            prompt = f"""
            Document Analysis Task:
            File: {filename}
            Full Content:
            {document_text}
            
            Question: {question}
            
            Please provide a concise answer based on the document content.
            """
            
            if model:
                response = model.generate_content(prompt)
                return response.text
            return generate_answer_with_fallback(prompt)
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def summarize_document(model, document_text: str) -> str:
    """Generate a summary of the document."""
    try:
        if count_tokens(document_text) > Config.MAX_TOKENS:
            chunks = chunk_text(document_text)
            summaries = []
            
            for chunk in chunks:
                prompt = f"""
                Please summarize this document portion:
                {chunk}
                
                Focus on key points and main ideas.
                """
                
                if model:
                    response = model.generate_content(prompt)
                    summaries.append(response.text)
                else:
                    summaries.append(generate_answer_with_fallback(prompt))
            
            # Combine summaries
            combined_summary = "\n\n".join(summaries)
            
            # Create a final summary
            summary_prompt = f"""
            Combine these partial summaries into one coherent summary:
            {combined_summary}
            
            Keep it concise (3-5 sentences) focusing on key points.
            """
            
            if model:
                final_summary = model.generate_content(summary_prompt)
                return final_summary.text
            return generate_answer_with_fallback(summary_prompt)
        else:
            prompt = f"""
            Please summarize this document:
            {document_text}
            
            Keep it concise (3-5 sentences) focusing on key points.
            """
            
            if model:
                response = model.generate_content(prompt)
                return response.text
            return generate_answer_with_fallback(prompt)
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def extract_key_points(model, document_text: str) -> str:
    """Extract key points from the document."""
    try:
        if count_tokens(document_text) > Config.MAX_TOKENS:
            chunks = chunk_text(document_text)
            key_points = []
            
            for chunk in chunks:
                prompt = f"""
                Extract key points from this document portion:
                {chunk}
                
                Return as a bulleted list of important ideas.
                """
                
                if model:
                    response = model.generate_content(prompt)
                    key_points.append(response.text)
                else:
                    key_points.append(generate_answer_with_fallback(prompt))
            
            # Combine key points
            combined_points = "\n\n".join(key_points)
            
            # Deduplicate and organize key points
            organize_prompt = f"""
            Combine these key points into one organized list:
            {combined_points}
            
            Remove duplicates and group related points.
            """
            
            if model:
                final_points = model.generate_content(organize_prompt)
                return final_points.text
            return generate_answer_with_fallback(organize_prompt)
        else:
            prompt = f"""
            Extract key points from this document:
            {document_text}
            
            Return as a bulleted list of important ideas.
            """
            
            if model:
                response = model.generate_content(prompt)
                return response.text
            return generate_answer_with_fallback(prompt)
    except Exception as e:
        return f"Error extracting key points: {str(e)}"

def generate_questions(model, document_text: str) -> list:
    """Generate relevant questions from the document content."""
    try:
        if count_tokens(document_text) > Config.MAX_TOKENS:
            chunks = chunk_text(document_text)
            all_questions = []
            
            for chunk in chunks:
                prompt = f"""
                Based on the following document content, generate 3-5 relevant and insightful questions
                that someone might want to ask about this information. Make the questions diverse,
                covering different aspects of the content.
                
                Document Content:
                {chunk}
                
                Return just the numbered questions without any additional text or explanations.
                """
                
                if model:
                    response = model.generate_content(prompt)
                    all_questions.append(response.text)
                else:
                    all_questions.append(generate_answer_with_fallback(prompt))
            
            # Combine and deduplicate questions
            combined_questions = "\n".join(all_questions)
            
            dedup_prompt = f"""
            Here are several sets of questions generated from different parts of a document:
            
            {combined_questions}
            
            Please review these questions, remove duplicates, and provide a final list of 
            10 unique and diverse questions that cover the main topics in the document.
            Return just the numbered questions without any additional text.
            """
            
            if model:
                final_questions = model.generate_content(dedup_prompt)
                # Parse questions into a list
                questions_list = final_questions.text.strip().split('\n')
                # Clean up numbering and any extra text
                clean_questions = [q.strip() for q in questions_list if q.strip()]
                clean_questions = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in clean_questions if re.search(r'\w', q)]
                return clean_questions
            
            fallback_response = generate_answer_with_fallback(dedup_prompt)
            questions_list = fallback_response.strip().split('\n')
            clean_questions = [q.strip() for q in questions_list if q.strip()]
            clean_questions = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in clean_questions if re.search(r'\w', q)]
            return clean_questions
                
        else:
            prompt = f"""
            Based on the following document content, generate 10 relevant and insightful questions
            that someone might want to ask about this information. Make the questions diverse,
            covering different aspects of the content.
            
            Document Content:
            {document_text}
            
            Return just the numbered questions without any additional text or explanations.
            """
            
            if model:
                response = model.generate_content(prompt)
                # Parse questions into a list
                questions_list = response.text.strip().split('\n')
                # Clean up numbering and any extra text
                clean_questions = [q.strip() for q in questions_list if q.strip()]
                clean_questions = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in clean_questions if re.search(r'\w', q)]
                return clean_questions
            
            fallback_response = generate_answer_with_fallback(prompt)
            questions_list = fallback_response.strip().split('\n')
            clean_questions = [q.strip() for q in questions_list if q.strip()]
            clean_questions = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in clean_questions if re.search(r'\w', q)]
            return clean_questions
    except Exception as e:
        return [f"Error generating questions: {str(e)}"]