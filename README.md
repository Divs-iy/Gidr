# Gidr — AI-Powered Invoice Intelligence Platform

> Extract any billing document to Excel, detect vendor discrepancies, and build persistent vendor memory — powered by Groq, CascadeFlow, and Hindsight.

🌐 **Live Demo:** [gidr-frontend.vercel.app](https://gidr-frontend.vercel.app)  
🔧 **Backend API:** [gidr.onrender.com](https://gidr.onrender.com)  
📖 **API Docs:** [gidr.onrender.com/docs](https://gidr.onrender.com/docs)

---

## 🚀 What is Gidr?

Gidr is a real-world deployed AI platform built for finance and accounts teams who deal with high-volume vendor billing. It was originally built as a freelance project for a construction company in Ahmedabad and extended with AI features for the hackathon.

**The problem it solves:**
- Finance teams waste hours manually entering invoice data into Excel
- Vendors overcharge or add unauthorized items — and it goes unnoticed
- Duplicate invoices get processed and paid twice
- No institutional memory of vendor billing history

**Gidr automates all of this.**

---

## ✨ Features

### 📄 Invoice Extraction
- Upload any invoice — PDF, PNG, JPG, JPEG
- AI reads the document using Groq's LLaMA 4 Scout vision model
- Extracts vendor name, invoice number, date, line items, quantities, rates, totals, and terms & conditions
- Generates a structured Excel file instantly
- Supports **printed, handwritten, and multilingual** (Hindi, Gujarati, Marathi) bills
- Automatically translates regional language content to English
- Shows confidence score — low confidence triggers a warning to verify manually

### 🔍 Quote vs Invoice Discrepancy Verification
- Upload a vendor quotation and an invoice side by side
- AI compares every line item and flags mismatches
- Auto-generates reason for each discrepancy:
  - *"Invoiced price is ₹500 higher than quoted price"*
  - *"Item was never approved in the initial quotation"*
  - *"Item present in quote but missing from invoice"*
- Accountant reviews each flag and clicks **Approve** or **Flag**
- Adds justification notes per item

### 📊 Audit Report Generation
- After review, download a color-coded Excel audit report
- 🟢 Green = matched items
- 🔴 Red = flagged discrepancies
- 🟡 Yellow = approved exceptions
- Summary section with total disputed amount
- Saved to database — revisit any past audit from the Audit Reports page

### ✨ Smart Document Extractor
- Upload **any** document — contract, agreement, BOQ, insurance policy, purchase order, receipt
- AI auto-detects document type — no templates, no configuration
- Generates multi-sheet Excel:
  - **Sheet 1:** Summary (parties, dates, key fields, financials, payment schedule)
  - **Sheet 2:** Fee Breakdown (itemized costs)
  - **Sheet 3:** Sections & Terms (every section summarized with key points)

### 🧠 Vendor Intelligence (Powered by Hindsight + CascadeFlow)
- Every invoice processed is stored as a persistent memory in Hindsight
- Ask natural language questions about vendor history:
  - *"How many invoices have been processed from Suryam Developers?"*
  - *"What is the average invoice amount for this vendor?"*
  - *"Were any discrepancies flagged recently?"*
- CascadeFlow routes queries by complexity:
  - Simple queries → `llama-3.1-8b-instant` (fast, cheap)
  - Complex analytical queries → `llama-3.3-70b-versatile` (powerful)
- Duplicate invoice detection — flags if same invoice number or amount was already processed
- Anomaly detection — alerts when vendor bills 15%+ above their historical average

### 🔒 Security & Multi-User
- JWT authentication — each user sees only their own data
- Password hashing with bcrypt
- All routes filter by user ID — complete data isolation
- Rate limiting on upload endpoints

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Next.js Frontend                      │
│              (Vercel — gidr-frontend.vercel.app)         │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS API calls
┌─────────────────────────▼───────────────────────────────┐
│                   FastAPI Backend                         │
│                (Render — gidr.onrender.com)              │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ OCR Pipeline│  │ AI Extractor │  │  Hindsight     │  │
│  │ PyMuPDF     │  │ Groq Vision  │  │  Vendor Memory │  │
│  │ 150 DPI     │  │ LLaMA 4 Scout│  │  Vector Store  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ CascadeFlow │  │   SQLite DB  │  │  Excel Engine  │  │
│  │ Model Router│  │  SQLAlchemy  │  │  openpyxl      │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, TypeScript |
| Backend | FastAPI, Python 3.11 |
| Database | SQLite + SQLAlchemy ORM |
| AI Vision | Groq API + LLaMA 4 Scout 17B |
| Model Routing | CascadeFlow (complexity-based routing) |
| Vendor Memory | Hindsight (persistent vector memory) |
| PDF Processing | PyMuPDF (150 DPI render) |
| Excel Generation | openpyxl, pandas |
| Authentication | JWT + bcrypt |
| Deployment | Render (backend) + Vercel (frontend) |

---

## 🔄 How It Works

### Invoice Extraction Pipeline
```
PDF/Image Upload
      ↓
PyMuPDF renders PDF pages at 150 DPI
      ↓
Pages converted to base64 PNG
      ↓
Groq LLaMA 4 Scout reads image directly (no OCR step)
      ↓
Structured JSON extracted (vendor, items, totals, T&C)
      ↓
openpyxl generates Excel file
      ↓
Hindsight stores invoice memory
      ↓
User downloads Excel
```

### Discrepancy Verification Pipeline
```
Quote uploaded → saved as processed JSON
      ↓
Invoice uploaded → extracted fresh
      ↓
Amount-based fuzzy matching of line items
      ↓
Discrepancies calculated with auto-reasons
      ↓
Accountant reviews in interactive UI
      ↓
Audit report generated with color coding
      ↓
Saved to DB for future reference
```

---

## 🌍 Supported Document Types

| Document Type | Extraction | Discrepancy Check | Smart Extract |
|---|---|---|---|
| Invoice / Bill | ✅ | ✅ | ✅ |
| BOQ (Bill of Quantities) | ✅ | ✅ | ✅ |
| Insurance Policy | ✅ | ❌ | ✅ |
| Contract / Agreement | ❌ | ❌ | ✅ |
| Purchase Order | ✅ | ✅ | ✅ |
| Handwritten Bills | ✅ | ✅ | ✅ |
| Hindi / Gujarati Bills | ✅ | ✅ | ✅ |

---

## ⚡ Performance

- **Extraction time:** 5-15 seconds per document
- **PDF render:** 150 DPI — optimal balance of quality and speed
- **Max file size:** 10MB
- **Max pages:** All pages processed in batches of 2
- **Supported formats:** PDF, PNG, JPG, JPEG

---

## 🚧 Limitations

1. **Server cold start** — Free Render tier sleeps after inactivity. First request takes ~50 seconds to wake up
2. **SQLite resets on redeploy** — Moving to PostgreSQL for production
3. **Very illegible handwriting** — If a human can't read it, neither can the AI. Low confidence score warns the user
4. **Multi-page BOQs** — Grand total extraction improves with more pages but very long documents may miss items
5. **Vendor intelligence needs history** — Gets smarter after multiple invoices from same vendor

---

## 🗺️ Roadmap

- [ ] PostgreSQL migration for persistent production database
- [ ] Razorpay payment integration for subscription billing
- [ ] Fine-tuned model for Indian handwritten bills (similar to medical prescription AI)
- [ ] Google Translate API integration for higher accuracy regional language support
- [ ] Mobile app for on-site invoice capture
- [ ] Tally and Zoho Books integration
- [ ] WhatsApp bot — send photo of bill, get Excel back

---

## 🏃 Running Locally

### Backend
```bash
git clone https://github.com/Divs-iy/Gidr.git
cd Gidr
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
echo "HINDSIGHT_API_KEY=your_key_here" >> .env
echo "HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io" >> .env

python3 main.py
```

### Frontend
```bash
git clone https://github.com/Divs-iy/Gidr-fe.git
cd Gidr-fe
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

---

## 👩‍💻 Built By

**Divya Thakur** — 7th Semester B.E. CSE-AIML, New LJ Institute of Engineering and Technology, Ahmedabad

Built as a freelance product for a real construction company client, then extended with AI features for this hackathon.

---

## 📄 License

MIT License — feel free to use, modify, and build on this.
