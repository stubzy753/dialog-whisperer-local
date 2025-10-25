"""Test screen capture functionality."""

import pytest
from PIL import Image
from dialog_whisperer import capture

def test_capture_imports():
    """Verify capture module imports."""
    from dialog_whisperer import capture
    assert hasattr(capture, 'capture_region')

def test_capture_invalid_bbox():
    """Test capture with invalid bounding box."""
    # Negative coordinates should be adjusted
    img = capture.capture_region((-100, -100, 100, 100))
    assert isinstance(img, Image.Image)
    
    # Zero-size regions should raise ValueError
    with pytest.raises(ValueError):
        capture.capture_region((100, 100, 100, 100))

def test_capture_missing_deps(monkeypatch):
    """Test graceful failure when mss/PIL imports fail."""
    def mock_import(*args):
        raise ImportError("mss not found")
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    with pytest.raises(ImportError) as exc:
        capture.capture_region((0, 0, 100, 100))
    assert "mss" in str(exc.value)