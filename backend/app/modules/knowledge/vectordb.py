import chromadb
from chromadb.utils import embedding_functions
from backend.app.core.settings import settings
import os
from pathlib import Path

DB_DIR = str(Path(__file__).parent.parent.parent.parent / "chroma_db")

client = chromadb.PersistentClient(path=DB_DIR)

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.openai_api_key,
    model_name="text-embedding-3-small"
)

surf_collection = client.get_or_create_collection(
    name="surf_safety_rules",
    embedding_function=openai_ef
)

def load_data():
    """Load predefined safety rules into Vector DB"""
    data_path = Path(__file__).parent / "data" / "safety_rules.txt"
    with open(data_path, "r") as f:
        content = f.read()
    
    beaches = content.split("## ")[1:]
    documents = []
    ids = []
    
    for i, beach_text in enumerate(beaches):
        name = beach_text.split("\n")[0].strip()
        documents.append(beach_text)
        ids.append(f"beach_{name.lower().replace(' ', '_')}")
        
    surf_collection.upsert(
        documents=documents,
        ids=ids
    )
    print(f"✅ Loaded {len(documents)} beach rules into Vector DB.")

def search_safety_rules(query: str) -> str:
    """
    Search the Vector DB for safety rules about a specific beach or condition.
    Use this tool when evaluating if a beach is safe for a surfer's skill level.
    """
    results = surf_collection.query(
        query_texts=[query],
        n_results=1
    )
    
    if results['documents'] and results['documents'][0]:
        return results['documents'][0][0]
    return "No safety rules found in database."

if __name__ == "__main__":
    load_data()
