# Invoice OCR and Field Extractor

College final year minor project to extract basic details from invoice and bill images using Tesseract OCR and Python.

## Requirements
- Python 3.10+
- Streamlit
- PyTesseract
- OpenCV & Pillow
- Pandas
- Tesseract OCR engine (Windows)

## Setup and Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR for Windows:
- Download the installer from the UB-Mannheim Tesseract wiki: https://github.com/UB-Mannheim/tesseract/wiki
- Install it to the default path: `C:\Program Files\Tesseract-OCR`

## Running the Application

Double click on `run.bat` or run from terminal:
```bash
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Testing with Samples
Sample invoice images are provided in this folder for testing:
- `sample_invoice.png` (tax invoice)
- `sample_cafe_receipt.png` (cafe bill)
- `sample_retail_bill.png` (retail store receipt)

Upload any of these images to test the extraction of Vendor Name, Date, Invoice Number, and Total Amount.
Extracted data can be edited on screen and downloaded as CSV or JSON.
