"""Test OCR functionality."""

import pytest
from PIL import Image
import io
from dialog_whisperer import ocr

def test_ocr_imports():
    """Verify OCR module imports."""
    from dialog_whisperer import ocr
    assert hasattr(ocr, 'image_to_text')

def test_ocr_empty_image():
    """Test OCR on blank image returns empty string."""
    # Create a blank white image
    img = Image.new('RGB', (100, 50), 'white')
    text = ocr.image_to_text(img)
    assert text.strip() == ""

def test_ocr_missing_tesseract(monkeypatch):
    """Test graceful failure when tesseract import fails."""
    # Mock builtins.__import__ to raise ImportError only for pytesseract
    import builtins
    real_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'pytesseract':
            raise ImportError("Tesseract not found")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', mock_import)

    img = Image.new('RGB', (100, 50), 'white')
    with pytest.raises(ImportError) as exc:
        ocr.image_to_text(img)
    assert "Tesseract not found" in str(exc.value)