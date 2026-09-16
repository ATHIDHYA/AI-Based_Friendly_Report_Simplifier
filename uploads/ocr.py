import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import sys
import os

# Add parent directory to path to import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the improved OCR functions from core
from core.extractor import _preprocess_image, TESSERACT_CONFIG


def main():
    # Create hidden Tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open image picker
    image_path = filedialog.askopenfilename(
        title="Choose an image",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.gif"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
    )

    if not image_path:
        print("No image selected.")
        return

    print(f"\nSelected image: {image_path}")
    print("Extracting text...\n")

    try:
        # Use the core extractor module for consistency
        from core.extractor import extract_text
        result = extract_text(image_path)
        
        print("=" * 50)
        print("EXTRACTED TEXT")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
        
        # Show page-by-page breakdown if available
        if len(result["pages"]) > 1:
            print("\n" + "=" * 50)
            print("PAGE-BY-PAGE BREAKDOWN")
            print("=" * 50)
            for page_info in result["pages"]:
                print(f"\n--- Page {page_info['page']} ({page_info['method']}) ---")
                print(page_info["text"][:200] + "..." if len(page_info["text"]) > 200 else page_info["text"])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()