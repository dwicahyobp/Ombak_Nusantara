# Ombak Nusantara - Agentic Architecture

## 1. Supervisor Agent (Team)
**Name:** Ombak Nusantara Main Supervisor
**Model:** OpenAI (gpt-4o)
**Role:**
The main manager of Ombak Nusantara. It receives user requests and orchestrates the workload by delegating to specialized sub-agents. It combines the insights from sub-agents into a single, cohesive final report for the user.

## 2. Sub-Agents

### A. Surf Report Sub-Agent
**Name:** Surf Report Sub-Agent
**Model:** OpenAI (gpt-4o)
**Role:**
Searches the live web to analyze current marine weather conditions, wave heights, swell direction, and wind speeds at the specified surfing locations.
**Tools:** 
- `TavilyTools` (Web Search)

### B. Surf Plan Sub-Agent
**Name:** Surf Plan Sub-Agent
**Model:** OpenAI (gpt-4o)
**Role:**
Creates personalized surf schedules, surfboard recommendations, and safety tips tailored to the user's profile and the target location's safety rules.
**Tools:**
- `search_safety_rules` (Vector DB / ChromaDB - Knowledge Base Retrieval)

## 3. Workflow Execution
1. A user submits a surf plan request via the API.
2. The FastAPI router (`/api/surf/analyze`) receives the request.
3. If no recent valid cache exists, the Supervisor Agent is invoked.
4. The Supervisor delegates web searching to the Surf Report Sub-Agent.
5. The Supervisor delegates safety analysis and planning to the Surf Plan Sub-Agent, which queries ChromaDB for specific beach safety rules.
6. The Supervisor synthesizes the results and returns a comprehensive markdown report.
7. The system evaluates the report text to extract the final Safety Status (Safe, Warning, Danger) and saves it to the SQL database.

## 4. MCP (Model Context Protocol)
The project includes a FastMCP server (`backend/app/modules/mcp/server.py`) which acts as an integration point for external tools or bots (like Discord/Telegram). It provides tools:
- `get_beach_safety_info`: Queries the Vector DB for safety guidelines of a specific beach.
- `get_available_beaches`: Returns the list of currently supported beaches.
