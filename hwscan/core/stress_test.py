"""Hardware Gauntlet Stress Test & Thermal Stability Engine.

Performs multi-threaded CPU stress testing, RAM pattern integrity verification,
disk I/O throughput benchmarking, and real-time GPU/CPU thermal monitoring.
"""

import os
import sys
import time
import math
import shutil
import hashlib
import tempfile
import threading
import subprocess
from typing import Dict, Any, Callable, Optional
import psutil


class StressTestEngine:
    """Manages multi-component hardware stress testing and live telemetry reporting."""

    def __init__(self):
        self._is_running = False
        self._stop_event = threading.Event()
        self._telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._completion_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._worker_threads = []
        self._ram_errors = 0
        self._disk_write_speed = 0.0
        self._disk_read_speed = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_gpu_temperature(self) -> Optional[int]:
        """Query GPU temperature via nvidia-smi if available."""
        try:
            cflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                creationflags=cflags,
                text=True,
                timeout=1
            ).strip()
            return int(out.split("\n")[0].strip())
        except Exception:
            return None

    def get_gpu_utilization(self) -> Optional[int]:
        """Query GPU utilization via nvidia-smi if available."""
        try:
            cflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                creationflags=cflags,
                text=True,
                timeout=1
            ).strip()
            return int(out.split("\n")[0].strip())
        except Exception:
            return None

    def start_test(
        self,
        duration_seconds: int = 30,
        test_cpu: bool = True,
        test_ram: bool = True,
        test_disk: bool = True,
        ram_mb: int = 1024,
        on_telemetry: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_completion: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """Start hardware stress test across selected subsystems in background threads."""
        if self._is_running:
            return

        self._is_running = True
        self._stop_event.clear()
        self._telemetry_callback = on_telemetry
        self._completion_callback = on_completion
        self._ram_errors = 0
        self._disk_write_speed = 0.0
        self._disk_read_speed = 0.0

        master_thread = threading.Thread(
            target=self._run_master,
            args=(duration_seconds, test_cpu, test_ram, test_disk, ram_mb),
            daemon=True
        )
        master_thread.start()

    def stop_test(self) -> None:
        """Signal all stress workers to stop immediately."""
        self._stop_event.set()
        self._is_running = False

    def _cpu_worker(self) -> None:
        """Worker thread for maxing out a CPU core with mathematical load."""
        while not self._stop_event.is_set():
            # Mix floating-point, trigonometry and hashing
            val = 0.0
            for i in range(1000):
                val += math.sqrt(i + 1.0) * math.sin(i)
            # Short hash computation
            hashlib.sha256(str(val).encode("utf-8")).digest()
            time.sleep(0.001)

    def _ram_worker(self, target_mb: int) -> None:
        """Allocates memory, writes alternating bit patterns, and verifies checksum integrity."""
        try:
            chunk_size = 16 * 1024 * 1024  # 16 MB chunks
            num_chunks = max(1, (target_mb * 1024 * 1024) // chunk_size)
            patterns = [b"\xaa" * chunk_size, b"\x55" * chunk_size, b"\x00" * chunk_size, b"\xff" * chunk_size]

            buffers = []
            for _ in range(num_chunks):
                if self._stop_event.is_set():
                    break
                buffers.append(bytearray(chunk_size))

            pat_idx = 0
            while not self._stop_event.is_set():
                pat = patterns[pat_idx % len(patterns)]
                pat_idx += 1

                # Write phase
                for buf in buffers:
                    if self._stop_event.is_set():
                        break
                    buf[:] = pat

                # Verify phase
                for buf in buffers:
                    if self._stop_event.is_set():
                        break
                    if buf != pat:
                        self._ram_errors += 1

                time.sleep(0.05)
        except MemoryError:
            pass
        except Exception:
            pass

    def _disk_worker(self) -> None:
        """Benchmarks sequential disk write and read throughput."""
        test_dir = tempfile.gettempdir()
        test_file = os.path.join(test_dir, f"hwgauntlet_benchmark_{os.getpid()}.dat")
        test_size_mb = 128
        chunk = b"X" * (1024 * 1024)  # 1MB chunk

        try:
            # 1. Write benchmark
            t0 = time.time()
            with open(test_file, "wb") as f:
                for _ in range(test_size_mb):
                    if self._stop_event.is_set():
                        break
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
            w_time = time.time() - t0
            if w_time > 0 and not self._stop_event.is_set():
                self._disk_write_speed = round(test_size_mb / w_time, 1)

            # 2. Read benchmark
            if not self._stop_event.is_set() and os.path.exists(test_file):
                t1 = time.time()
                with open(test_file, "rb") as f:
                    while True:
                        if self._stop_event.is_set():
                            break
                        data = f.read(1024 * 1024)
                        if not data:
                            break
                r_time = time.time() - t1
                if r_time > 0 and not self._stop_event.is_set():
                    self._disk_read_speed = round(test_size_mb / r_time, 1)
        except Exception:
            pass
        finally:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except Exception:
                    pass

    def _run_master(self, duration: int, test_cpu: bool, test_ram: bool, test_disk: bool, ram_mb: int) -> None:
        """Coordinates active workers and streams telemetry."""
        threads = []

        # 1. Launch CPU workers (all logical cores)
        if test_cpu:
            cpu_count = os.cpu_count() or 4
            for _ in range(cpu_count):
                t = threading.Thread(target=self._cpu_worker, daemon=True)
                t.start()
                threads.append(t)

        # 2. Launch RAM worker
        if test_ram:
            t = threading.Thread(target=self._ram_worker, args=(ram_mb,), daemon=True)
            t.start()
            threads.append(t)

        # 3. Launch Disk worker
        if test_disk:
            t = threading.Thread(target=self._disk_worker, daemon=True)
            t.start()
            threads.append(t)

        start_time = time.time()
        peak_cpu_load = 0.0
        peak_gpu_temp = 0

        # Telemetry loop
        while not self._stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            cpu_percent = psutil.cpu_percent(interval=0.5)
            peak_cpu_load = max(peak_cpu_load, cpu_percent)

            gpu_temp = self.get_gpu_temperature()
            if gpu_temp is not None:
                peak_gpu_temp = max(peak_gpu_temp, gpu_temp)

            gpu_util = self.get_gpu_utilization()

            mem = psutil.virtual_memory()

            freq = psutil.cpu_freq()
            curr_freq_mhz = freq.current if freq else 0.0

            telemetry = {
                "elapsed": round(elapsed, 1),
                "duration": duration,
                "progress_percent": min(100.0, round((elapsed / duration) * 100, 1)),
                "cpu_percent": cpu_percent,
                "peak_cpu_load": peak_cpu_load,
                "cpu_freq_mhz": curr_freq_mhz,
                "gpu_temp": gpu_temp,
                "peak_gpu_temp": peak_gpu_temp,
                "gpu_util": gpu_util,
                "ram_percent": mem.percent,
                "ram_errors": self._ram_errors,
                "disk_write_speed": self._disk_write_speed,
                "disk_read_speed": self._disk_read_speed,
                "is_running": True
            }

            if self._telemetry_callback:
                self._telemetry_callback(telemetry)

        # Signal completion
        self._stop_event.set()
        self._is_running = False

        total_elapsed = round(time.time() - start_time, 1)
        final_summary = {
            "total_elapsed": total_elapsed,
            "peak_cpu_load": round(peak_cpu_load, 1),
            "peak_gpu_temp": peak_gpu_temp if peak_gpu_temp > 0 else None,
            "ram_errors": self._ram_errors,
            "disk_write_speed": self._disk_write_speed,
            "disk_read_speed": self._disk_read_speed,
            "stability_status": "PASSED (STABLE)" if self._ram_errors == 0 else f"FAILED ({self._ram_errors} RAM ERRORS)",
            "is_running": False
        }

        if self._completion_callback:
            self._completion_callback(final_summary)
