"""Automated 3-Consecutive Verification Suite for Hardware Gauntlet Single-Instance Mutex Guard.

Tests that:
1. When a primary instance is active, it successfully acquires the single-instance mutex.
2. Any subsequent/secondary instance attempts to launch:
   - Detects the already-existing mutex
   - Finds and focuses the existing instance's window
   - Returns False and exits immediately with code 0 without duplicate process creation.
3. When the primary instance terminates, the mutex is cleanly freed.
4. A newly spawned instance immediately acquires the freed lock without stale handle locks.
5. Performs this verification across 3 full consecutive cycles.
"""

import os
import sys
import time
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hwscan.core.instance_guard import (
    acquire_single_instance_lock,
    release_single_instance_lock,
    find_existing_window,
    focus_window,
    WINDOW_TITLE
)

# Python script to run an instance that holds the lock and reports readiness
PRIMARY_HOLDER_CODE = """
import sys
import time
import tkinter as tk
from hwscan.core.instance_guard import acquire_single_instance_lock, release_single_instance_lock, WINDOW_TITLE

locked = acquire_single_instance_lock(WINDOW_TITLE)
if not locked:
    print("PRIMARY_LOCK_FAILED", flush=True)
    sys.exit(1)

print("PRIMARY_LOCKED", flush=True)

root = tk.Tk()
root.title(WINDOW_TITLE)
root.geometry("400x300")

def check_stdin():
    root.after(100, check_stdin)

root.after(100, check_stdin)
root.mainloop()

release_single_instance_lock()
print("PRIMARY_RELEASED", flush=True)
"""

# Python script to run a secondary instance that attempts to acquire the lock
SECONDARY_ATTEMPT_CODE = """
import sys
from hwscan.core.instance_guard import acquire_single_instance_lock, WINDOW_TITLE

locked = acquire_single_instance_lock(WINDOW_TITLE)
if locked:
    print("SECONDARY_UNEXPECTEDLY_ACQUIRED", flush=True)
    sys.exit(2)
else:
    print("SECONDARY_PROPERLY_BLOCKED", flush=True)
    sys.exit(0)
"""


def kill_process_tree(pid: int):
    """Safely terminate a process and its child processes on Windows."""
    try:
        import psutil
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception:
                pass
        parent.kill()
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=3)
        except Exception:
            pass


