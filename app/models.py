from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Link: One user can have many invoices
    invoices = relationship("InvoiceRecord", back_populates="owner")

class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="invoices")
    filename = Column(String, nullable=True)
    vendor_name = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    date = Column(String, nullable=True)
    total_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    excel_link = Column(String, nullable=True)          # ✅ ADD
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")  # ✅ ADD


class LineItem(Base):                                   # ✅ ADD entire class
    __tablename__ = "line_items"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Float, nullable=True)
    amount = Column(Float)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    invoice = relationship("InvoiceRecord", back_populates="items")