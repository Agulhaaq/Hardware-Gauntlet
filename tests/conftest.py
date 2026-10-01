"""Global pytest fixtures and configuration."""

import os
import sys
import pytest
import tkinter as tk

# Pin TCL/TK library directories if running under Python on Windows
if sys.platform == "win32":
    py_dir = os.path.dirname(sys.executable)
    tcl_dir = os.path.join(py_dir, "tcl", "tcl8.6")
    tk_dir = os.path.join(py_dir, "tcl", "tk8.6")
    if os.path.exists(tcl_dir) and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = tcl_dir
    if os.path.exists(tk_dir) and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = tk_dir


@pytest.fixture(scope="session")
def tk_session_root():
    """Single hidden Tk root for all GUI and component tests."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass
