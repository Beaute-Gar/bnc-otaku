from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
from backend.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    cert_number = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    level = Column(Enum("junior", "senior", "master", "legendary", name="cert_level"), nullable=False)
    score = Column(Integer, nullable=False)
    issued_at = Column(DateTime, server_default=func.now())
    download_count = Column(Integer, default=0)
    is_verified = Column(Integer, default=0)
