import os
import re
import cv2
import numpy as np
import pandas as pd
import streamlit as st
import pytesseract
from PIL import Image

st.set_page_config(
    page_title="Invoice Information Extraction",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stAppDeployButton"],
button[data-testid="stAppDeployButton"],
.stAppDeployButton,
.stDeployButton {
    display: none !important;
}
footer {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# check defualt tesseract path
standard_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
]

detected_path = ""
for p in standard_paths:
    if os.path.exists(p):
        detected_path = p
        pytesseract.pytesseract.tesseract_cmd = p
        break

st.sidebar.title("Invoice OCR System")
st.sidebar.caption("Final Year Project - Automated Field Extraction")

st.sidebar.subheader("Image Preprocessing")
apply_grayscale = st.sidebar.checkbox("Convert to Grayscale", value=True)
apply_threshold = st.sidebar.checkbox("Apply Adaptive Threshold", value=False)
apply_denoise = st.sidebar.checkbox("Apply Noise Reduction", value=True)

with st.sidebar.expander("Settings & Config", expanded=False):
    tess_path_input = st.text_input(
        "Tesseract Path:",
        value=detected_path or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    if tess_path_input and os.path.exists(tess_path_input):
        pytesseract.pytesseract.tesseract_cmd = tess_path_input

# image preproccessing and resize
def preprocess_image(pil_img):
    if pil_img.width < 1600:
        pil_img = pil_img.resize((pil_img.width * 2, pil_img.height * 2), Image.Resampling.LANCZOS)

    img_arr = np.array(pil_img)
    
    if len(img_arr.shape) == 3:
        if apply_grayscale:
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
    
    if apply_denoise and len(img_arr.shape) == 2:
        img_arr = cv2.medianBlur(img_arr, 3)
        
    if apply_threshold and len(img_arr.shape) == 2:
        img_arr = cv2.adaptiveThreshold(
            img_arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
    return img_arr

# parse out fields using regex
def extract_fields(text):
    data = {
        "vendor": "Not Detected",
        "date": "Not Detected",
        "invoice_no": "Not Detected",
        "total_amount": "Not Detected"
    }
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    ignore_words = ["invoice", "tax invoice", "bill", "cash receipt", "receipt", "gst", "original"]
    for line in lines[:5]:
        clean_line = line.lower()
        if not any(word in clean_line for word in ignore_words) and len(line) > 2:
            data["vendor"] = line
            break
            
    # regex for dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[.,\s]+\d{1,2}[,\s]+\d{4}\b',
        r'\b\d{1,2}[-\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]+\d{2,4}\b'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["date"] = match.group(0)
            break
            
    inv_patterns = [
        r'(?:Invoice|Inv|Receipt|Bill|Order)[\s#.:\'-]*(?:No|Num|Number|#)[\s.:\'-]*([A-Za-z0-9][A-Za-z0-9._\'-]{2,20})',
        r'(?:Invoice|Receipt|Bill)\s*#\s*([A-Za-z0-9][A-Za-z0-9._\'-]{2,20})',
        r'\bINV[-\s.:]*([0-9A-Za-z]{3,12})\b'
    ]
    for pattern in inv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_no"] = match.group(1).strip()
            break
            
    amount_patterns = [
        r'(?:Grand\s*Total|Total\s*Amount|Net\s*Total|Total\s*Payable|Balance\s*Due)[\s.:]*(?:INR|Rs\.?|[$₹€£])?\s*([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:Total|Amount|Due)[\s.:]*(?:INR|Rs\.?|[$₹€£])?\s*([0-9,]+\.[0-9]{2})',
        r'(?:INR|Rs\.?|[$₹€£])\s*([0-9,]+\.[0-9]{2})'
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["total_amount"] = match.group(1).strip()
            break

    return data

# ui layout
st.title("Automated Invoice OCR & Information Extraction")
st.markdown("Upload an invoice or receipt image to extract vendor name, date, invoice number, and total amount.")

st.write("---")

uploaded_file = st.file_uploader(
    "Choose an invoice image (PNG, JPG, JPEG):", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    raw_img = Image.open(uploaded_file)
    processed_np = preprocess_image(raw_img)
    
    col1, col2 = st.columns([1, 1.2], gap="medium")
    
    with col1:
        st.subheader("Invoice Preview")
        st.image(raw_img, use_container_width=True, caption=uploaded_file.name)
        
        with st.expander("Preprocessed Image View"):
            st.image(processed_np, use_container_width=True, clamp=True)
            
    with col2:
        st.subheader("Extraction Results")
        
        with st.spinner("Processing document with Tesseract OCR..."):
            try:
                ocr_text = pytesseract.image_to_string(processed_np)
                fields = extract_fields(ocr_text)
                
                if not ocr_text.strip():
                    st.warning("No readable text detected. Adjust preprocessing options in sidebar.")
                else:
                    st.success("Extraction completed.")
                    
                st.markdown("#### Review & Verify Extracted Fields")
                vendor_val = st.text_input("Vendor / Company Name:", value=fields["vendor"])
                date_val = st.text_input("Invoice Date:", value=fields["date"])
                inv_no_val = st.text_input("Invoice Number:", value=fields["invoice_no"])
                amount_val = st.text_input("Total Amount:", value=fields["total_amount"])
                
                final_record = {
                    "Vendor Name": vendor_val,
                    "Invoice Date": date_val,
                    "Invoice Number": inv_no_val,
                    "Total Amount": amount_val,
                    "File Name": uploaded_file.name
                }
                
                df = pd.DataFrame([final_record])
                
                st.write("---")
                st.subheader("Export Data")
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                json_data = df.to_json(orient='records', indent=2)
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"invoice_{fields['invoice_no'] or 'extracted'}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with btn_col2:
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"invoice_{fields['invoice_no'] or 'extracted'}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    
            except pytesseract.TesseractNotFoundError:
                st.error("Tesseract-OCR executable not found on the system.")
                st.info(
                    "Please install Tesseract for Windows from: https://github.com/UB-Mannheim/tesseract/wiki\n\n"
                    "Default path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
                )
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")

    if 'ocr_text' in locals() and ocr_text:
        st.write("---")
        with st.expander("View Raw OCR Text Output"):
            st.text_area("Extracted Raw Text:", ocr_text, height=220)

else:
    st.info("Please upload an invoice image above to begin processing.")
    
    st.markdown("### Process Overview:")
    steps_col1, steps_col2, steps_col3 = st.columns(3)
    with steps_col1:
        st.markdown("**1. Upload Image**")
        st.caption("Supports JPG, JPEG, and PNG formats.")
    with steps_col2:
        st.markdown("**2. Preprocessing & OCR**")
        st.caption("Adaptive filtering and optical text recognition.")
    with steps_col3:
        st.markdown("**3. Field Parsing & Export**")
        st.caption("Structured extraction and CSV/JSON export.")
