from backend.app.core.settings import settings
from openai import OpenAI
from tavily import TavilyClient

if not settings.openai_api_key or not settings.tavily_api_key:
    raise ValueError("⚠️ Attention, OpenAI API Key atau Tavily API Key belum diisi di file .env!")

oai_client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=120.0  # Increased timeout from default 60s to 120s
)
tavily_client = TavilyClient(api_key=settings.tavily_api_key)
