# Gidr – Intelligent Document Processing for Invoice Automation

## Overview
Gidr is an AI-powered Invoice/Bill Processing System designed to convert invoice images into structured editable data and export them into Excel.

## Features
- Invoice image upload
- OCR-based text extraction (PaddleOCR)
- Key field extraction:
  - Invoice Number
  - Date
  - Vendor Name
  - Total Amount
- Human-in-the-loop editable verification
- Excel export automation
- Streamlit interface

## Tech Stack
- Python
- Streamlit
- PaddleOCR
- OpenCV
- Pandas
- OpenPyXL

## Current Status
### Completed:
- OCR extraction
- Structured field extraction
- UI verification
- Excel export

### Upcoming:
- Layout-aware invoice understanding
- LLM semantic extraction
- Multi-template invoice adaptation
- Confidence scoring
- Advanced ML pipeline

## Project Structure
```bash
Gidr/
│── app.py
│── pipeline/
│   ├── ocr_engine.py
│   ├── extractor.py
│── utils/
│── data/
│── requirements.txt
│── README.md
