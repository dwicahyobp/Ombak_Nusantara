from mcp.server.fastmcp import FastMCP
from backend.app.modules.knowledge.vectordb import search_safety_rules


mcp = FastMCP(
    "Ombak Nusantara Community Server",
    dependencies=["chromadb", "openai"]
)

@mcp.tool()
def get_beach_safety_info(beach_name: str) -> str:
    """
    Dapatkan panduan keselamatan dan peringatan karang untuk pantai surfing di Indonesia.
    Tool ini digunakan oleh bot komunitas (misal Discord/Telegram) untuk mendapatkan informasi
    dari Knowledge Base (Vector DB) Ombak Nusantara.
    """

    result = search_safety_rules(beach_name)
    
    return f"🌊 Laporan Keselamatan {beach_name.upper()} (Sumber: Ombak Nusantara)\n{'-'*50}\n{result}"

@mcp.tool()
def get_available_beaches() -> str:
    """Lihat daftar pantai yang saat ini datanya tersedia di Ombak Nusantara."""
    return "Pantai yang didukung: Kuta, Batu Bolong, Uluwatu, Padang Padang, Desert Point."

if __name__ == "__main__":
    mcp.run()
