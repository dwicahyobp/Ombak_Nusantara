from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="Unique username for the surfer")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., description="User password")
    skill_level: str = Field(default="Beginner", description="Skill levels: Beginner, Intermediate, Advanced, Expert")

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateSkillRequest(BaseModel):
    skill_level: str

class UserUpdateBioRequest(BaseModel):
    bio: str

class UserUpdateProfilePicRequest(BaseModel):
    profile_pic_url: str

class SurfboardCreateRequest(BaseModel):
    name: Optional[str] = Field(default="My Surfboard")
    brand: Optional[str] = None
    length: Optional[str] = None
    caption: Optional[str] = None
    image_url: Optional[str] = None

class SurfboardResponse(BaseModel):
    id: int
    user_id: int
    name: str
    brand: Optional[str]
    length: Optional[str]
    caption: Optional[str]
    image_url: Optional[str]
    created_at: datetime

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    skill_level: str
    bio: Optional[str]
    profile_pic_url: Optional[str]
    created_at: datetime
    surfboards: List[SurfboardResponse] = []
    # Can also add posts and plans if needed

class SurfPlanCreateRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user creating the plan")
    target_spot: str = Field(..., description="Surfing spot destination")
    planned_date: str = Field(..., description="Target date in YYYY-MM-DD format")