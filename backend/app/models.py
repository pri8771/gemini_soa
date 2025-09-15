from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class PO(Base):
    __tablename__ = "pos"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    pdf_path = Column(String, nullable=False)
    pdf_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="queued")
    progress = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)

    buyer_name = Column(String, default="")
    buyer_street = Column(String, default="")
    buyer_city = Column(String, default="")
    buyer_postal = Column(String, default="")

    shipto_name = Column(String, default="")
    shipto_street = Column(String, default="")
    shipto_city = Column(String, default="")
    shipto_postal = Column(String, default="")
    shipto_id = Column(String, default="")

    line_items = relationship("LineItem", back_populates="po", cascade="all, delete-orphan")

class LineItem(Base):
    __tablename__ = "line_items"
    id = Column(String, primary_key=True, index=True)
    po_id = Column(String, ForeignKey("pos.id"))
    description = Column(Text, default="")
    quantity = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    po = relationship("PO", back_populates="line_items")

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String, nullable=False)  # 'global' or 'customer'
    customer_key = Column(String, nullable=True)
    prompt_text = Column(Text, default="")
