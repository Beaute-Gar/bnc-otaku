from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.database import Base


class WaSession(Base):
    __tablename__ = "wa_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_key = Column(String(64), unique=True, nullable=False, index=True)
    session_data = Column(Text, nullable=False)
    checksum = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