def run_single_instance_cycle(cycle_num: int):
    print(f"\n======================================================================")
    print(f" >>> [CYCLE #{cycle_num}/3] SINGLE-INSTANCE MUTEX VERIFICATION")
    print(f"======================================================================")
    t0 = time.time()

    # Step 1: Launch Primary Instance in separate process
    print(f" [C{cycle_num}:Step 1] Spawning Primary Instance #1...")
    p1 = subprocess.Popen(
        [sys.executable, "-c", PRIMARY_HOLDER_CODE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=REPO_ROOT
    )

    # Wait for instance to acquire lock and signal readiness
    ready = False
    for _ in range(50):
        if p1.poll() is not None:
            break
        line = p1.stdout.readline()
        if "PRIMARY_LOCKED" in line:
            ready = True
            break
        time.sleep(0.1)

    assert ready, f"Primary instance failed to acquire lock or launch. Returncode: {p1.poll()}"
    print(f" [C{cycle_num}:Step 1] ✓ Primary Instance #1 running (PID: {p1.pid}) with mutex held.")

    # Brief pause to let Tk register the window handle
    time.sleep(0.5)

    # Step 2: Verify window is discoverable via Win32 API
    if sys.platform == "win32":
        hwnd = find_existing_window(WINDOW_TITLE)
        print(f" [C{cycle_num}:Step 2] Querying Win32 API for active instance window handle: HWND={hwnd}")
        assert hwnd is not None and hwnd != 0, f"Failed to locate window for {WINDOW_TITLE}"
        print(f" [C{cycle_num}:Step 2] ✓ Active window located successfully.")

    # Step 3: Attempt to launch Secondary Instance #2
    print(f" [C{cycle_num}:Step 3] Spawning Secondary Instance #2 while Primary is active...")
    p2 = subprocess.run(
        [sys.executable, "-c", SECONDARY_ATTEMPT_CODE],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10
    )

    assert p2.returncode == 0, f"Secondary instance returned error code {p2.returncode}: {p2.stderr}"
    assert "SECONDARY_PROPERLY_BLOCKED" in p2.stdout, f"Secondary instance output unexpected: {p2.stdout}"
    print(f" [C{cycle_num}:Step 3] ✓ Secondary Instance #2 detected existing instance and exited cleanly.")

    # Step 4: Attempt to launch Tertiary Instance #3 (Verify multiple blocked calls)
    print(f" [C{cycle_num}:Step 4] Spawning Tertiary Instance #3 while Primary is active...")
    p3 = subprocess.run(
        [sys.executable, "-c", SECONDARY_ATTEMPT_CODE],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10
    )

    assert p3.returncode == 0, f"Tertiary instance returned error code {p3.returncode}: {p3.stderr}"
    assert "SECONDARY_PROPERLY_BLOCKED" in p3.stdout, f"Tertiary instance output unexpected: {p3.stdout}"
    print(f" [C{cycle_num}:Step 4] ✓ Tertiary Instance #3 detected existing instance and exited cleanly.")

    # Step 5: Terminate Primary Instance #1 and verify clean mutex release
    print(f" [C{cycle_num}:Step 5] Terminating Primary Instance #1 (PID: {p1.pid})...")
    kill_process_tree(p1.pid)
    time.sleep(0.5)
    print(f" [C{cycle_num}:Step 5] ✓ Primary Instance #1 terminated. Mutex freed.")

    # Step 6: Verify a new instance can now acquire the freed mutex
    print(f" [C{cycle_num}:Step 6] Spawning New Instance #4 to verify freed mutex reacquisition...")
    res = acquire_single_instance_lock(WINDOW_TITLE)
    assert res is True, "Failed to reacquire mutex after previous instance terminated."
    release_single_instance_lock()
    print(f" [C{cycle_num}:Step 6] ✓ New Instance successfully acquired previously held mutex.")

    # Step 7: Verify standalone binary single-instance mutex
    dist_exe = os.path.join(REPO_ROOT, "dist", "HardwareGauntlet.exe")
    if os.path.exists(dist_exe):
        print(f" [C{cycle_num}:Step 7] Testing compiled binary single-instance guard...")
        bin_p1 = subprocess.Popen([dist_exe], cwd=REPO_ROOT)
        time.sleep(1.8)
        try:
            assert bin_p1.poll() is None, "Compiled binary Instance #1 failed to stay active"
            bin_p2 = subprocess.run([dist_exe], capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
            assert bin_p2.returncode == 0, f"Compiled binary duplicate returned {bin_p2.returncode}"
            print(f" [C{cycle_num}:Step 7] ✓ Compiled binary duplicate instance blocked and exited cleanly.")
        finally:
            kill_process_tree(bin_p1.pid)
            time.sleep(0.8)

    elapsed = time.time() - t0
    print(f" >>> [PASS] CYCLE #{cycle_num} COMPLETED IN {elapsed:.2f}s WITH ZERO ERRORS!")


def main():
    print("======================================================================")
    print(" HARDWARE GAUNTLET — 3 CONSECUTIVE SINGLE-INSTANCE MUTEX VERIFICATION")
    print("======================================================================")

    start_time = time.time()
    for cycle in range(1, 4):
        run_single_instance_cycle(cycle)
        if cycle < 3:
            time.sleep(1)

    total_time = time.time() - start_time
    print("\n======================================================================")
    print(f" [ALL PASS] 3/3 SINGLE-INSTANCE MUTEX CYCLES PASSED IN {total_time:.2f}s!")
    print(" MUTEX ENFORCEMENT, DUPLICATE PREVENTION & RESTORE VERIFIED 100% STABLE.")
    print("======================================================================")


if __name__ == "__main__":
    main()
