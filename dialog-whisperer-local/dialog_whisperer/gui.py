"""Minimal Tkinter UI: draggable capture box and basic controls.

This provides a simple MVP GUI that lets you draw a capture rectangle and run OCR+TTS.
Dependencies are lazy-imported when used so the module imports cleanly without external packages.
Hotkeys:
- Alt+Shift+C: Capture and read text
- Alt+Shift+S: Stop/resume reading
- Alt+Shift+H: Show/hide settings
"""

# Default hotkeys (can be changed via settings or env vars)
_DEFAULT_HOTKEYS = {
    "capture": "alt+shift+c",
    "toggle_speak": "alt+shift+s",
    "toggle_settings": "alt+shift+h"
}

# HotkeySettings uses tkinter, so it's created inside start_gui after tk is imported.

def _setup_hotkeys(capture_fn, toggle_speak_fn):
    """Setup global hotkeys. Returns cleanup function to unregister."""
    try:
        import keyboard
        import os
    except Exception as e:
        print("Hotkeys disabled - keyboard module not available: %s" % e)
        return lambda: None

    registered_hotkeys = []
    for key, default in _DEFAULT_HOTKEYS.items():
        try:
            hotkey = os.environ.get(f"DIALOG_WHISPER_HOTKEY_{key.upper()}", default)
            if key == "capture":
                keyboard.add_hotkey(hotkey, capture_fn)
            elif key == "toggle_speak":
                keyboard.add_hotkey(hotkey, toggle_speak_fn)
            # toggle_settings is handled by Tkinter bindings
            print(f"Hotkey registered: {hotkey} = {key.replace('_', ' ').title()}")
            registered_hotkeys.append(hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {key}: {e}")
    
    def cleanup():
        try:
            import keyboard
            keyboard.unhook_all()  # Remove all hotkeys at once
        except:
            pass
    
    return cleanup

def start_gui():
    try:
        import tkinter as tk
        from tkinter import messagebox
        import os
        from collections import deque
        import time
        import threading
        import queue
        import atexit
    except Exception as e:
        raise ImportError("Tkinter is required for GUI: %s" % e)

    class HotkeySettings:
        """Simple settings dialog for hotkeys."""
        def __init__(self, parent):
            self.window = tk.Toplevel(parent)
            self.window.title("Hotkey Settings")
            self.window.geometry("300x200")
            self.window.transient(parent)
            self.window.protocol("WM_DELETE_WINDOW", self.hide)
            
            # Settings grid
            tk.Label(self.window, text="Hotkeys", font=('Arial', 12, 'bold')).pack(pady=10)
            frame = tk.Frame(self.window)
            frame.pack(fill=tk.BOTH, expand=True, padx=20)
            
            self.entries = {}
            row = 0
            for key, default in _DEFAULT_HOTKEYS.items():
                tk.Label(frame, text=f"{key.replace('_', ' ').title()}:").grid(row=row, column=0, sticky='e', pady=4)
                entry = tk.Entry(frame, width=15)
                entry.insert(0, os.environ.get(f"DIALOG_WHISPER_HOTKEY_{key.upper()}", default))
                entry.grid(row=row, column=1, padx=10)
                self.entries[key] = entry
                row += 1
                
            tk.Button(self.window, text="Save", command=self.save).pack(pady=10)
            self.window.withdraw()
            
        def show(self):
            self.window.deiconify()
            
        def hide(self):
            self.window.withdraw()
            
        def save(self):
            for key, entry in self.entries.items():
                os.environ[f"DIALOG_WHISPER_HOTKEY_{key.upper()}"] = entry.get()
            self.hide()

    from . import capture, ocr, tts
    from . import region_selector

    # Initialize tkinter before class definitions
    global root
    root = tk.Tk()
    root.title("Dialog Whisperer — Local MVP")
    root.geometry("420x180")  # Made taller for hotkey info

    coords = {"x1": 100, "y1": 100, "x2": 500, "y2": 300}
    speaking_enabled = {"value": True}  # Use dict for mutable state
    settings_dialog = HotkeySettings(root)

    # State tracking
    state = {
        "monitoring": False,
        "speaking": False,
        "last_text": None,
        "last_activity": time.time(),
        "text_queue": queue.Queue(),
        "conversation_timeout": 20,  # seconds before considering conversation ended
        "reference_image": None,
        "ui_visible": True,
        "bbox": None
    }
    
    def capture_text():
        """Capture and process text from the selected region."""
        try:
            img = capture.capture_region((coords["x1"], coords["y1"], coords["x2"], coords["y2"]))
            return ocr.image_to_text(img).strip()
        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def monitor_text():
        """Background thread to monitor for text changes."""
        last_text = None
        last_image = None
        while state["monitoring"]:
            if not speaking_enabled["value"]:
                time.sleep(0.5)
                continue
                
            # Capture current region
            try:
                current_image = capture.capture_region((coords["x1"], coords["y1"], coords["x2"], coords["y2"]))
                
                # If we have a reference image for the UI, compare current image
                if state["reference_image"] is not None:
                    state["ui_visible"] = capture.compare_images(current_image, state["reference_image"])
                    
                # If UI is visible, don't process text
                if state["ui_visible"]:
                    time.sleep(0.5)
                    continue
                    
                # Process text only when UI is not visible
                current_text = ocr.image_to_text(current_image).strip()
                if current_text and current_text != last_text:
                    state["last_activity"] = time.time()
                    state["text_queue"].put(current_text)
                    last_text = current_text
                
                # Check for conversation timeout
                if time.time() - state["last_activity"] > state["conversation_timeout"]:
                    last_text = None  # Reset for new conversation
            except Exception as e:
                print(f"Monitor error: {e}")
                
            time.sleep(0.5)  # Poll interval
    
    def speak_queue():
        """Background thread to speak queued text sequentially."""
        while state["monitoring"]:
            try:
                # Wait for text in the queue
                text = state["text_queue"].get(timeout=0.5)
                if text:
                    state["speaking"] = True
                    update_speaking_buttons()
                    tts.speak(text)
                    state["speaking"] = False
                    update_speaking_buttons()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Speech error: {e}")
                state["speaking"] = False
                update_speaking_buttons()
    
    def start_monitoring():
        """Start continuous text monitoring."""
        if state["monitoring"]:
            return
            
        if not speaking_enabled["value"]:
            messagebox.showinfo("Speaking Disabled", "Speaking is currently disabled (Alt+Shift+S to enable)")
            return
        
        # Initial capture to verify region has text
        initial_text = capture_text()
        if not initial_text:
            messagebox.showinfo("OCR Result", "No text detected in selected region")
            return
            
        state["monitoring"] = True
        state["text_queue"].put(initial_text)  # Queue initial text
        
        # Start monitoring and speaking threads
        threading.Thread(target=monitor_text, daemon=True).start()
        threading.Thread(target=speak_queue, daemon=True).start()
        
        # Update UI
        btn_start.config(text="Monitoring...", state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)
        if minimize_var.get():
            root.iconify()
    
    def capture_ui_reference():
        """Capture a reference image of the UI for comparison."""
        if state["bbox"] is None:
            messagebox.showinfo("Error", "Please select a region first")
            return
            
        try:
            state["reference_image"] = capture.capture_region((coords["x1"], coords["y1"], coords["x2"], coords["y2"]))
            messagebox.showinfo("Success", "UI reference image captured. Text will be read only when the UI is not visible.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture reference UI: {e}")

    def stop_monitoring():
        """Stop text monitoring and speech."""
        state["monitoring"] = False
        state["speaking"] = False
        # Clear queue
        while not state["text_queue"].empty():
            state["text_queue"].get()
        
        # Update UI
    def stop_monitoring():
        """Stop text monitoring and speech."""
        try:
            state["monitoring"] = False
            state["speaking"] = False
            # Clear queue
            while not state["text_queue"].empty():
                state["text_queue"].get()
            
            # Update UI
            btn_start.config(text="Start Monitoring", state=tk.NORMAL)
            btn_stop.config(state=tk.DISABLED)
            root.deiconify()  # Restore window
            update_speaking_buttons()
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def toggle_speaking():
        speaking_enabled["value"] = not speaking_enabled["value"]
        state["speaking"] = False  # Reset speaking state
        status = "enabled" if speaking_enabled["value"] else "disabled"
        status_label.config(text=f"Speaking: {'ON' if speaking_enabled['value'] else 'OFF'}", 
                          fg='green' if speaking_enabled['value'] else 'red')
        update_speaking_buttons()
        print(f"Speaking {status}")
    
    def update_speaking_buttons():
        """Update button states based on speaking status"""
        has_valid_region = (coords["x1"] != coords["x2"] and coords["y1"] != coords["y2"])
        
        # Update main control buttons
        if state["monitoring"]:
            btn_start.config(state=tk.DISABLED)
            btn_stop.config(state=tk.NORMAL)
        else:
            btn_start.config(state=tk.NORMAL if has_valid_region else tk.DISABLED)
            btn_stop.config(state=tk.DISABLED)
    
    def pause_speaking():
        """Stop current speech and restore window"""
        state["speaking"] = False
        update_speaking_buttons()
        root.deiconify()
    
    def toggle_settings():
        if settings_dialog.window.winfo_ismapped():
            settings_dialog.hide()
        else:
            settings_dialog.show()

    # Add hotkey info frame at top
    info_frame = tk.Frame(root)
    info_frame.pack(fill=tk.X, padx=10, pady=4)
    
    # Add speaking status label
    status_label = tk.Label(info_frame, text="Speaking: ON", fg='green')
    status_label.pack(side=tk.RIGHT, padx=10)
    
    hotkeys_text = "Hotkeys:\\n"
    for key, default in _DEFAULT_HOTKEYS.items():
        hotkey = os.environ.get(f"DIALOG_WHISPER_HOTKEY_{key.upper()}", default)
        hotkeys_text += f"  {hotkey.upper()} = {key.replace('_', ' ').title()}\\n"
    
    tk.Label(info_frame, text=hotkeys_text, fg='blue', justify=tk.LEFT).pack(side=tk.LEFT)
    
    # Setup global hotkey
    cleanup_hotkeys = _setup_hotkeys(
        lambda: start_monitoring() if not state["monitoring"] else None,
        toggle_speaking
    )
    root.bind("<Destroy>", lambda e: (state.update(monitoring=False), cleanup_hotkeys()))  # Clean up on window close

    # (region label will be updated after it's created)

    # Region frame with preview
    region_frame = tk.Frame(root)
    region_frame.pack(padx=8, pady=4, fill=tk.X)

    # Region info label shows current coordinates
    def update_region_label():
        """Update the label with current region coordinates."""
        region_label.config(
            text=f"Capture Region: ({coords['x1']}, {coords['y1']}) to ({coords['x2']}, {coords['y2']})"
        )

    region_label = tk.Label(region_frame, text="Click 'Select Region' to choose capture area")
    region_label.pack(pady=4)
    # initialize label text
    update_region_label()

    def on_region_selected(x1, y1, x2, y2):
        """Handle new region selection."""
        coords.update({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
        state["bbox"] = (x1, y1, x2, y2)
        state["reference_image"] = None  # Reset reference image when region changes
        update_region_label()
        # Enable monitoring when region is selected
        update_speaking_buttons()

    def select_region():
        """Open the region selector overlay."""
        try:
            # Minimize main window during selection if requested
            if minimize_var.get():
                root.iconify()
            selector = region_selector.RegionSelector(on_region_selected)
            selector.root.mainloop()
        finally:
            # Only restore if window still exists
            try:
                if root.winfo_exists():
                    root.deiconify()
                    root.focus_force()  # Bring window to front after selection
            except:
                pass

    # Select region button
    tk.Button(region_frame, text="Select Region", command=select_region).pack()

    # Button frame
    # Button frame
    btn_frame = tk.Frame(root)
    btn_frame.pack(padx=8, fill=tk.X)

    # Left side controls
    left_frame = tk.Frame(btn_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.X)

    # Main control buttons
    btn_start = tk.Button(left_frame, text="Start Monitoring", command=start_monitoring, state=tk.DISABLED)
    btn_start.pack(side=tk.LEFT, padx=4)

    btn_stop = tk.Button(left_frame, text="Stop", command=stop_monitoring, state=tk.DISABLED)
    btn_stop.pack(side=tk.LEFT, padx=4)

    # Minimize checkbox
    minimize_var = tk.BooleanVar(value=True)
    tk.Checkbutton(left_frame, text="Minimize on Start", variable=minimize_var).pack(side=tk.LEFT, padx=4)

    # Right side buttons
    right_frame = tk.Frame(btn_frame)
    right_frame.pack(side=tk.RIGHT)

    btn_capture_ui = tk.Button(right_frame, text="Capture UI", command=capture_ui_reference)
    btn_capture_ui.pack(side=tk.RIGHT, padx=4)

    btn_settings = tk.Button(right_frame, text="Settings", command=toggle_settings)
    btn_settings.pack(side=tk.RIGHT, padx=4)

    def cleanup():
        """Clean up resources on exit."""
        state["monitoring"] = False
        state["speaking"] = False
        
        # Clean up hotkeys
        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass
            
        # Clean up TTS
        try:
            from . import tts
            tts.cleanup()
        except:
            pass
        
        # Ensure window is destroyed properly
        try:
            root.quit()
            root.destroy()
        except:
            pass

    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", lambda: cleanup() or root.quit())
    
    try:
        root.mainloop()
    finally:
        cleanup()  # Ensure cleanup happens
