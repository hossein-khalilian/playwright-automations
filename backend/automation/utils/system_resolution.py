import re
import subprocess
from typing import Dict


def get_system_resolution() -> Dict[str, int]:
    """
    Get the system's primary screen resolution.
    Tries multiple methods for cross-platform compatibility.
    Returns a dict with 'width' and 'height', or defaults to 1920x1080.
    """
    # Method 1: Try using tkinter (cross-platform, usually available)
    try:
        import tkinter as tk

        root = tk.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        if width > 0 and height > 0:
            print(f"[*] Detected system resolution: {width}x{height} (via tkinter)")
            return {"width": width, "height": height}
    except Exception:
        pass

    # Method 2: Try xrandr on Linux/X11
    try:
        result = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            # Parse xrandr output for primary display
            for line in result.stdout.split("\n"):
                if " connected" in line and "primary" in line:
                    # Extract resolution from line like: "1920x1080     60.00*+"
                    match = re.search(r"(\d+)x(\d+)", line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        print(
                            f"[*] Detected system resolution: {width}x{height} (via xrandr)"
                        )
                        return {"width": width, "height": height}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Method 3: Try xdpyinfo on Linux/X11
    try:
        result = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            # Parse xdpyinfo output
            for line in result.stdout.split("\n"):
                if "dimensions:" in line:
                    match = re.search(r"(\d+)x(\d+)", line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        print(
                            f"[*] Detected system resolution: {width}x{height} (via xdpyinfo)"
                        )
                        return {"width": width, "height": height}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Default fallback
    print("[*] Could not detect system resolution, using default: 1920x1080")
    return {"width": 1920, "height": 1080}
