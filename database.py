from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
import datetime
import os

# This creates the gidr.db file in your folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'gidr.db')}"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# This is the "Shape" of your data in the database
class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String)
    invoice_number = Column(String)
    date = Column(String)
    total_amount = Column(Float)
    tax_amount = Column(Float)
    confidence_score = Column(Float)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    excel_link = Column(String, nullable=True) 
    original_filename = Column(String, nullable=True)  # ✅ ADD THIS
    terms_and_conditions = Column(String, nullable=True)
    items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")
    # database.py — add one line inside InvoiceRecord class
class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    unit = Column(String, nullable=True) 
    quantity = Column(Integer)
    unit_price = Column(Float)
    amount = Column(Float)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    invoice = relationship("InvoiceRecord", back_populates="items")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class AuditReport(Base):
    __tablename__ = "audit_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    quote_filename = Column(String)
    invoice_filename = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    items = relationship("AuditItem", back_populates="report", cascade="all, delete-orphan")

class AuditItem(Base):
    __tablename__ = "audit_items"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("audit_reports.id"))
    description = Column(String)
    quoted_price = Column(Float)
    invoiced_price = Column(Float)
    status = Column(String)        # MATCH, PRICE MISMATCH, NOT IN QUOTE
    reason = Column(String)        # auto-generated reason
    action = Column(String)        # FLAGGED or APPROVED
    comment = Column(String)       # accountant's note
    report = relationship("AuditReport", back_populates="items")


def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()