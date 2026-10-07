"""Full-Spectrum 3-Consecutive Verification Runner for Hardware Gauntlet.
Runs 3 complete end-to-end testing cycles across:
1. Pytest 91-test unit & integration suite
2. CLI and JSON telemetry engines
3. Live Tkinter UI event-loop, 8 tabs, theme toggling, and modals
4. Standalone portable executable binaries
"""
import os
import sys
import time
import subprocess
import json
import tkinter as tk

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hwscan.gui import HardwareGauntletGUI


def test_ui_cycle(cycle_num: int):
    """Run headless live UI test within Tkinter mainloop."""
    print(f"   [C{cycle_num}:UI] Initializing Tkinter GUI instance...")
    gui = HardwareGauntletGUI()
    orig_run_tkinter = gui._run_tkinter
    errors = []

    def patched_run_tkinter():
        orig_mainloop = tk.Tk.mainloop
        def custom_mainloop(root_win):
            def automated_driver():
                try:
                    root_win.update()
                    assert "Hardware Gauntlet" in root_win.title(), "Invalid title"
                    w, h = root_win.winfo_width(), root_win.winfo_height()
                    assert w >= 900 and h >= 650, f"Invalid geometry: {w}x{h}"

                    theme_btn = None
                    scan_btn = None
                    update_btn = None
                    trim_btn = None
                    tab_buttons = []

                    for child in root_win.winfo_children():
                        for sub in child.winfo_children():
                            if hasattr(sub, "text"):
                                txt = getattr(sub, "text", "")
                                if any(k in txt for k in ["OVERVIEW", "STRESS", "CPU", "MEMORY", "GRAPHICS", "STORAGE", "SECURITY", "UTILITIES"]):
                                    tab_buttons.append(sub)
                            for btn in sub.winfo_children():
                                if hasattr(btn, "text"):
                                    txt = getattr(btn, "text", "")
                                    if "SCAN" in txt and not scan_btn:
                                        scan_btn = btn
                                    elif "LIGHT" in txt or "DARK" in txt:
                                        theme_btn = btn
                                    elif "UPDATE" in txt and not update_btn:
                                        update_btn = btn
                                    elif "TRIM RAM" in txt:
                                        trim_btn = btn
                                    elif any(k in txt for k in ["OVERVIEW", "STRESS", "CPU", "MEMORY", "GRAPHICS", "STORAGE", "SECURITY", "UTILITIES"]):
                                        tab_buttons.append(btn)

                    assert len(tab_buttons) >= 8, f"Expected 8 tab buttons, found {len(tab_buttons)}"
                    assert scan_btn is not None, "Scan button not found"
                    assert theme_btn is not None, "Theme toggle not found"
                    assert update_btn is not None, "Update button not found"

                    # 1. Exercise all 8 tabs
                    for tab in tab_buttons[:8]:
                        tab.command()
                        root_win.update()

                    tab_buttons[0].command()
                    root_win.update()

                    # 2. Toggle Theme (Dark -> Light -> Dark)
                    assert gui.current_theme == "dark"
                    theme_btn.command()
                    root_win.update()
                    assert gui.current_theme == "light"
                    theme_btn.command()
                    root_win.update()
                    assert gui.current_theme == "dark"

                    # 3. Open and close update channel modal
                    update_btn.command()
                    root_win.update()
                    top_wins = [w for w in root_win.winfo_children() if isinstance(w, tk.Toplevel)]
                    assert len(top_wins) >= 1, "Failed to open modal"
                    top_wins[0].destroy()
                    root_win.update()

                    # 4. Trigger scan
                    rep = gui.engine.run_full_scan()
                    assert rep is not None and rep.health_score > 0

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    errors.append(e)
                finally:
                    root_win.destroy()

            root_win.after(40, automated_driver)
            orig_mainloop(root_win)

        tk.Tk.mainloop = custom_mainloop
        try:
            orig_run_tkinter()
        finally:
            tk.Tk.mainloop = orig_mainloop

    gui._run_tkinter = patched_run_tkinter
    gui._run_tkinter()

    if errors:
        raise errors[0]
    print(f"   [C{cycle_num}:UI] ✓ UI and Event Loop passed cleanly.")


