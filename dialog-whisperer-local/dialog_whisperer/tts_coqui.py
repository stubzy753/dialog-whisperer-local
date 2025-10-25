"""Optional Coqui TTS backend (lazy)."""

_TTS = None
_MODEL_NAME = "tts_models/en/ljspeech/glow-tts"


def _ensure_model(model_name=None, use_gpu=False):
    global _TTS, _MODEL_NAME
    if model_name:
        _MODEL_NAME = model_name
    if _TTS is not None:
        return _TTS
    try:
        from TTS.api import TTS
    except Exception as e:
        raise ImportError("Coqui TTS (TTS) package is required: %s" % e)

    # Initialize model (may download weights on first run)
    _TTS = TTS(_MODEL_NAME, progress_bar=False, gpu=use_gpu)
    return _TTS


def _play_wave_bytes(wave_bytes_path):
    """Play a WAV file using the stdlib wave reader and sounddevice (no extra deps)."""
    import wave
    import numpy as np
    import sounddevice as sd

    with wave.open(wave_bytes_path, "rb") as wf:
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        sampwidth = wf.getsampwidth()
        nch = wf.getnchannels()

    # Convert bytes to numpy array
    if sampwidth == 2:
        dtype = np.int16
    elif sampwidth == 4:
        dtype = np.int32
    else:
        # fallback to int16
        dtype = np.int16

    audio = np.frombuffer(frames, dtype=dtype)
    if nch > 1:
        audio = audio.reshape(-1, nch)

    # Normalize to float32 range [-1,1] for sounddevice
    if np.issubdtype(audio.dtype, np.integer):
        max_val = float(2 ** (8 * sampwidth - 1))
        audio = audio.astype('float32') / max_val

    sd.play(audio, sr)
    sd.wait()


def speak(text, model_name=None, use_gpu=False):
    """Synthesize and play text using Coqui TTS.

    Notes:
    - This will download model files on first run if not present.
    - Playback uses sounddevice (already in requirements).
    """
    import tempfile
    import os

    tts = _ensure_model(model_name=model_name, use_gpu=use_gpu)

    # Try to get waveform directly
    try:
        res = tts.tts(text)
        # res may be (wav, sr) or numpy array
        if isinstance(res, tuple) and len(res) == 2:
            wav, sr = res
            import sounddevice as sd
            sd.play(wav, sr)
            sd.wait()
            return
        elif hasattr(res, "dtype"):
            # assume numpy array, assume 22050Hz
            import sounddevice as sd
            sd.play(res, 22050)
            sd.wait()
            return
    except Exception:
        # Fall back to writing to a temporary wav file
        pass

    # Use tts.tts_to_file or synth to file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_path = tf.name

    try:
        # prefer tts.tts_to_file if available
        if hasattr(tts, "tts_to_file"):
            tts.tts_to_file(text=text, file_path=tmp_path)
        elif hasattr(tts, "synth_to_file"):
            tts.synth_to_file(texts=[text], file_path=tmp_path)
        else:
            # last resort: try tts.tts_to_file_v2
            tts.tts_to_file(text=text, file_path=tmp_path)

        _play_wave_bytes(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
