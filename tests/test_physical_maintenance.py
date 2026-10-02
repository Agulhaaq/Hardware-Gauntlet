"""Hardware Gauntlet - Physical Hardware Maintenance & Inspection Guide Tests."""

import unittest
from unittest.mock import patch, MagicMock

from hwscan.core.physical_maintenance import (
    detect_chassis_form_factor,
    generate_physical_maintenance_guide,
    get_fan_and_heatsink_cleaning_protocol,
    get_thermal_repasting_advisor,
    get_peripherals_and_ports_hygiene_guide,
    run_physical_maintenance_suite,
)


class TestPhysicalMaintenance(unittest.TestCase):
    """Test suite for physical maintenance advisor, dust protocols, and TIM guides."""

    @patch("hwscan.core.physical_maintenance.psutil.sensors_battery")
    def test_detect_chassis_form_factor_laptop(self, mock_battery):
        mock_batt = MagicMock()
        mock_batt.percent = 85
        mock_battery.return_value = mock_batt

        form_factor = detect_chassis_form_factor()
        self.assertEqual(form_factor, "LAPTOP")

    @patch("hwscan.core.physical_maintenance.psutil.sensors_battery")
    def test_detect_chassis_form_factor_desktop(self, mock_battery):
        mock_battery.return_value = None

        form_factor = detect_chassis_form_factor()
        self.assertEqual(form_factor, "DESKTOP")

    def test_fan_and_heatsink_cleaning_protocol(self):
        protocol = get_fan_and_heatsink_cleaning_protocol("LAPTOP")
        self.assertIn("steps", protocol)
        self.assertIn("warnings", protocol)
        self.assertIn("tools_required", protocol)
        # Check back-EMF generator warning presence
        warnings_str = " ".join(protocol["warnings"])
        self.assertIn("fan", warnings_str.lower())
        self.assertIn("emf", warnings_str.lower())

    def test_thermal_repasting_advisor_normal_temp(self):
        advisor = get_thermal_repasting_advisor(cpu_temp=55.0)
        self.assertIn("recommended_compounds", advisor)
        self.assertIn("application_technique", advisor)
        self.assertIn("warnings", advisor)
        self.assertEqual(advisor["urgency"], "PREVENTATIVE")

    def test_thermal_repasting_advisor_high_temp(self):
        advisor = get_thermal_repasting_advisor(cpu_temp=92.0)
        self.assertIn("URGENT", advisor["urgency"])
        # Should highlight PTM7950 phase-change material
        compounds_str = " ".join([c["name"] for c in advisor["recommended_compounds"]])
        self.assertIn("PTM7950", compounds_str)

    def test_peripherals_and_ports_hygiene_guide(self):
        guide = get_peripherals_and_ports_hygiene_guide()
        self.assertIn("display_cleaning", guide)
        self.assertIn("port_cleaning", guide)
        self.assertIn("keyboard_cleaning", guide)
        self.assertIn("prohibited_substances", guide)

    @patch("hwscan.core.physical_maintenance.detect_chassis_form_factor")
    def test_generate_physical_maintenance_guide_customized(self, mock_detect):
        mock_detect.return_value = "LAPTOP"
        logs = []
        guide = generate_physical_maintenance_guide(log_fn=logs.append)
        self.assertEqual(guide["form_factor"], "LAPTOP")
        self.assertIn("checklist", guide)
        self.assertTrue(len(logs) > 0)

    def test_run_physical_maintenance_suite(self):
        logs = []
        results = run_physical_maintenance_suite(log_fn=logs.append)
        self.assertIn("form_factor", results)
        self.assertIn("cleaning_protocol", results)
        self.assertIn("repasting_advisor", results)
        self.assertIn("peripherals_guide", results)
        self.assertTrue(len(logs) > 0)


if __name__ == "__main__":
    unittest.main()
