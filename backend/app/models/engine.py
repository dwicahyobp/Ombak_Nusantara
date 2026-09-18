from sqlmodel import create_engine, Session
from backend.app.core.settings import settings

connect_args = {}
if settings.db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.db_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session