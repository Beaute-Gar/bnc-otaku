from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, func, DECIMAL
from backend.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    montant_fcfa = Column(Integer, nullable=False)
    devise = Column(String(10), default="XAF")
    operateur = Column(Enum("MTN", "ORANGE", "WAVE", "MOOV", "AIRTEL", name="operateur"), nullable=False)
    transaction_id = Column(String(100), unique=True, nullable=True)
    reference = Column(String(100), unique=True, nullable=False)
    statut = Column(Enum("pending", "success", "failed", "expired", name="payment_status"), nullable=False, default="pending")
    produit = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    raw_webhook = Column(Text, nullable=True)


class PremiumProduct(Base):
    __tablename__ = "premium_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    prix_fcfa = Column(Integer, nullable=False)
    badge_label = Column(String(50), nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
