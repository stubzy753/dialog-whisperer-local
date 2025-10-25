"""Entry point for the Dialog Whisperer MVP."""

def main():
    print("Dialog Whisperer — local MVP starting")
    import os
    import sys
    # Add package root to path if running directly
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    
    # Import GUI lazily so importing package doesn't require GUI deps
    try:
        from dialog_whisperer.gui import start_gui
    except Exception as e:
        print("Failed to import GUI: %s" % e)
        import traceback
        traceback.print_exc()
        return
    start_gui()


if __name__ == "__main__":
    main()
