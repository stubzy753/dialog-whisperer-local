"""Utility to load a screenshot, show it, run OCR and optionally speak the text.

Usage:
    python -m scripts.run_screenshot_test --image PATH [--tts]

If --image is not provided a demo image is generated.
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

from dialog_whisperer import ocr
from dialog_whisperer import tts


def make_demo_image(path):
    img = Image.new('RGB', (800, 200), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    try:
        # try to use a built-in truetype font if available
        font = ImageFont.truetype("arial.ttf", 48)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 60), "SCORE: 12345  HP: 78/100", fill=(255, 255, 255), font=font)
    img.save(path)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', '-i', help='Path to screenshot image file')
    parser.add_argument('--tts', action='store_true', help='Speak recognized text (requires pyttsx3)')
    parser.add_argument('--select', action='store_true', help='Interactively select a region from the image before OCR')
    args = parser.parse_args()

    if args.image:
        img_path = args.image
        if not os.path.exists(img_path):
            print(f"Image not found: {img_path}")
            return
    else:
        img_path = os.path.join(os.getcwd(), 'demo_screenshot.png')
        make_demo_image(img_path)
        print(f"Generated demo image at {img_path}")

    img = Image.open(img_path)
    print(f"Opening image: {img_path}")
    # If user requested interactive selection, open a simple Tk window to display image and let user drag
    if args.select:
        try:
            import tkinter as tk
            from PIL import ImageTk

            class ImageSelector:
                def __init__(self, pil_image):
                    self.root = tk.Tk()
                    self.root.title('Select region - drag to select, then release')
                    self.img = pil_image
                    self.tkimg = ImageTk.PhotoImage(self.img)
                    self.canvas = tk.Canvas(self.root, width=self.tkimg.width(), height=self.tkimg.height(), cursor='cross')
                    self.canvas.pack()
                    self.canvas.create_image(0, 0, anchor='nw', image=self.tkimg)
                    self.start_x = None
                    self.start_y = None
                    self.rect = None
                    self.bbox = None
                    self.canvas.bind('<Button-1>', self.on_button_press)
                    self.canvas.bind('<B1-Motion>', self.on_move)
                    self.canvas.bind('<ButtonRelease-1>', self.on_release)

                def on_button_press(self, event):
                    self.start_x = int(event.x)
                    self.start_y = int(event.y)
                    if self.rect:
                        self.canvas.delete(self.rect)
                    self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

                def on_move(self, event):
                    curX, curY = (int(event.x), int(event.y))
                    self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

                def on_release(self, event):
                    end_x, end_y = int(event.x), int(event.y)
                    x1 = min(self.start_x, end_x)
                    y1 = min(self.start_y, end_y)
                    x2 = max(self.start_x, end_x)
                    y2 = max(self.start_y, end_y)
                    self.bbox = (x1, y1, x2, y2)
                    self.root.quit()

                def run(self):
                    # Center window on screen if possible
                    try:
                        self.root.update_idletasks()
                    except Exception:
                        pass
                    self.root.mainloop()

            selector = ImageSelector(img)
            selector.run()
            if selector.bbox:
                print(f"Selected bbox: {selector.bbox}")
                img = img.crop(selector.bbox)
            else:
                print("No selection made; using full image.")
        except Exception as e:
            print(f"Interactive selection unavailable: {e}")
            try:
                img.show()
            except Exception:
                print("(image.show() failed or not supported in this environment)")
    else:
        try:
            img.show()
        except Exception:
            # show may fail in headless environments; continue
            print("(image.show() failed or not supported in this environment)")

    print("Running OCR...")
    try:
        text = ocr.image_to_text(img)
    except Exception as e:
        print(f"OCR failed: {e}")
        return

    print("--- OCR Result ---")
    print(text)
    print("------------------")

    if args.tts and text.strip():
        try:
            print("Speaking recognized text...")
            tts.speak(text)
        except Exception as e:
            print(f"TTS failed: {e}")


if __name__ == '__main__':
    main()
