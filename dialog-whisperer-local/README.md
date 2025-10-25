# Dialog Whisperer — Local, Offline MVP

This is a minimal, fully local MVP of "Dialog Whisperer" for VS Code.

Features
- Offline OCR via Tesseract (`pytesseract`) — requires system Tesseract install.
- Offline TTS via `pyttsx3`.
- Fast screen capture with `mss`.
- Simple Tkinter UI for draggable capture box and controls.

Requirements
- Python 3.10+
- Install Tesseract separately:
  - Windows: install Tesseract from the official binary (add to PATH)
  - macOS: `brew install tesseract`
  - Linux: use your package manager, e.g. `sudo apt install tesseract-ocr`

Python dependencies are listed in `requirements.txt`.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Ensure tesseract is installed and on PATH, then:
python -m dialog_whisperer.main
```

Notes
- The code uses lazy imports so you can inspect the files without all deps installed.
- This is an MVP scaffold for local use. Follow-up: hotkeys, voice detection, styles, and tests.
