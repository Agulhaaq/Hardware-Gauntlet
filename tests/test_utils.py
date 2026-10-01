"""Unit tests for hwscan.core.utils."""

import sys
import unittest
from hwscan.core.utils import (
    format_bytes,
    format_hz,
    format_uptime,
    is_admin,
    get_current_os,
    run_command,
    run_powershell_json,
)


class TestUtils(unittest.TestCase):
    def test_format_bytes(self):
        self.assertEqual(format_bytes(None), "N/A")
        self.assertEqual(format_bytes(-100), "N/A")
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1024), "1 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 16), "16.0 GB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024 * 2), "2.0 TB")

    def test_format_hz(self):
        self.assertEqual(format_hz(None), "N/A")
        self.assertEqual(format_hz(0), "N/A")
        self.assertEqual(format_hz(-50), "N/A")
        self.assertEqual(format_hz(800, is_mhz=True), "800 MHz")
        self.assertEqual(format_hz(3600, is_mhz=True), "3.60 GHz")
        self.assertEqual(format_hz(4800000000, is_mhz=False), "4.80 GHz")
        self.assertEqual(format_hz(800000000, is_mhz=False), "800 MHz")

    def test_format_uptime(self):
        self.assertEqual(format_uptime(None), "Unknown")
        self.assertEqual(format_uptime(-1), "Unknown")
        self.assertEqual(format_uptime(45), "0m")
        self.assertEqual(format_uptime(125), "2m")
        self.assertEqual(format_uptime(3665), "1h 1m")
        self.assertEqual(format_uptime(90061), "1d 1h 1m")

    def test_get_current_os(self):
        os_name = get_current_os()
        self.assertIn(os_name, ["windows", "macos", "linux", "other"])
        if sys.platform == "win32":
            self.assertEqual(os_name, "windows")

    def test_is_admin(self):
        result = is_admin()
        self.assertIsInstance(result, bool)

    def test_run_command(self):
        if sys.platform == "win32":
            out = run_command("cmd.exe /c echo hello")
        else:
            out = run_command("echo hello")
        self.assertEqual(out, "hello")

        # Invalid command handles safely
        out_bad = run_command("nonexistent_command_xyz_12345")
        self.assertEqual(out_bad, "")

    def test_run_powershell_json(self):
        if sys.platform == "win32":
            out = run_powershell_json("@{test='ok'}")
            self.assertTrue(len(out) > 0)
            self.assertIn("test", out)
            self.assertIn("ok", out)
        else:
            self.assertEqual(run_powershell_json("test"), "")


if __name__ == "__main__":
    unittest.main()
