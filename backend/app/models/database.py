from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# ==========================================
# 1. TABEL PENGGUNA (USER)
# ==========================================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    password: str = Field(default="password")
    # Skill levels: Beginner, Intermediate, Advanced, Expert
    skill_level: str = Field(default="Beginner") 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Profil V2
    bio: Optional[str] = Field(default=None)
    profile_pic_url: Optional[str] = Field(default=None)
    
    # Hubungan Relasi
    surf_plans: List["SurfPlan"] = Relationship(back_populates="user")
    surfboards: List["Surfboard"] = Relationship(back_populates="user")
    posts: List["Post"] = Relationship(back_populates="user")
    comments: List["Comment"] = Relationship(back_populates="user")
    likes: List["Like"] = Relationship(back_populates="user")
    notifications_received: List["Notification"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[Notification.user_id]"}
    )

# ==========================================
# 2. TABEL RENCANA SURFING (SURF PLAN)
# ==========================================
class SurfPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    target_spot: str = Field(index=True)
    planned_date: str  # Format: YYYY-MM-DD
    status: str = Field(default="Pending")  # Pending, Approved, Rejected, Completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Hubungan Relasi
    user: User = Relationship(back_populates="surf_plans")
    report: Optional["SurfReport"] = Relationship(back_populates="surf_plan")

# ==========================================
# 3. TABEL LAPORAN AGEN AI (SURF REPORT)
# ==========================================
class SurfReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    surf_plan_id: int = Field(foreign_key="surfplan.id", unique=True)
    
    # Metadata & Hasil Kerja Multi-Agent
    safety_status: str  # Safe, Warning, Danger (Blocked)
    summary: str        # Ringkasan cepat dari Supervisor Agent
    content_md: str     # Laporan Markdown detail gabungan Sub-Agent
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Hubungan Relasi
    surf_plan: SurfPlan = Relationship(back_populates="report")

# ==========================================
# 4. TABEL RESEARCH JOB (CELERY TASK RESULT)
# ==========================================
class ResearchJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Input dari user
    region: str = Field(default="Bali")
    target_spot: str = Field(index=True)
    skill_level: str
    date: str               # Format: YYYY-MM-DD
    preferred_time: str = Field(default="Sore")
    
    # Status & hasil dari Celery task
    status: str = Field(default="Pending")  # Pending, Completed, Failed, Rejected
    result_md: Optional[str] = Field(default=None)  # Laporan markdown final
    error_message: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

# ==========================================
# 5. TABEL V2: GARASI PAPAN (SURFBOARD)
# ==========================================
class Surfboard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    brand: Optional[str] = Field(default=None)
    length: Optional[str] = Field(default=None) # misal: "6'2"
    caption: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="surfboards")

# ==========================================
# 6. TABEL V2: SOCIAL FEED (POST)
# ==========================================
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    location: str = Field(index=True)
    category: str = Field(default="Session")
    caption: str
    media_url: Optional[str] = Field(default=None) # Foto/Video Tunggal (Legacy)
    media_urls: Optional[str] = Field(default=None) # Array string JSON URL (Multiple)
    
    # AI Weather Automations (ditarik background saat post dibuat)
    ai_weather_synced: bool = Field(default=False)
    wind_conditions: Optional[str] = Field(default=None)
    swell_info: Optional[str] = Field(default=None)
    tide_info: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")
    likes: List["Like"] = Relationship(back_populates="post")

# ==========================================
# 7. TABEL V2: COMMENTS & LIKES
# ==========================================
class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    user_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    post: Post = Relationship(back_populates="comments")
    user: User = Relationship(back_populates="comments")

class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    user_id: int = Field(foreign_key="user.id")
    
    post: Post = Relationship(back_populates="likes")
    user: User = Relationship(back_populates="likes")

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") # Receiver
    sender_id: int = Field(foreign_key="user.id") # Sender
    entity_id: Optional[int] = Field(default=None)
    entity_type: Optional[str] = Field(default=None) # 'post', 'thread', 'market', 'meetup', 'hazard'
    type: str # 'like', 'comment', 'alert', 'mention'
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    receiver: User = Relationship(back_populates="notifications_received", sa_relationship_kwargs={"foreign_keys": "[Notification.user_id]"})

# ==========================================
# 8. TABEL V2: AGENT MEMORY (Coding Agent)
# ==========================================
class AgentMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    prompt: str
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()

# ==========================================
# 9. TABEL V3: COMMUNITY (THREADS & MARKET)
# ==========================================
class Thread(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    category: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    comments: List["ThreadComment"] = Relationship(back_populates="thread")

class ThreadComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: int = Field(foreign_key="thread.id")
    user_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    thread: Thread = Relationship(back_populates="comments")

class MarketItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    price: str
    location: str
    condition: str
    description: str
    image_url: Optional[str] = Field(default=None)
    status: str = Field(default="Available")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    comments: List["MarketComment"] = Relationship(back_populates="market_item")

class MarketComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    market_item_id: int = Field(foreign_key="marketitem.id")
    user_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    market_item: MarketItem = Relationship(back_populates="comments")

class Meetup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    location: str
    date: str
    time: str
    description: str
    skill_level: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    attendees: List["MeetupAttendee"] = Relationship(back_populates="meetup")
    comments: List["MeetupComment"] = Relationship(back_populates="meetup")

class MeetupComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meetup_id: int = Field(foreign_key="meetup.id")
    user_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    meetup: Meetup = Relationship(back_populates="comments")

class MeetupAttendee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meetup_id: int = Field(foreign_key="meetup.id")
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    meetup: Meetup = Relationship(back_populates="attendees")

# ==========================================
# 10. TABEL V3: HAZARD ALERTS
# ==========================================
class HazardReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    location: str = Field(index=True)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: int # 1 to 5
    hazard_type: str
    description: str
    media_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship()
    comments: List["HazardComment"] = Relationship(back_populates="report", cascade_delete=True)

class HazardComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="hazardreport.id")
    user_id: int = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship()
    report: HazardReport = Relationship(back_populates="comments")