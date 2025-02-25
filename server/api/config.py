import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = "isef-project"
    PINECONE_NAMESPACE: str = "task-commands"
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = ["*"]

settings = Settings()
