"""Test the enhanced monitoring and text processing functionality."""

import pytest
import time
import queue
import tkinter as tk
from unittest.mock import MagicMock, patch
from PIL import Image
import threading

from dialog_whisperer import gui, ocr, tts, capture

@pytest.fixture
def mock_root():
    with patch('tkinter.Tk') as mock:
        instance = mock.return_value
        instance.title = MagicMock()
        instance.geometry = MagicMock()
        instance.iconify = MagicMock()
        instance.deiconify = MagicMock()
        yield instance

@pytest.fixture
def mock_capture():
    with patch('dialog_whisperer.capture.capture_region') as mock_capture:
        # Create a simple test image
        test_image = Image.new('RGB', (100, 30), color='white')
        mock_capture.return_value = test_image
        yield mock_capture

@pytest.fixture
def mock_ocr():
    with patch('dialog_whisperer.ocr.image_to_text') as mock_ocr:
        yield mock_ocr

@pytest.fixture
def mock_tts():
    with patch('dialog_whisperer.tts.speak') as mock_tts:
        yield mock_tts

def test_text_monitoring_startup(mock_root, mock_capture, mock_ocr, mock_tts):
    """Test that text monitoring starts correctly."""
    mock_ocr.return_value = "Initial test text"
    
    # Initialize GUI
    app = gui.start_gui()
    
    # Simulate region selection
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    
    # Start monitoring
    app.start_monitoring()
    
    # Verify initial state
    assert app.state["monitoring"] == True
    assert not app.state["text_queue"].empty()
    assert mock_capture.called
    assert mock_ocr.called
    
    # Clean up
    app.stop_monitoring()

def test_conversation_timeout(mock_root, mock_capture, mock_ocr, mock_tts):
    """Test conversation timeout detection."""
    mock_ocr.side_effect = ["First text", "", "New conversation"]
    
    app = gui.start_gui()
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    app.state["conversation_timeout"] = 2  # Shorter timeout for testing
    
    app.start_monitoring()
    
    # Wait for timeout
    time.sleep(3)
    
    # Simulate new text
    mock_ocr.return_value = "New conversation"
    
    # Verify timeout was detected
    assert app.state["last_text"] is None
    
    app.stop_monitoring()

def test_text_queue_processing(mock_root, mock_capture, mock_ocr, mock_tts):
    """Test that text is queued and processed in order."""
    texts = ["First line", "Second line", "Third line"]
    spoken_texts = []
    
    mock_ocr.side_effect = texts
    mock_tts.side_effect = lambda text: spoken_texts.append(text)
    
    app = gui.start_gui()
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    
    app.start_monitoring()
    
    # Wait for processing
    time.sleep(2)
    
    # Verify texts were spoken in order
    assert spoken_texts == texts
    
    app.stop_monitoring()

def test_gui_state_management(mock_root, mock_capture, mock_ocr, mock_tts):
    """Test GUI button states and window management."""
    app = gui.start_gui()
    
    # Initially, start button should be disabled
    assert app.btn_start["state"] == tk.DISABLED
    
    # After region selection
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    app.on_region_selected(0, 0, 100, 100)
    assert app.btn_start["state"] == tk.NORMAL
    
    # During monitoring
    app.start_monitoring()
    assert app.btn_start["state"] == tk.DISABLED
    assert app.btn_stop["state"] == tk.NORMAL
    
    # After stopping
    app.stop_monitoring()
    assert app.btn_start["state"] == tk.NORMAL
    assert app.btn_stop["state"] == tk.DISABLED

def test_clear_region(mock_root):
    """Test region clearing functionality."""
    app = gui.start_gui()
    
    # Set initial region
    app.coords = {"x1": 10, "y1": 20, "x2": 30, "y2": 40}
    
    # Clear region
    app.clear_region()
    
    # Verify region was cleared
    assert app.coords["x1"] == 0
    assert app.coords["y1"] == 0
    assert app.coords["x2"] == 0
    assert app.coords["y2"] == 0
    assert app.btn_start["state"] == tk.DISABLED

def test_minimize_preference(mock_root, mock_capture, mock_ocr):
    """Test minimize on start preference."""
    app = gui.start_gui()
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    
    # Test with minimize enabled
    app.minimize_var.set(True)
    app.start_monitoring()
    assert mock_root.iconify.called
    app.stop_monitoring()
    
    # Test with minimize disabled
    mock_root.iconify.reset_mock()
    app.minimize_var.set(False)
    app.start_monitoring()
    assert not mock_root.iconify.called
    app.stop_monitoring()

@pytest.mark.integration
def test_full_monitoring_cycle(mock_root, mock_capture, mock_ocr, mock_tts):
    """Integration test for a full monitoring cycle."""
    conversation = [
        "Hello there!",
        "How are you?",
        "",  # Simulated pause
        "Starting new conversation",
    ]
    mock_ocr.side_effect = conversation
    
    app = gui.start_gui()
    app.coords = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    app.state["conversation_timeout"] = 1  # Short timeout for testing
    
    # Start monitoring
    app.start_monitoring()
    
    # Let it run through the conversation
    time.sleep(4)
    
    # Verify all text was processed
    assert mock_tts.call_count == 3  # Empty string should be skipped
    
    # Verify conversation timeout was detected
    assert app.state["last_text"] is None
    
    app.stop_monitoring()