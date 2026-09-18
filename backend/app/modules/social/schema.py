from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostCreateRequest(BaseModel):
    user_id: int
    location: str
    category: str = "Session"
    caption: str
    media_url: Optional[str] = None
    media_urls: Optional[str] = None

class CommentCreateRequest(BaseModel):
    user_id: int
    content: str

class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    content: str
    created_at: datetime

class PostResponse(BaseModel):
    id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    location: str
    category: str
    caption: str
    media_url: Optional[str] = None
    media_urls: Optional[str] = None
    ai_weather_synced: bool
    wind_conditions: Optional[str] = None
    swell_info: Optional[str] = None
    tide_info: Optional[str] = None
    created_at: datetime
    comments: List[CommentResponse] = []
    likes_count: int = 0
    liked_by_users: List[int] = []

class TranslateRequest(BaseModel):
    text: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    sender_id: int
    sender_name: str
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    type: str
    message: str
    is_read: bool
    created_at: datetime

# ==========================================
# V3 NEW SCHEMAS (Community & Hazard)
# ==========================================

class ThreadCreateRequest(BaseModel):
    user_id: int
    title: str
    category: str
    content: str

class ThreadCommentCreateRequest(BaseModel):
    user_id: int
    content: str

class ThreadCommentResponse(BaseModel):
    id: int
    thread_id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    content: str
    created_at: datetime

class ThreadResponse(BaseModel):
    id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    title: str
    category: str
    content: str
    created_at: datetime
    comments: List[ThreadCommentResponse] = []

class MarketItemCreateRequest(BaseModel):
    user_id: int
    title: str
    price: str
    location: str
    condition: str
    description: str
    image_url: Optional[str] = None

class MarketCommentCreateRequest(BaseModel):
    user_id: int
    content: str

class MarketCommentResponse(BaseModel):
    id: int
    market_item_id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    content: str
    created_at: datetime

class MarketItemResponse(BaseModel):
    id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    title: str
    price: str
    location: str
    condition: str
    description: str
    image_url: Optional[str] = None
    status: str = "Available"
    created_at: datetime
    comments: List[MarketCommentResponse] = []

class MeetupCreateRequest(BaseModel):
    user_id: int
    title: str
    location: str
    date: str
    time: str
    description: str
    skill_level: str

class MeetupCommentCreateRequest(BaseModel):
    user_id: int
    content: str

class MeetupCommentResponse(BaseModel):
    id: int
    meetup_id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    content: str
    created_at: datetime

class MeetupResponse(BaseModel):
    id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    title: str
    location: str
    date: str
    time: str
    description: str
    skill_level: str
    created_at: datetime
    attendees: List[str] = []
    comments: List[MeetupCommentResponse] = []

class HazardCommentCreateRequest(BaseModel):
    user_id: int
    content: str

class HazardCommentResponse(BaseModel):
    id: int
    user_id: int
    username: str
    profile_pic_url: Optional[str] = None
    content: str
    created_at: datetime

class HazardReportCreateRequest(BaseModel):
    reporter_id: int
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: int
    hazard_type: str
    description: str
    media_url: Optional[str] = None

class HazardReportResponse(BaseModel):
    id: int
    reporter_id: int
    username: str
    profile_pic_url: Optional[str] = None
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: int
    hazard_type: str
    description: str
    media_url: Optional[str] = None
    created_at: datetime
    comments: List[HazardCommentResponse] = []
