"""Test GUI and region selector functionality."""

import pytest
import tkinter as tk
from dialog_whisperer import gui, region_selector

def test_gui_imports():
    """Verify GUI modules import."""
    from dialog_whisperer import gui, region_selector
    assert hasattr(gui, 'start_gui')
    assert hasattr(region_selector, 'RegionSelector')

def test_region_selector(monkeypatch):
    """Test region selector callback."""
    called_with = None
    
    def mock_callback(x1, y1, x2, y2):
        nonlocal called_with
        called_with = (x1, y1, x2, y2)
    
    # Mock Tk to avoid actually creating windows
    class MockTk:
        def __init__(self, *args, **kwargs):
            self.calls = []
            self._widgets = []
            
        def attributes(self, *args):
            self.calls.append(('attributes', args))
            return self
            
        def bind(self, event, func):
            self.calls.append(('bind', event, func))
            
        def destroy(self):
            self.calls.append(('destroy',))
            
        def configure(self, **kwargs):
            self.calls.append(('configure', kwargs))
            
        def wait_visibility(self, *args):
            pass
            
        def pack(self, **kwargs):
            pass
            
        def mainloop(self):
            pass

    class MockCanvas(MockTk):
        def __init__(self, master=None, **kwargs):
            super().__init__()
            self.master = master
            self._item_counter = 0
            self._coords = {}
            
        def create_rectangle(self, x1, y1, x2, y2, **kwargs):
            self._item_counter += 1
            self.calls.append(('create_rectangle', (x1, y1, x2, y2), kwargs))
            return self._item_counter
            
        def delete(self, item_id):
            self.calls.append(('delete', item_id))
            
        def coords(self, item_id, *args):
            if args:
                self.calls.append(('coords', item_id, args))
                # store the last set coordinates for the item
                self._coords[item_id] = list(args)
                return self._coords[item_id]
            # return stored coords if available
            return self._coords.get(item_id, [0, 0, 100, 100])  # Dummy coordinates
            
    # Create a mock module for tkinter
    class MockTkModule:
        Tk = MockTk
        Canvas = MockCanvas
        BOTH = 'both'
        
    monkeypatch.setattr('dialog_whisperer.region_selector.tk', MockTkModule)
    
    # Create selector and simulate selection
    selector = region_selector.RegionSelector(mock_callback)
    
    # Simulate mouse events
    class Event:
        def __init__(self, x, y):
            self.x = x
            self.y = y
    
    # Test selection process
    start_event = Event(100, 100)
    selector.start_selection(start_event)
    
    move_event = Event(200, 200)
    selector.update_selection(move_event)
    
    end_event = Event(200, 200)
    selector.finish_selection(end_event)
    
    # Verify callback was called with correct coordinates
    assert called_with == (100, 100, 200, 200), f"Expected (100, 100, 200, 200) but got {called_with}"
    
    assert called_with == (100, 100, 200, 200)