from sqlalchemy import Column, Integer, String, Float, DateTime, func
from backend.database import Base


class AdEvent(Base):
    __tablename__ = "admin_ad_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(20), nullable=False, default="view")
    revenue = Column(Float, default=0.0)
    source = Column(String(50), default="ad-gate")
    ip_address = Column(String(45), default=None)
    user_agent = Column(String(255), default=None)
    created_at = Column(DateTime, server_default=func.now())


class ReferralClick(Base):
    __tablename__ = "referral_clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False)
    ip_address = Column(String(45), default=None)
    created_at = Column(DateTime, server_default=func.now())


class CertificateRecord(Base):
    __tablename__ = "certificate_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(50), nullable=False)
    level_name = Column(String(30), nullable=False)
    grade = Column(String(5), nullable=False)
    score = Column(Integer, nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
