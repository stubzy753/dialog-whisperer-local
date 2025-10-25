from setuptools import setup, find_packages

setup(
    name="dialog-whisperer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytesseract",
        "pyttsx3",
        "mss",
        "Pillow",
        "numpy",
        "sounddevice",
        "keyboard",
    ],
    python_requires=">=3.10",
)