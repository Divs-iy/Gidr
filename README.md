**Gidr | AI-Powered Invoice Extraction & Comparison**

[https://github.com/user-attachments/assets/dad26131-7b19-4419-89ee-c8ffe134b834]


Gidr is a full-stack web application designed to streamline accounts payable workflows. It leverages AI-driven OCR (Optical Character Recognition) to extract data from invoices and compare them against quotes with high precision.

🚀 Live Demo
Live Demo: [https://gidr-frontend-h9suzbxgw-divyas-projects-cf497612.vercel.app]

Backend API: (https://gidr.onrender.com)/docs

✨ Features
User Authentication: Secure Sign-in/Sign-up flow with JWT (JSON Web Tokens).

AI Extraction: Uses PaddleOCR and Groq Vision to extract line items, vendor details, and totals from images/PDFs.

Intelligent Comparison: Compares extracted invoice data against uploaded quotes to identify price discrepancies automatically.

Export to Excel: Generates downloadable .xlsx reports of extracted data.

Invoice History: A dashboard to view, edit, and manage previously processed documents.

🛠️ Technical Stack
Frontend

Framework: Next.js (React)

Language: TypeScript

Styling: Tailwind CSS

State Management: Axios & React Hooks

Backend

Framework: FastAPI (Python)

OCR Engine: PaddleOCR (Headless)

LLM Integration: Groq (Vision-Llama)

Database: SQLite with SQLAlchemy ORM

Deployment: Render (Dockerized/System Libs)

⚙️ Installation & Setup
Prerequisites

Python 3.10+

Node.js 18+

Groq API Key

Backend Setup

Navigate to the backend directory: cd gidr-be

Create a virtual environment: python -m venv venv

Install dependencies:
pip install -r requirements.txt
GROQ_API_KEY=your_key_here
DATABASE_URL=sqlite:///./test.db
uvicorn main:app --reload

Frontend Setup

Navigate to the frontend directory: cd gidr-fe

Install packages: npm install

Set up environment variables in .env.local:

Code snippet
NEXT_PUBLIC_API_URL=http://localhost:8000
Run the development server: npm run dev

📸 Deployment Notes
The application is architected to be environment-aware.

CORS: Configured to allow cross-origin requests between Vercel and Render.

System Dependencies: Backend requires libGL.so.1 and libgomp.so.1 for PaddleOCR execution on Linux environments.

🤝 Contact
Divya Thakur - [Divs-iy]

Project Link: https://github.com/Divs-iy/gidr
