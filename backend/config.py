import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    PORT = int(os.getenv('PORT', 5000))
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
