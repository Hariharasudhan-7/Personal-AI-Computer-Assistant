import os
import warnings

warnings.filterwarnings("ignore")
os.environ["USER_AGENT"] = "RPAnswerBot"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_huggingface_embeddings(model_name: str = "BAAI/bge-small-en-v1.5") -> HuggingFaceEmbeddings:
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={'normalize_embeddings': True}
    )
    
    return embeddings

def get_gemini_embeddings(api_key: str, model_name: str = "models/gemini-embedding-001") -> GoogleGenerativeAIEmbeddings:
    if not api_key:
        raise ValueError("API Key is required for Gemini Embeddings.")
        
    embeddings = GoogleGenerativeAIEmbeddings(
        model=model_name,
        google_api_key=api_key
    )
    return embeddings
