# Ombak Nusantara - Final Project

This is a complete end-to-end application built for the Final Project, fulfilling all the technical requirements for an AI-powered agentic system.

## 🌟 Features & Technical Checklist

✅ **Technology Stack**
- **FastAPI**: Main web framework serving the API and Frontend.
- **SQLModel & Alembic**: ORM and migrations managing `User`, `SurfPlan`, and `SurfReport` models.
- **Celery & Redis**: Background worker task queue for heavy deep research processes.
- **SQLite**: Local database for persistence.
- **Frontend**: A sleek, dark-mode Vanilla JS + HTML + CSS UI built from scratch to act as the web interface.

✅ **AI & Agents**
- **LLM Model**: Powered by OpenAI `gpt-4o`.
- **Agents with Tools**: Uses `TavilyTools` for live web search and custom ChromaDB tools.
- **MCP (Model Context Protocol)**: Standalone FastMCP server running in `backend/app/modules/mcp/server.py` exposing safety database as tools.
- **Vector DB (Embeddings)**: `ChromaDB` initialized with OpenAI `text-embedding-3-small` used for retrieval.
- **Sub-Agents**: Implemented `Surf Report Sub-Agent` and `Surf Plan Sub-Agent` in `agents.py`.
- **Agentic Workflow**: A Supervisor Team agent intelligently orchestrates the sub-agents and synthesizes final responses based on user profiles.

## 🚀 How to Run the Application

The application consists of multiple components. Follow these steps to start them all:

### 1. Start the API Server & Frontend
This starts the main FastAPI server which also serves the Web UI.
```bash
make dev
# Open http://127.0.0.1:8000 in your browser for the Web UI.
```

### 2. Start the Celery Worker
(Ensure you have `redis-server` running in the background on port 6379)
Open a new terminal and run:
```bash
make worker
```

### 3. Run the MCP Server
To expose the knowledge base as an MCP server over stdio (compatible with Claude Desktop):
```bash
uv run python -m backend.app.modules.mcp.server
```

## 🛠 Project Structure
- `backend/app/main.py` - FastAPI entry point.
- `backend/app/modules/surf/agents.py` - Swarm and Sub-Agent definition.
- `backend/app/modules/knowledge/vectordb.py` - ChromaDB implementation.
- `backend/app/modules/mcp/server.py` - FastMCP Server.
- `backend/app/modules/research/tasks.py` - Celery Tasks for deep web search.
- `frontend/` - HTML, CSS, JS files for the sleek user interface.
- `.codex/AGENTS.md` - Documentation of the agentic workflow architecture.
