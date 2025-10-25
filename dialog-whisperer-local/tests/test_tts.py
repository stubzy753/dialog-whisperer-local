"""Test TTS functionality."""

import pytest
from dialog_whisperer import tts

def test_tts_imports():
    """Verify TTS module imports."""
    from dialog_whisperer import tts
    assert hasattr(tts, 'speak')

def test_tts_missing_pyttsx3(monkeypatch):
    """Test graceful failure when pyttsx3 import fails."""
    def mock_import(*args):
        raise ImportError("pyttsx3 not found")
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    with pytest.raises(ImportError) as exc:
        tts.speak("test")
    assert "pyttsx3 not found" in str(exc.value)

def test_tts_backend_env_var(monkeypatch):
    """Test TTS backend selection via environment variable."""
    monkeypatch.setenv("DIALOG_WHISPER_TTS_BACKEND", "invalid")
    # Ensure deterministic behavior: mock pyttsx3 import to force ImportError
    import builtins
    real_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'pyttsx3':
            raise ImportError("pyttsx3 not found")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', mock_import)
    with pytest.raises(ImportError):
        tts.speak("test")