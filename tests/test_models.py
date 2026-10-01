"""Unit tests for hwscan.core.models."""

import unittest
from hwscan.core.models import (
    SystemInfo,
    CPUInfo,
    MemoryModule,
    MemoryInfo,
    MotherboardInfo,
    GPUDevice,
    GPUInfo,
    StoragePartition,
    PhysicalDisk,
    StorageInfo,
    NetworkInterface,
    NetworkInfo,
    BatteryInfo,
    PeripheralInfo,
    SecurityInfo,
    HealthWarning,
    HardwareReport,
)


class TestModels(unittest.TestCase):
    def test_system_info_defaults_and_dict(self):
        sys_info = SystemInfo(hostname="TEST-HOST", os_name="Windows 11")
        d = sys_info.to_dict()
        self.assertEqual(d["hostname"], "TEST-HOST")
        self.assertEqual(d["os_name"], "Windows 11")
        self.assertEqual(d["is_admin"], False)

    def test_cpu_info(self):
        cpu = CPUInfo(model="Intel Core i9-13900K", physical_cores=24, logical_cores=32)
        d = cpu.to_dict()
        self.assertEqual(d["model"], "Intel Core i9-13900K")
        self.assertEqual(d["physical_cores"], 24)
        self.assertEqual(d["logical_cores"], 32)
        self.assertEqual(d["cache_l2"], "N/A")

    def test_memory_info(self):
        mod = MemoryModule(bank_label="DIMM 0", capacity_bytes=17179869184, speed_mhz=6000)
        mem = MemoryInfo(total_bytes=34359738368, modules=[mod])
        d = mem.to_dict()
        self.assertEqual(len(d["modules"]), 1)
        self.assertEqual(d["modules"][0]["speed_mhz"], 6000)

    def test_hardware_report_structure(self):
        report = HardwareReport(
            system=SystemInfo(hostname="PC-01"),
            cpu=CPUInfo(model="AMD Ryzen 9"),
            memory=MemoryInfo(),
            motherboard=MotherboardInfo(),
            gpu=GPUInfo(devices=[GPUDevice(name="RTX 4090", vendor="NVIDIA")]),
            storage=StorageInfo(),
            network=NetworkInfo(),
            battery=BatteryInfo(),
            peripherals=PeripheralInfo(),
            security=SecurityInfo(secure_boot=True),
            health_score=95,
            warnings=[HealthWarning(category="Storage", level="WARNING", title="Low Space", description="Drive C is 92% full")]
        )
        d = report.to_dict()
        self.assertEqual(d["health_score"], 95)
        self.assertEqual(d["system"]["hostname"], "PC-01")
        self.assertEqual(d["gpu"]["devices"][0]["name"], "RTX 4090")
        self.assertEqual(len(d["warnings"]), 1)
        self.assertEqual(d["warnings"][0]["level"], "WARNING")


if __name__ == "__main__":
    unittest.main()
