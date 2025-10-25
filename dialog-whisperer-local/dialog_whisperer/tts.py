"""Small TTS helper using pyttsx3 with lazy import."""


_engine = None

def _get_engine():
    """Get or initialize the TTS engine."""
    global _engine
    if _engine is None:
        # Allow optional Coqui backend via environment variable
        import os
        backend = os.environ.get("DIALOG_WHISPER_TTS_BACKEND", "pyttsx3").lower()
        if backend == "coqui":
            try:
                from . import tts_coqui
                return tts_coqui
            except Exception as e:
                print("Coqui TTS backend requested but failed to load: %s" % e)

        try:
            import pyttsx3
            _engine = pyttsx3.init()
        except Exception as e:
            raise ImportError("pyttsx3 is required for TTS: %s" % e)
    return _engine

def speak(text, rate=None, volume=None):
    """Speak text using pyttsx3. Lazy-imports pyttsx3 so file is safe to import without deps.

    Args:
        text (str): text to speak
        rate (int|None): optional speech rate
        volume (float|None): volume 0.0-1.0
    """
    engine = _get_engine()
    
    # Handle Coqui TTS differently
    if hasattr(engine, 'speak'):  # Coqui TTS module
        return engine.speak(text)
        
    # pyttsx3 engine
    if rate is not None:
        engine.setProperty("rate", rate)
    if volume is not None:
        engine.setProperty("volume", float(volume))
    engine.say(text)
    engine.runAndWait()

def cleanup():
    """Clean up TTS resources."""
    global _engine
    if _engine is not None:
        try:
            _engine.stop()
        except:
            pass
        _engine = None
