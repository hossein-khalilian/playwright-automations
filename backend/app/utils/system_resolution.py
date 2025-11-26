import tkinter as tk
from typing import Dict


def get_system_resolution() -> Dict[str, int]:
    """
    Get the system's primary screen resolution.
    Tries multiple methods for cross-platform compatibility.
    Returns a dict with 'width' and 'height', or defaults to 1920x1080.
    """
    # Method 1: Try using tkinter (cross-platform, usually available)
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        if width > 0 and height > 0:
            print(f"[*] Detected system resolution: {width}x{height} (via tkinter)")
            return {"width": width, "height": height}
    except Exception:
        pass

    print("[*] Could not detect system resolution, using default: 1920x1080")
    return {"width": 1920, "height": 1080}


if __name__ == "__main__":
    print(get_system_resolution())
