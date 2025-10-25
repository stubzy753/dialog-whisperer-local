"""Draggable screen region selector with transparent overlay."""

import tkinter as tk

class RegionSelector:
    """Transparent overlay window for selecting screen regions by dragging."""
    
    def __init__(self, callback):
        """Create a full-screen transparent window for region selection.
        
        Args:
            callback: Function to call with (x1, y1, x2, y2) coordinates when selection completes
        """
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.3)  # semi-transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        # Make it look like a selection overlay
        self.root.configure(bg='gray')
        self.root.wait_visibility(self.root)
        
        # Selection canvas (transparent)
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.configure(bg='gray')
        
        # Track selection state
        self.start_x = None
        self.start_y = None
        self.selection = None
        self.callback = callback
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.finish_selection)
        
        # Escape key closes without selection
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
    def start_selection(self, event):
        """Start drawing selection rectangle."""
        self.start_x = event.x
        self.start_y = event.y
        if self.selection:  # Clear any existing selection
            self.canvas.delete(self.selection)
        self.selection = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='white'
        )
        
    def update_selection(self, event):
        """Update selection rectangle as mouse moves."""
        if self.selection:
            self.canvas.coords(self.selection,
                self.start_x, self.start_y, event.x, event.y)
            
    def finish_selection(self, event):
        """Complete selection and return coordinates."""
        if self.selection:
            x1, y1, x2, y2 = self.canvas.coords(self.selection)
            # Convert to screen coordinates
            x1, x2 = int(min(x1, x2)), int(max(x1, x2))
            y1, y2 = int(min(y1, y2)), int(max(y1, y2))
            self.root.destroy()
            if self.callback:
                self.callback(x1, y1, x2, y2)