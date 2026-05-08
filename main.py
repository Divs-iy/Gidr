# ✅ CORRECT STRUCTURE

# --- 1. IMPORTS (no duplicates) ---
import os, json, shutil, logging
from database import get_db, init_db, InvoiceRecord, LineItem, User
#from huggingface_hub import User
import uvicorn
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Body, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pipeline.ocr import OCRProcessor
from pipeline.extractor import AIExtractor
from fastapi import Header

# --- PATCH START ---
import bcrypt
# Passlib looks for __about__, so we give it what it wants
def get_password_hash(password: str):
    # Convert string to bytes
    pwd_bytes = password.encode('utf-8')
    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    try:
        # Both the attempt and the stored hash must be encoded to bytes
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False
# --- PATCH END ---

# --- 2. APP SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gidr API")
executor = ThreadPoolExecutor(max_workers=2)
EXPORT_DIR = "data/exports"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR, exist_ok=True)
# app.mount("/data/raw", StaticFiles(directory="data/raw"), name="raw_files")
app.mount("/downloads", StaticFiles(directory="data/exports"), name="downloads")
# main.py — add this line after the other app.mount lines
os.makedirs("data/raw_archive", exist_ok=True)
app.mount("/originals", StaticFiles(directory="data/raw_archive"), name="originals")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ocr_engine = OCRProcessor()
extractor_engine = AIExtractor()
init_db()
# Security Constants
SECRET_KEY = "GIDR_SUPER_SECRET_KEY_2026" # Keep this safe!
ALGORITHM = "HS256"
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Helper Functions
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/register")
async def register(
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash and save (using the new bcrypt logic)
    hashed = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"msg": "Registration successful", "user_id": new_user.id}

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.email, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "user_name": user.email}

# --- 3. HELPERS ---
def save_processed_json(filename: str, data: dict):
    """Saves extracted data so /compare can load it without re-OCR."""
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    path = os.path.join(processed_dir, f"{filename}.json")
    with open(path, "w") as f:
        json.dump(data, f)
    return path

