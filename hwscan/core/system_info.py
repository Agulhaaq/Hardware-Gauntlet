"""Hardware Gauntlet core scanner orchestrator and health evaluation engine."""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from hwscan.core.models import (
    HardwareReport, HealthWarning, SystemInfo, CPUInfo,
    MemoryInfo, MotherboardInfo, GPUInfo, StorageInfo,
    NetworkInfo, BatteryInfo, PeripheralInfo, SecurityInfo
)
from hwscan.scanners.system import SystemScanner
from hwscan.scanners.cpu import CPUScanner
from hwscan.scanners.memory import MemoryScanner
from hwscan.scanners.motherboard import MotherboardScanner
from hwscan.scanners.gpu import GPUScanner
from hwscan.scanners.storage import StorageScanner
from hwscan.scanners.network import NetworkScanner
from hwscan.scanners.battery import BatteryScanner
from hwscan.scanners.peripherals import PeripheralScanner
from hwscan.scanners.security import SecurityScanner


class HardwareScannerEngine:
    """Coordinates all component scanners and produces comprehensive HardwareReport."""

    def __init__(self):
        self.system_scanner = SystemScanner()
        self.cpu_scanner = CPUScanner()
        self.memory_scanner = MemoryScanner()
        self.motherboard_scanner = MotherboardScanner()
        self.gpu_scanner = GPUScanner()
        self.storage_scanner = StorageScanner()
        self.network_scanner = NetworkScanner()
        self.battery_scanner = BatteryScanner()
        self.peripheral_scanner = PeripheralScanner()
        self.security_scanner = SecurityScanner()

    def run_full_scan(self) -> HardwareReport:
        """Run all scanners concurrently in parallel threads, evaluate health, and return final report."""
        t0 = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            fut_system = executor.submit(self.system_scanner.scan)
            fut_cpu = executor.submit(self.cpu_scanner.scan)
            fut_memory = executor.submit(self.memory_scanner.scan)
            fut_motherboard = executor.submit(self.motherboard_scanner.scan)
            fut_gpu = executor.submit(self.gpu_scanner.scan)
            fut_storage = executor.submit(self.storage_scanner.scan)
            fut_network = executor.submit(self.network_scanner.scan)
            fut_battery = executor.submit(self.battery_scanner.scan)
            fut_peripherals = executor.submit(self.peripheral_scanner.scan)
            fut_security = executor.submit(self.security_scanner.scan)

            system = fut_system.result()
            cpu = fut_cpu.result()
            memory = fut_memory.result()
            motherboard = fut_motherboard.result()
            gpu = fut_gpu.result()
            storage = fut_storage.result()
            network = fut_network.result()
            battery = fut_battery.result()
            peripherals = fut_peripherals.result()
            security = fut_security.result()

        health_score, warnings = self._evaluate_health(
            system, cpu, memory, storage, security, battery
        )

        duration = round(time.time() - t0, 3)

        return HardwareReport(
            system=system,
            cpu=cpu,
            memory=memory,
            motherboard=motherboard,
            gpu=gpu,
            storage=storage,
            network=network,
            battery=battery,
            peripherals=peripherals,
            security=security,
            health_score=health_score,
            warnings=warnings,
            scan_duration_seconds=duration
        )

    def _evaluate_health(
        self, system, cpu, memory, storage, security, battery
    ) -> Tuple[int, List[HealthWarning]]:
        """Compute health score (0-100) and identify optimization/security warnings."""
        score = 100
        warnings: List[HealthWarning] = []

        # 1. Storage checks
        for part in storage.partitions:
            if part.percent >= 90.0:
                score -= 15
                warnings.append(HealthWarning(
                    category="Storage",
                    level="CRITICAL",
                    title=f"Critical Disk Usage on {part.mountpoint}",
                    description=f"Partition {part.mountpoint} is {part.percent}% full with only {part.free_formatted} remaining."
                ))
            elif part.percent >= 80.0:
                score -= 5
                warnings.append(HealthWarning(
                    category="Storage",
                    level="WARNING",
                    title=f"High Disk Usage on {part.mountpoint}",
                    description=f"Partition {part.mountpoint} is {part.percent}% full ({part.free_formatted} free)."
                ))

        # 2. Memory checks
        if memory.percent >= 90.0:
            score -= 10
            warnings.append(HealthWarning(
                category="Memory",
                level="WARNING",
                title="High RAM Consumption",
                description=f"System RAM is at {memory.percent}% utilization."
            ))

        if len(memory.modules) > 1:
            speeds = set(m.speed_mhz for m in memory.modules if m.speed_mhz > 0)
            capacities = set(m.capacity_bytes for m in memory.modules if m.capacity_bytes > 0)
            if len(speeds) > 1:
                warnings.append(HealthWarning(
                    category="Memory",
                    level="INFO",
                    title="Mismatched RAM Speeds Detected",
                    description=f"Installed RAM modules have differing clock frequencies: {', '.join(str(s) + 'MHz' for s in speeds)}."
                ))
            if len(capacities) > 1:
                warnings.append(HealthWarning(
                    category="Memory",
                    level="INFO",
                    title="Asymmetric Memory Capacity",
                    description="Installed RAM modules have differing capacities (e.g. 16GB + 8GB), running in flex mode."
                ))

        # 3. Security checks
        if security.secure_boot is False:
            score -= 5
            warnings.append(HealthWarning(
                category="Security",
                level="WARNING",
                title="Secure Boot Disabled",
                description="UEFI Secure Boot is disabled. Enabling it protects boot integrity against rootkits."
            ))

        if security.tpm_present is False:
            warnings.append(HealthWarning(
                category="Security",
                level="INFO",
                title="TPM 2.0 Not Detected",
                description="Trusted Platform Module is missing or disabled in BIOS. Required for Windows 11 and BitLocker."
            ))

        if security.virtualization_enabled is False:
            warnings.append(HealthWarning(
                category="Security",
                level="INFO",
                title="Hardware Virtualization Disabled",
                description="VT-x / AMD-V is disabled in BIOS. Enable it to run WSL2, Docker, or Virtual Machines."
            ))

        # 4. Battery checks (if laptop)
        if battery.has_battery and battery.cycle_count and battery.cycle_count > 800:
            score -= 10
            warnings.append(HealthWarning(
                category="Battery",
                level="WARNING",
                title="High Battery Cycle Count",
                description=f"Battery has reached {battery.cycle_count} charge cycles. Capacity may be degraded."
            ))

        score = max(0, min(100, score))
        return score, warnings
