from sqlalchemy import Column, Integer, String, DateTime, func
from backend.database import Base


class AdEvent(Base):
    __tablename__ = "ad_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    event_type = Column(String(50), nullable=False)
    page = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
