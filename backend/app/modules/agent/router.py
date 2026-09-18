from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime

from backend.app.models.engine import get_session
from backend.app.models.database import User, AgentMemory
from backend.app.modules.agent.schema import AgentRequest, AgentResponse
from backend.app.modules.agent.services import generate_code_response

router = APIRouter()

@router.post("/code", response_model=AgentResponse)
async def ask_coding_agent(request: AgentRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Generate code using the agent
    code_response = generate_code_response(request.prompt)
    
    # Store in memory/persistence
    memory = AgentMemory(
        user_id=request.user_id,
        prompt=request.prompt,
        response=code_response
    )
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    
    return memory
