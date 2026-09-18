from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from backend.app.modules.planner.router import planner_router
from backend.app.modules.surf.router import router as surf_router
from backend.app.modules.social.router import router as social_router
from backend.app.modules.agent.router import router as agent_router

app = FastAPI(title="Ombak Nusantara", version="1.0.0")

@app.on_event("startup")
def on_startup():
    from sqlmodel import SQLModel
    from backend.app.models.engine import engine
    import backend.app.models.database  # ensure models are loaded
    SQLModel.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(planner_router, prefix="/api/planner", tags=["Surf Planner Tasks"])

app.include_router(surf_router, prefix="/api/surf", tags=["Surf & Swarm"])

app.include_router(social_router, prefix="/api/social", tags=["Social Feed"])

app.include_router(agent_router, prefix="/api/agent", tags=["Coding Agent"])

@app.get("/scalar", response_class=HTMLResponse)
def get_scalar():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="Ombak Nusantara API Reference",
    )

app.mount("/static/uploads", StaticFiles(directory="backend/uploads"), name="static_uploads")
app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

import os
import shutil
import uuid
from fastapi import UploadFile, File

@app.post("/api/upload", tags=["Upload"])
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("backend/uploads", exist_ok=True)
    # Generate unique filename to avoid conflicts
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = f"backend/uploads/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{filename}"}

@app.get("/")
async def root():
    response = FileResponse("frontend/dist/index.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
