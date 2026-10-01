"""Unit and integration tests for hardware scanners."""

import unittest
from hwscan.scanners.system import SystemScanner
from hwscan.scanners.cpu import CPUScanner
from hwscan.scanners.memory import MemoryScanner
from hwscan.scanners.storage import StorageScanner
from hwscan.scanners.gpu import GPUScanner
from hwscan.scanners.motherboard import MotherboardScanner
from hwscan.scanners.network import NetworkScanner
from hwscan.scanners.security import SecurityScanner
from hwscan.scanners.battery import BatteryScanner
from hwscan.scanners.peripherals import PeripheralScanner


class TestScanners(unittest.TestCase):
    def test_system_scanner(self):
        scanner = SystemScanner()
        info = scanner.scan()
        self.assertIsNotNone(info.hostname)
        self.assertNotEqual(info.hostname, "")
        self.assertIsNotNone(info.os_name)
        self.assertGreaterEqual(info.uptime_seconds, 0)

    def test_cpu_scanner(self):
        scanner = CPUScanner()
        info = scanner.scan()
        self.assertIsNotNone(info.model)
        self.assertGreater(info.logical_cores, 0)
        self.assertGreater(info.physical_cores, 0)
        self.assertIsInstance(info.features, list)

    def test_memory_scanner(self):
        scanner = MemoryScanner()
        info = scanner.scan()
        self.assertGreater(info.total_bytes, 0)
        self.assertGreaterEqual(info.available_bytes, 0)
        self.assertGreaterEqual(info.percent, 0.0)
        self.assertLessEqual(info.percent, 100.0)

    def test_storage_scanner(self):
        scanner = StorageScanner()
        info = scanner.scan()
        self.assertIsInstance(info.partitions, list)
        self.assertIsInstance(info.physical_disks, list)
        # On any normal system at least one partition exists
        self.assertGreater(len(info.partitions), 0)

    def test_gpu_scanner(self):
        scanner = GPUScanner()
        info = scanner.scan()
        self.assertIsInstance(info.devices, list)

    def test_motherboard_scanner(self):
        scanner = MotherboardScanner()
        info = scanner.scan()
        self.assertIsNotNone(info.manufacturer)
        self.assertIsNotNone(info.bios_vendor)

    def test_network_scanner(self):
        scanner = NetworkScanner()
        info = scanner.scan()
        self.assertIsInstance(info.interfaces, list)

    def test_security_scanner(self):
        scanner = SecurityScanner()
        info = scanner.scan()
        self.assertIsNotNone(info)

    def test_battery_scanner(self):
        scanner = BatteryScanner()
        info = scanner.scan()
        self.assertIsInstance(info.has_battery, bool)

    def test_peripherals_scanner(self):
        scanner = PeripheralScanner()
        info = scanner.scan()
        self.assertIsInstance(info.usb_devices, list)
        self.assertIsInstance(info.audio_devices, list)


if __name__ == "__main__":
    unittest.main()
