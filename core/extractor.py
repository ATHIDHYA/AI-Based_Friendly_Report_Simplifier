"""
extractor.py
------------
Turns an uploaded medical report (PDF or image) into plain text, so the
NER + simplification modules have something to work with.

Two situations, two strategies:

1. DIGITAL PDF (text is embedded, like a Word export or lab-generated report)
   -> pdfplumber can just "read" the text directly. Fast and 100% accurate.

2. SCANNED PDF or IMAGE (it's really just a photo/scan of a paper report)
   -> There's no embedded text at all, just pixels. We render each page as an
      image and run Tesseract OCR on it -- the same tech that lets your phone
      "read" a business card photo and turn it into contacts.

We don't ask the user which type they uploaded -- we detect it automatically:
if pdfplumber finds barely any text on a page, we assume it's a scanned image
and fall back to OCR for that page.
"""

from pathlib import Path

import fitz  # PyMuPDF, used to rasterize PDF pages for OCR
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# If a page has fewer than this many characters of extractable text,
# we treat it as "scanned" and run OCR instead.
MIN_CHARS_FOR_DIGITAL_PAGE = 20

# Tesseract configuration for better medical report OCR
TESSERACT_CONFIG = r'--oem 3 --psm 6 -l eng+fra+spa+deu'  # Support multiple languages common in medical reports


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy for medical reports.
    - Convert to grayscale
    - Enhance contrast
    - Apply slight sharpening
    - Remove noise
    """
    # Convert to grayscale for better OCR
    if img.mode != 'L':
        img = img.convert('L')
    
    # Enhance contrast to make text stand out
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Apply slight sharpening
    img = img.filter(ImageFilter.SHARPEN)
    
    # Remove noise (median filter)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    return img


def _ocr_page_with_pymupdf(pdf_path: str, page_number: int, zoom: float = 2.0) -> str:
    """Renders a single PDF page to an image and runs Tesseract OCR on it."""
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    # Zoom in before OCR -- higher resolution = much better OCR accuracy,
    # the same way zooming in on a blurry photo before reading small text helps.
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    
    # Preprocess image for better OCR
    processed_img = _preprocess_image(img)
    
    return pytesseract.image_to_string(processed_img, config=TESSERACT_CONFIG)


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extracts text from a PDF, page by page, automatically choosing between
    direct text extraction and OCR depending on the page.

    Returns:
        {
            "text": "<full combined report text>",
            "pages": [ {"page": 1, "method": "digital", "text": "..."}, ... ]
        }
    """
    pages_info = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            digital_text = (page.extract_text() or "").strip()

            if len(digital_text) >= MIN_CHARS_FOR_DIGITAL_PAGE:
                pages_info.append({"page": i + 1, "method": "digital", "text": digital_text})
            else:
                ocr_text = _ocr_page_with_pymupdf(pdf_path, i).strip()
                pages_info.append({"page": i + 1, "method": "ocr", "text": ocr_text})

    full_text = "\n".join(p["text"] for p in pages_info)
    return {"text": full_text, "pages": pages_info}


def extract_text_from_image(image_path: str) -> dict:
    """For when the user uploads a raw image (JPG/PNG) instead of a PDF."""
    try:
        img = Image.open(image_path)
        
        # Preprocess image for better OCR
        processed_img = _preprocess_image(img)
        
        # Run OCR with improved configuration
        text = pytesseract.image_to_string(processed_img, config=TESSERACT_CONFIG).strip()
        
        return {"text": text, "pages": [{"page": 1, "method": "ocr", "text": text}]}
    except Exception as e:
        # Fallback: try without preprocessing if preprocessing fails
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img).strip()
            return {"text": text, "pages": [{"page": 1, "method": "ocr_fallback", "text": text}]}
        except Exception as fallback_error:
            raise ValueError(f"Failed to extract text from image: {e}. Fallback also failed: {fallback_error}")


def extract_text(file_path: str) -> dict:
    """
    Main entry point -- routes to the right extractor based on file extension.
    This is the function the Flask upload route will call.
    """
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp", ".gif"}:
        return extract_text_from_image(file_path)
    elif suffix == ".txt":
        text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        return {"text": text, "pages": [{"page": 1, "method": "text_file", "text": text}]}
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        print(f"--- Extracted ({len(result['pages'])} page(s)) ---")
        for p in result["pages"]:
            print(f"[Page {p['page']} | method: {p['method']}]")
        print("\n--- Full text ---")
        print(result["text"])
    else:
        print("Usage: python extractor.py <path_to_pdf_or_image>")