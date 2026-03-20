"""
Configuration file for the Multi-Agent Research Studio
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file with error handling for encoding issues
try:
    load_dotenv(encoding='utf-8')
except (UnicodeDecodeError, TypeError):
    try:
        load_dotenv()
    except Exception:
        pass

# Groq Configuration
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# LLM Parameters
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# Research Configuration
MAX_RESEARCH_ITERATIONS: int = int(os.getenv("MAX_RESEARCH_ITERATIONS", "5"))
MIN_SOURCES_REQUIRED: int = int(os.getenv("MIN_SOURCES_REQUIRED", "3"))
MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
RESEARCH_DEPTH: str = os.getenv("RESEARCH_DEPTH", "comprehensive")  # quick, standard, comprehensive

# Search Configuration
SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))
ENABLE_WIKIPEDIA: bool = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"

# Quality Thresholds
MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "0.7"))
MIN_SOURCE_CREDIBILITY: float = float(os.getenv("MIN_SOURCE_CREDIBILITY", "0.5"))

# Export Configuration
EXPORT_FORMATS: list = ["markdown", "pdf", "html", "json"]
DEFAULT_EXPORT_FORMAT: str = "markdown"

# UI Configuration
ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_REAL_TIME_UPDATES: bool = os.getenv("ENABLE_REAL_TIME_UPDATES", "true").lower() == "true"

# Research Templates
RESEARCH_TEMPLATES = {
    "academic": {
        "sections": ["Abstract", "Introduction", "Literature Review", "Methodology", "Findings", "Discussion", "Conclusion", "References"],
        "style": "academic"
    },
    "business": {
        "sections": ["Executive Summary", "Introduction", "Market Analysis", "Key Findings", "Recommendations", "Conclusion", "References"],
        "style": "professional"
    },
    "technical": {
        "sections": ["Overview", "Background", "Technical Details", "Implementation", "Results", "Conclusion", "References"],
        "style": "technical"
    },
    "custom": {
        "sections": [],
        "style": "flexible"
    }
}
