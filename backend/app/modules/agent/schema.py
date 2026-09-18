from pydantic import BaseModel

class AgentRequest(BaseModel):
    user_id: int
    prompt: str

class AgentResponse(BaseModel):
    id: int
    user_id: int
    prompt: str
    response: str
