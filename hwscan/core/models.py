"""Data models representing system hardware and diagnostics."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class SystemInfo:
    hostname: str = "Unknown"
    os_name: str = "Unknown"
    os_version: str = "Unknown"
    os_build: str = "Unknown"
    os_arch: str = "Unknown"
    kernel: str = "Unknown"
    uptime_seconds: float = 0.0
    uptime_formatted: str = "Unknown"
    boot_mode: str = "Unknown"  # UEFI / Legacy
    is_admin: bool = False
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CPUInfo:
    model: str = "Unknown"
    vendor: str = "Unknown"
    architecture: str = "Unknown"
    physical_cores: int = 0
    logical_cores: int = 0
    base_clock_mhz: float = 0.0
    max_clock_mhz: float = 0.0
    current_usage_percent: float = 0.0
    features: List[str] = field(default_factory=list)
    cache_l2: str = "N/A"
    cache_l3: str = "N/A"
    temperature_c: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryModule:
    bank_label: str = "DIMM"
    capacity_bytes: int = 0
    capacity_formatted: str = "N/A"
    speed_mhz: int = 0
    memory_type: str = "Unknown"  # DDR4, DDR5, LPDDR5, etc.
    manufacturer: str = "Unknown"
    part_number: str = "Unknown"
    form_factor: str = "DIMM"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryInfo:
    total_bytes: int = 0
    available_bytes: int = 0
    used_bytes: int = 0
    percent: float = 0.0
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    swap_percent: float = 0.0
    modules: List[MemoryModule] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MotherboardInfo:
    manufacturer: str = "Unknown"
    product_name: str = "Unknown"
    version: str = "Unknown"
    serial_number: str = "Unknown"
    bios_vendor: str = "Unknown"
    bios_version: str = "Unknown"
    bios_release_date: str = "Unknown"
    chassis_type: str = "Desktop/Laptop"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GPUDevice:
    name: str = "Unknown"
    vendor: str = "Unknown"
    vram_bytes: int = 0
    vram_formatted: str = "N/A"
    driver_version: str = "Unknown"
    video_processor: str = "Unknown"
    resolution: str = "N/A"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GPUInfo:
    devices: List[GPUDevice] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StoragePartition:
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total_bytes: int = 0
    total_formatted: str = ""
    used_bytes: int = 0
    used_formatted: str = ""
    free_bytes: int = 0
    free_formatted: str = ""
    percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhysicalDisk:
    model: str = "Unknown"
    interface_type: str = "Unknown"  # NVMe, SATA, USB, SCSI
    media_type: str = "Unknown"  # SSD, HDD, NVMe
    size_bytes: int = 0
    size_formatted: str = ""
    serial_number: str = "Unknown"
    smart_status: str = "Healthy"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StorageInfo:
    physical_disks: List[PhysicalDisk] = field(default_factory=list)
    partitions: List[StoragePartition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkInterface:
    name: str = ""
    mac_address: str = "N/A"
    ipv4: List[str] = field(default_factory=list)
    ipv6: List[str] = field(default_factory=list)
    speed_mbps: int = 0
    is_up: bool = False
    is_wireless: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkInfo:
    interfaces: List[NetworkInterface] = field(default_factory=list)
    default_gateway: str = "N/A"
    hostname: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatteryInfo:
    has_battery: bool = False
    percent: float = 0.0
    is_charging: bool = False
    power_plugged: bool = True
    time_remaining_seconds: Optional[int] = None
    health_status: str = "Good"
    cycle_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PeripheralInfo:
    usb_devices: List[str] = field(default_factory=list)
    audio_devices: List[str] = field(default_factory=list)
    bluetooth_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityInfo:
    secure_boot: Optional[bool] = None
    tpm_present: Optional[bool] = None
    tpm_ready: Optional[bool] = None
    tpm_version: Optional[str] = None
    virtualization_enabled: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthWarning:
    category: str  # 'Storage', 'Memory', 'CPU', 'Security', etc.
    level: str     # 'INFO', 'WARNING', 'CRITICAL'
    title: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HardwareReport:
    system: SystemInfo
    cpu: CPUInfo
    memory: MemoryInfo
    motherboard: MotherboardInfo
    gpu: GPUInfo
    storage: StorageInfo
    network: NetworkInfo
    battery: BatteryInfo
    peripherals: PeripheralInfo
    security: SecurityInfo
    health_score: int = 100
    warnings: List[HealthWarning] = field(default_factory=list)
    scan_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
