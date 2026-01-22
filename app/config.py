import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
SCHEME_JSON_PATH = os.getenv("SCHEME_JSON_PATH", "data/final_structured_schemes.json")
