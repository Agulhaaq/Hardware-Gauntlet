"""Hardware Gauntlet - Startup Hygiene, Background Services & Latency Tests."""

import unittest
from unittest.mock import patch, MagicMock

from hwscan.core.startup_service_tuner import (
    audit_startup_applications,
    audit_background_services,
    audit_power_and_latency_profiles,
    run_startup_optimization_suite,
)


class TestStartupServiceTuner(unittest.TestCase):
    """Test suite for autostart inspection, service overhead analysis, and power plans."""

    def test_audit_startup_applications_structure(self):
        logs = []
        result = audit_startup_applications(log_fn=logs.append)
        self.assertIn("items", result)
        self.assertIn("total_items", result)
        self.assertIn("high_impact_count", result)
        self.assertIsInstance(result["items"], list)
        self.assertTrue(len(logs) > 0)

    def test_audit_background_services_structure(self):
        logs = []
        result = audit_background_services(log_fn=logs.append)
        self.assertIn("total_services_analyzed", result)
        self.assertIn("telemetry_services_flagged", result)
        self.assertIn("recommendations", result)
        self.assertIsInstance(result["recommendations"], list)
        self.assertTrue(len(logs) > 0)

    def test_audit_power_and_latency_profiles_structure(self):
        logs = []
        result = audit_power_and_latency_profiles(log_fn=logs.append)
        self.assertIn("active_scheme", result)
        self.assertIn("power_state_status", result)
        self.assertIn("recommendations", result)
        self.assertTrue(len(logs) > 0)

    @patch("hwscan.core.startup_service_tuner.sys.platform", "linux")
    def test_startup_tuner_linux_simulation(self):
        logs = []
        res = audit_startup_applications(log_fn=logs.append)
        self.assertIn("items", res)
        srv = audit_background_services(log_fn=logs.append)
        self.assertIn("recommendations", srv)

    @patch("hwscan.core.startup_service_tuner.sys.platform", "darwin")
    def test_startup_tuner_macos_simulation(self):
        logs = []
        res = audit_startup_applications(log_fn=logs.append)
        self.assertIn("items", res)
        pwr = audit_power_and_latency_profiles(log_fn=logs.append)
        self.assertIn("active_scheme", pwr)

    def test_run_startup_optimization_suite(self):
        logs = []
        suite_res = run_startup_optimization_suite(log_fn=logs.append)
        self.assertIn("startup", suite_res)
        self.assertIn("services", suite_res)
        self.assertIn("power", suite_res)
        self.assertTrue(len(logs) > 0)


if __name__ == "__main__":
    unittest.main()
