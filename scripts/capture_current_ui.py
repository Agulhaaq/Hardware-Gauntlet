import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hwscan.gui import HardwareGauntletGUI

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]

def capture_widget(widget, filename):
    widget.update()
    hwnd = widget.winfo_id()
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    hwnd_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    old_bmp = gdi32.SelectObject(mem_dc, bitmap)

    user32.PrintWindow(hwnd, mem_dc, 2)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(bmi), 0)

    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    im.save(filename)

    gdi32.SelectObject(mem_dc, old_bmp)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)

def run_captures():
    gui = HardwareGauntletGUI()
    orig_run_tkinter = gui._run_tkinter

    def patched_run_tkinter():
        orig_mainloop = tk.Tk.mainloop
        def custom_mainloop(root_win):
            def execute_and_capture():
                theme_btn = None
                scan_btn = None
                channel_btn = None

                for child in root_win.winfo_children():
                    for sub in child.winfo_children():
                        for btn in sub.winfo_children():
                            if hasattr(btn, "text"):
                                txt = getattr(btn, "text", "")
                                if "SCAN" in txt and not scan_btn:
                                    scan_btn = btn
                                if "LIGHT" in txt or "DARK" in txt:
                                    theme_btn = btn
                                if "UPDATE" in txt:
                                    channel_btn = btn

                # Trigger real hardware scan synchronously
                report = gui.engine.run_full_scan()
                # Find and call update_ui_with_report through scan_btn or simulated callback
                # We can call the button command which starts background thread, or wait for report
                if scan_btn and scan_btn.command:
                    scan_btn.command()

                def check_done():
                    if gui.current_report is not None:
                        root_win.update()
                        out_dark = os.path.join(REPO_ROOT, "current_ui_dark.png")
                        capture_widget(root_win, out_dark)
                        print(f"Captured: {out_dark}")

                        # Switch to Light Mode
                        if theme_btn and theme_btn.command:
                            theme_btn.command()
                            root_win.update()
                            out_light = os.path.join(REPO_ROOT, "current_ui_light.png")
                            capture_widget(root_win, out_light)
                            print(f"Captured: {out_light}")

                            # Switch back to Dark Mode
                            theme_btn.command()
                            root_win.update()

                        # Open Update Channel Modal
                        if channel_btn and channel_btn.command:
                            channel_btn.command()
                            root_win.update_idletasks()
                            root_win.update()
                            top_wins = [w for w in root_win.winfo_children() if isinstance(w, tk.Toplevel)]
                            if top_wins:
                                top_win = top_wins[0]
                                def finish_modal():
                                    top_win.update_idletasks()
                                    top_win.update()
                                    out_modal = os.path.join(REPO_ROOT, "current_ui_update_modal.png")
                                    capture_widget(top_win, out_modal)
                                    print(f"Captured: {out_modal}")
                                    top_win.destroy()
                                    root_win.destroy()
                                root_win.after(200, finish_modal)
                                return

                        root_win.destroy()
                    else:
                        root_win.after(200, check_done)

                root_win.after(500, check_done)

            root_win.after(50, execute_and_capture)
            orig_mainloop(root_win)

        tk.Tk.mainloop = custom_mainloop
        try:
            orig_run_tkinter()
        finally:
            tk.Tk.mainloop = orig_mainloop

    gui._run_tkinter = patched_run_tkinter
    gui._run_tkinter()

if __name__ == "__main__":
    run_captures()