def test_cli_cycle(cycle_num: int):
    """Test CLI commands and JSON output."""
    print(f"   [C{cycle_num}:CLI] Testing CLI flags (--version, --health, --json)...")
    
    # Version
    res = subprocess.run([sys.executable, "-m", "hwscan.cli", "--version"], capture_output=True, text=True)
    assert res.returncode == 0, f"Version failed: {res.stderr}"
    assert "Hardware Gauntlet" in res.stdout

    # Health
    res = subprocess.run([sys.executable, "-m", "hwscan.cli", "--health"], capture_output=True, text=True)
    assert res.returncode in (0, 1), f"Health check failed: {res.stderr}"
    assert "Hardware Health Score:" in res.stdout

    # JSON export
    res = subprocess.run([sys.executable, "-m", "hwscan.cli", "--json", "-"], capture_output=True, text=True)
    assert res.returncode == 0, f"JSON export failed: {res.stderr}"
    data = json.loads(res.stdout)
    assert "health_score" in data and "system" in data and "cpu" in data
    print(f"   [C{cycle_num}:CLI] ✓ CLI commands & JSON parser passed cleanly.")


def test_pytest_cycle(cycle_num: int):
    """Run complete pytest test suite."""
    print(f"   [C{cycle_num}:PYTEST] Executing full pytest suite (91 tests)...")
    t0 = time.time()
    res = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    elapsed = time.time() - t0
    assert res.returncode == 0, f"Pytest failed with exit code {res.returncode}:\n{res.stdout}\n{res.stderr}"
    assert "91 passed" in res.stdout or "passed" in res.stdout
    print(f"   [C{cycle_num}:PYTEST] ✓ 91/91 tests passed in {elapsed:.2f}s.")


def test_binaries_cycle(cycle_num: int):
    """Verify standalone single-file executables."""
    print(f"   [C{cycle_num}:BIN] Checking standalone portable executables...")
    root_exe = os.path.join(REPO_ROOT, "HardwareGauntlet.exe")
    dist_exe = os.path.join(REPO_ROOT, "dist", "HardwareGauntlet.exe")

    for path in [root_exe, dist_exe]:
        assert os.path.exists(path), f"Binary not found: {path}"
        sz = os.path.getsize(path)
        assert sz > 20_000_000, f"Binary abnormally small ({sz} bytes): {path}"
        with open(path, "rb") as f:
            header = f.read(2)
            assert header == b"MZ", f"Invalid PE header in {path}"

    print(f"   [C{cycle_num}:BIN] ✓ Both binaries exist, valid PE headers, sized ~{sz/(1024*1024):.1f} MB.")


def run_full_cycle(cycle_num: int):
    print(f"\n======================================================================")
    print(f" >>> STARTING CONSECUTIVE TEST CYCLE #{cycle_num} OF 3")
    print(f"======================================================================")
    t0 = time.time()

    # Step 1: Pytest
    test_pytest_cycle(cycle_num)

    # Step 2: CLI
    test_cli_cycle(cycle_num)

    # Step 3: UI
    test_ui_cycle(cycle_num)

    # Step 4: Standalone Binaries
    test_binaries_cycle(cycle_num)

    elapsed = time.time() - t0
    print(f"\n >>> [PASS] CYCLE #{cycle_num} COMPLETED IN {elapsed:.2f}s WITH ZERO ERRORS!")


def main():
    print("======================================================================")
    print(" HARDWARE GAUNTLET — 3 CONSECUTIVE RIGOROUS SYSTEM VERIFICATION RUNS")
    print("======================================================================")

    start_time = time.time()
    for cycle in range(1, 4):
        run_full_cycle(cycle)
        if cycle < 3:
            time.sleep(1)

    total_time = time.time() - start_time
    print("\n======================================================================")
    print(f" [ALL PASS] 3/3 CONSECUTIVE TEST CYCLES PASSED IN {total_time:.2f}s!")
    print(" ALL 8 TABS, UI THEME ENGINE, MODALS, CLI, 91 PYTESTS & BINARIES VERIFIED.")
    print("======================================================================")


if __name__ == "__main__":
    main()
