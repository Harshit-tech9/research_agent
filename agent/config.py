import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL_NAME    = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
TEMPERATURE   = float(os.getenv("TEMPERATURE", "0.2"))
MAX_STEPS     = int(os.getenv("MAX_STEPS", "8"))

MEMORY_STORE_DIR = str(Path(__file__).parent / "memory_store")
EPISODIC_DB_PATH = str(Path(__file__).parent / "episodic_memory.db")
