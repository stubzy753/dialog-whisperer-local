"""Simple wrapper around pytesseract with lazy import."""

def image_to_text(pil_image):
    """Run OCR on a PIL image and return text. If pytesseract is missing, raises ImportError.

    Args:
        pil_image: PIL.Image instance

    Returns:
        str: recognized text (may be empty)
        
    Raises:
        ImportError: If pytesseract is not available
    """
    try:
        import pytesseract
        from PIL import ImageStat
        import os
        
        # Check common Windows installation path
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"Debug: Found Tesseract at {tesseract_path}")
        else:
            print("Debug: Tesseract not found in Program Files, will try PATH")
    except ImportError as e:
        if "pytesseract" in str(e):
            raise ImportError(
                "Tesseract not found. Please install Tesseract OCR:\n"
                "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Install to C:\\Program Files\\Tesseract-OCR\n"
                "3. Restart the application"
            )
        raise ImportError(str(e))

    # Check if image is blank or nearly blank
    stat = ImageStat.Stat(pil_image)
    if len(stat.mean) >= 3:  # RGB or RGBA image
        # Check if image is mostly white
        if all(x > 250 for x in stat.mean[:3]):  # Check RGB channels
            print("Debug: Image appears to be blank (mostly white)")
            return ""

    try:
        # Try to get tesseract version to confirm it's working
        version = pytesseract.get_tesseract_version()
        print(f"Debug: Tesseract version {version}")
        
        # Save debug image to see what's being processed
        debug_path = "ocr_debug.png"
        pil_image.save(debug_path)
        print(f"Debug: Saved capture to {debug_path}")
        
        text = pytesseract.image_to_string(pil_image)
        if not text.strip():
            print("Debug: OCR returned no text")
        else:
            print(f"Debug: OCR found text ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"Debug: OCR failed - {str(e)}")
        return ""
