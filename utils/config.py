import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MAX_FILE_SIZE_MB = 10
    SUPPORTED_FILE_TYPES = ["pdf", "csv", "docx", "txt"]
    CHUNK_SIZE = 10000
    MAX_TOKENS = 30000
    MODEL_NAME = "gemini-1.5-flash"  # Updated to use the latest free model
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"