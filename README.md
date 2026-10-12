# Ombak Nusantara 🌊

An AI-powered surf community and trip-planning app for Indonesian surf spots. Surfers can generate a personalised surf plan (conditions, safety status, gear, stay and itinerary), share sessions, report hazards, and trade gear with the community.

Built as the final exam project of the **Devscale AI-Enabled Python Web Development Bootcamp**.

## Features

- **Surf Planner**: pick a spot, date, and preferred time; a multi-agent system researches live conditions and local safety rules, then returns a structured plan. Every plan is saved to **My Surf Plans**.
- **Session Feed**: photo/video posts with likes, comments, @mentions, notifications, and one-click translation.
- **Community**: discussion threads, a gear marketplace, and meetups.
- **Hazard Alerts**: community-reported hazards with severity, location, and media.
- **Dashboard & Map**: today's surf summary for the selected spot, spot map, and live cams.

## AI architecture

| Piece | Implementation |
| --- | --- |
| Framework | [Agno](https://www.agno.com/) agents with OpenAI `gpt-4o` |
| Agentic workflow | A **Supervisor** team agent orchestrates the sub-agents and writes the final report, adapted to the user's profile |
| Sub-agents | **Surf Report Sub-Agent** (live web search via Tavily) and **Surf Plan Sub-Agent** (safety knowledge via ChromaDB) |
| Vector DB | ChromaDB with `text-embedding-3-small` embeddings, seeded from `backend/app/modules/knowledge/data/safety_rules.txt` |
| MCP | A FastMCP server exposes the safety knowledge base as tools (`backend/app/modules/mcp/server.py`) |
| Background jobs | Celery + Redis (post weather sync, legacy deep-research jobs) |

More detail: [`.codex/AGENTS.md`](.codex/AGENTS.md).

## Tech stack

- **Backend:** FastAPI, SQLModel, Alembic, Celery, Redis, SQLite
- **Frontend:** Svelte 4, Vite 5, Tailwind CSS 3
- **Tooling:** Python ≥ 3.13, [uv](https://docs.astral.sh/uv/), Node.js 18+

## Getting started

### 1. Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- Redis running on `localhost:6379` (needed for Celery features)
- An [OpenAI API key](https://platform.openai.com/api-keys) and a [Tavily API key](https://tavily.com/)

### 2. Configure environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-key
TAVILY_API_KEY=your-tavily-key
# Optional overrides
# DB_URL=sqlite:///./dev.db
# REDIS_URL=redis://localhost:6379/0
```

> Never commit `.env`. It is already listed in `.gitignore`.

### 3. Install dependencies

```bash
uv sync
cd frontend && npm install && cd ..
```

### 4. Seed the knowledge base (first run)

```bash
uv run python -m backend.app.modules.knowledge.vectordb
```

### 5. Run the app

Build the frontend once, then start the API server (it also serves the built UI):

```bash
cd frontend && npm run build && cd ..
make dev
# open http://127.0.0.1:8000
```

Start the Celery worker in a second terminal (Redis must be running):

```bash
make worker
```

**Frontend development with hot reload:** keep `make dev` running, then in another terminal:

```bash
cd frontend && npm run dev
# open http://localhost:5173/static/   (note the /static/ path)
```

### 6. Try the MCP server

The MCP server speaks over stdio, so test it with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run python -m backend.app.modules.mcp.server
```

It also works with MCP clients such as Claude Desktop.

## Project structure

```
backend/app/
├── main.py                  # FastAPI entry point, serves the built frontend
├── core/settings.py         # Environment-based configuration
├── models/                  # SQLModel tables and DB engine
└── modules/
    ├── surf/                # Supervisor + sub-agents, /api/surf endpoints, plan history
    ├── knowledge/           # ChromaDB vector store and safety rules data
    ├── mcp/                 # FastMCP server
    ├── social/              # Feed, community, notifications, hazards (/api/social)
    ├── planner/             # Celery-based deep-research jobs (/api/planner)
    └── agent/               # Coding-agent endpoint (/api/agent)
frontend/src/                # Svelte components (Dashboard, SurfPlanner, SocialFeed, ...)
migrations/                  # Alembic migrations
```

## API docs

With the server running, interactive docs are available at `http://127.0.0.1:8000/docs` (Swagger UI) and `http://127.0.0.1:8000/scalar` (Scalar).

## Contributing

Issues and pull requests are welcome.

## License

Released under the MIT License. See [`LICENSE`](LICENSE).