# --- 4. ROUTES ---
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Assumes format "Bearer <token>"
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
@app.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    source: str = Query(default="extraction")
):
    logger.info(f"Received file: {file.filename}")
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    temp_path = f"data/raw/{file.filename}"
    os.makedirs("data/raw", exist_ok=True)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        loop = asyncio.get_event_loop()

        def run_pipeline():
            ocr_results = ocr_engine.run_ocr(temp_path)
            return extractor_engine.extract_with_groq(ocr_results)

        extracted = await loop.run_in_executor(executor, run_pipeline)

        base_name = os.path.splitext(file.filename)[0]
        save_processed_json(base_name, extracted)

        rows = []
        for item in extracted.get("line_items", []):
            rows.append({
                "Invoice Number": extracted.get("invoice_number"),
                "Vendor": extracted.get("vendor_name"),
                "Date": extracted.get("date"),
                "Description": item.get("description"),
                "Quantity": item.get("quantity"),
                "Unit Price": item.get("unit_price"),
                "Line Amount": item.get("amount"),
                "Total Bill": extracted.get("total_amount"),
            })
        if not rows:
            rows.append({"Note": "No line items found", **extracted})

        file_name = f"invoice_{extracted.get('invoice_number', 'unknown')}_{datetime.now().strftime('%H%M%S')}.xlsx"
        web_export_path = os.path.join("data", "exports", file_name)
        pd.DataFrame(rows).to_excel(web_export_path, index=False)
        download_url = f"http://localhost:8000/downloads/{file_name}"

        # ✅ Only save to DB if real extraction — quotes are temp files only
        if source == "extraction":
            new_record = InvoiceRecord(
                vendor_name=extracted.get("vendor_name", "Unknown"),
                total_amount=extracted.get("total_amount", 0.0),
                invoice_number=extracted.get("invoice_number", "N/A"),
                date=extracted.get("date"),
                excel_link=download_url,
                confidence_score=extracted.get("confidence_score", None),
                user_id=current_user_id,
                original_filename=file.filename,
            )
            db.add(new_record)
            db.flush()

            for item in extracted.get("line_items", []):
                db.add(LineItem(
                    invoice_id=new_record.id,
                    description=item.get("description"),
                    unit=item.get("unit"),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    amount=item.get("amount")
                ))
            db.commit()

        # ✅ Always return regardless of source
        return {
            "status": "success",
            "filename": file.filename,
            "saved_as": base_name,
            "download_url": download_url,
            "extracted_data": extracted,
            # "record_id": new_record.id if new_record else None
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            # ✅ Only archive originals for real extractions
            if source == "extraction":
                archive_path = f"data/raw_archive/{file.filename}"
                os.makedirs("data/raw_archive", exist_ok=True)
                shutil.copy(temp_path, archive_path)
            os.remove(temp_path)
@app.post("/compare")
async def compare_docs(
    invoice: UploadFile = File(...),
    quote_filename: str = Query(...)
):
    # ✅ Load quote JSON — already extracted at upload time
    quote_path = f"data/processed/{quote_filename}.json"
    if not os.path.exists(quote_path):
        raise HTTPException(status_code=404, detail="Quote not found. Upload quote first.")

    with open(quote_path, "r") as f:
        quote_data = json.load(f)

    # ✅ Save the invoice file temporarily
    temp_invoice = f"data/raw/{invoice.filename}"
    os.makedirs("data/raw", exist_ok=True)

    try:
        with open(temp_invoice, "wb") as buffer:
            shutil.copyfileobj(invoice.file, buffer)

        # ✅ Check if this invoice was already extracted (uploaded before)
        invoice_base = os.path.splitext(invoice.filename)[0]
        invoice_json_path = f"data/processed/{invoice_base}.json"

        if os.path.exists(invoice_json_path):
            # ✅ Already extracted — just load the JSON, zero OCR cost
            with open(invoice_json_path, "r") as f:
                invoice_data = json.load(f)
        else:
            # ✅ Not seen before — OCR + extract once, then save for reuse
            ocr_result = ocr_engine.run_ocr(temp_invoice)
            invoice_data = extractor_engine.extract_with_groq(ocr_result)
            save_processed_json(invoice_base, invoice_data)

        # ✅ Pure JSON comparison — no OCR, just math
        discrepancies = []

        q_amt = float(quote_data.get('total_amount', 0))
        i_amt = float(invoice_data.get('total_amount', 0))
        if abs(q_amt - i_amt) > 0.01:
            discrepancies.append({
                "field": "Total Amount",
                "quote": q_amt,
                "invoice": i_amt,
                "diff": round(i_amt - q_amt, 2)
            })

        # ✅ Also compare line items if both have them
        q_items = {item['description']: item['amount'] for item in quote_data.get('line_items', [])}
        i_items = {item['description']: item['amount'] for item in invoice_data.get('line_items', [])}

        for desc, q_val in q_items.items():
            i_val = i_items.get(desc)
            if i_val is None:
                discrepancies.append({
                    "field": f"Item '{desc}'",
                    "quote": q_val,
                    "invoice": "MISSING",
                    "diff": q_val
                })
            elif abs(float(q_val) - float(i_val)) > 0.01:
                discrepancies.append({
                    "field": f"Item '{desc}'",
                    "quote": q_val,
                    "invoice": i_val,
                    "diff": round(float(i_val) - float(q_val), 2)
                })

        return {
            "status": "MISMATCH" if discrepancies else "MATCH",
            "discrepancies": discrepancies,
            "invoice_data": invoice_data,
            "quote_data": quote_data
        }

    finally:
        if os.path.exists(temp_invoice):
            os.remove(temp_invoice)

@app.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: int, updated_data: dict = Body(...), db: Session = Depends(get_db)):
    invoice = db.query(InvoiceRecord).filter(InvoiceRecord.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.vendor_name = updated_data.get("vendor_name", invoice.vendor_name)
    invoice.total_amount = updated_data.get("total_amount", invoice.total_amount)
    invoice.date = updated_data.get("date", invoice.date)
    db.commit()
    return {"status": "success", "message": "Updated successfully"}


@app.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(InvoiceRecord).filter(InvoiceRecord.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"status": "success", "message": "Deleted successfully"}

@app.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    invoices = db.query(InvoiceRecord).options(
        joinedload(InvoiceRecord.items)
    ).filter(
        InvoiceRecord.user_id == current_user_id
    ).order_by(InvoiceRecord.id.desc()).all()

    # ✅ Manually serialize — fixes history page showing nothing
    return [
        {
            "id": inv.id,
            "vendor_name": inv.vendor_name,
            "total_amount": inv.total_amount,
            "date": inv.date,
            "confidence_score": inv.confidence_score,
            # "filename": inv.invoice_number,
            "filename": inv.original_filename or inv.invoice_number,
            "excel_link": inv.excel_link,
            "items": [
                {"id": item.id, "description": item.description, "unit": item.unit,"amount": item.amount}
                for item in inv.items
            ]
        }
        for inv in invoices
    ]


@app.get("/export-all")
async def export_all(db: Session = Depends(get_db)):
    invoices = db.query(InvoiceRecord).all()
    all_data = []
    for inv in invoices:
        for item in inv.items:
            all_data.append({
                "Invoice #": inv.invoice_number,
                "Vendor": inv.vendor_name,
                "Item": item.description,
                "Amount": item.amount,
                "Total Bill": inv.total_amount,
                "Date": inv.date
            })
    master_path = os.path.expanduser("~/Desktop/Gidr_Exports/Master_Report.xlsx")
    pd.DataFrame(all_data).to_excel(master_path, index=False)
    return {"status": "success", "path": master_path}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)