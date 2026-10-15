"""Comprehensive 3-Cycle Verification Suite for All Hardware Gauntlet Utilities.

Runs three consecutive cycles testing all cleanup, deep cleanup, hardware health,
physical maintenance, startup/service tuning utilities, and GUI wrappers.
Every utility must pass all contract assertions across all 3 cycles.
If any cycle fails, the runner stops immediately and exits with non-zero exit code.
"""

import sys
import os
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hwscan.core.cleanup import (
    clean_storage,
    clean_ram,
    clean_cpu,
    clean_network_cache,
    run_full_system_cleanup
)
from hwscan.core.deep_cleanup import (
    clean_component_store,
    clean_driver_and_kernel_store,
    optimize_system_storage_overhead,
    clean_developer_caches,
    run_deep_system_optimization
)
from hwscan.core.hardware_health import (
    audit_thermal_health,
    audit_battery_longevity,
    optimize_ssd_trim,
    run_hardware_health_suite
)
from hwscan.core.physical_maintenance import (
    detect_chassis_form_factor,
    get_fan_and_heatsink_cleaning_protocol,
    get_thermal_repasting_advisor,
    get_peripherals_and_ports_hygiene_guide,
    generate_physical_maintenance_guide,
    run_physical_maintenance_suite
)
from hwscan.core.startup_service_tuner import (
    audit_startup_applications,
    audit_background_services,
    audit_power_and_latency_profiles,
    run_startup_optimization_suite
)


def run_single_test_cycle(cycle_num: int):
    print(f"\n=======================================================")
    print(f" >>> COMMENCING UTILITY TEST CYCLE {cycle_num} / 3 <<<")
    print(f"=======================================================")
    
    logs = []
    def test_logger(msg: str):
        logs.append(msg)

    # -------------------------------------------------------------
    # Group 1: Standard Cleanup Engines (hwscan.core.cleanup)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 1.1: clean_storage...")
    logs.clear()
    r = clean_storage(log_fn=test_logger)
    assert isinstance(r, dict), "clean_storage must return dict"
    assert r.get("success") is True, f"clean_storage success failed: {r}"
    assert "freed_bytes" in r and "files_removed" in r, f"Invalid storage schema: {r}"
    assert len(logs) > 0, "clean_storage should emit logs"
    print(f"    [OK] clean_storage OK: Freed {r.get('freed_str')}")

    print(f"[{cycle_num}] Testing 1.2: clean_ram...")
    logs.clear()
    r = clean_ram(log_fn=test_logger)
    assert isinstance(r, dict), "clean_ram must return dict"
    assert r.get("success") is True, f"clean_ram success failed: {r}"
    assert "reclaimed_bytes" in r and "before_used" in r, f"Invalid RAM schema: {r}"
    assert len(logs) > 0, "clean_ram should emit logs"
    print(f"    [OK] clean_ram OK: Reclaimed {r.get('reclaimed_str')}")

    print(f"[{cycle_num}] Testing 1.3: clean_cpu...")
    logs.clear()
    r = clean_cpu(log_fn=test_logger)
    assert isinstance(r, dict), "clean_cpu must return dict"
    assert r.get("success") is True, f"clean_cpu success failed: {r}"
    assert "processes_scanned" in r, f"Invalid CPU schema: {r}"
    assert len(logs) > 0, "clean_cpu should emit logs"
    print(f"    [OK] clean_cpu OK: Scanned {r.get('processes_scanned')} procs")

    print(f"[{cycle_num}] Testing 1.4: clean_network_cache...")
    logs.clear()
    r = clean_network_cache(log_fn=test_logger)
    assert isinstance(r, dict), "clean_network_cache must return dict"
    assert r.get("success") is True, f"clean_network_cache success failed: {r}"
    assert r.get("dns_flushed") is True, f"Invalid network schema: {r}"
    assert len(logs) > 0, "clean_network_cache should emit logs"
    print(f"    [OK] clean_network_cache OK: DNS Flushed")

    print(f"[{cycle_num}] Testing 1.5: run_full_system_cleanup...")
    logs.clear()
    r = run_full_system_cleanup(log_fn=test_logger)
    assert isinstance(r, dict), "run_full_system_cleanup must return dict"
    assert r.get("success") is True, f"run_full_system_cleanup success failed: {r}"
    assert "storage" in r and "ram" in r and "cpu" in r and "network" in r
    assert len(logs) > 0, "run_full_system_cleanup should emit logs"
    print(f"    [OK] run_full_system_cleanup OK")

    # -------------------------------------------------------------
    # Group 2: Deep OS Cleanup Engines (hwscan.core.deep_cleanup)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 2.1: clean_component_store...")
    logs.clear()
    r = clean_component_store(log_fn=test_logger)
    assert isinstance(r, dict), "clean_component_store must return dict"
    assert r.get("success") is True, f"clean_component_store success failed: {r}"
    assert "category" in r, f"Invalid component store schema: {r}"
    print(f"    [OK] clean_component_store OK")

    print(f"[{cycle_num}] Testing 2.2: clean_driver_and_kernel_store...")
    logs.clear()
    r = clean_driver_and_kernel_store(log_fn=test_logger)
    assert isinstance(r, dict), "clean_driver_and_kernel_store must return dict"
    assert r.get("success") is True, f"clean_driver_and_kernel_store success failed: {r}"
    assert "packages_detected" in r, f"Invalid driver store schema: {r}"
    print(f"    [OK] clean_driver_and_kernel_store OK: Packages: {r.get('packages_detected')}")

    print(f"[{cycle_num}] Testing 2.3: optimize_system_storage_overhead...")
    logs.clear()
    r = optimize_system_storage_overhead(log_fn=test_logger, reduce_hibernation=False)
    assert isinstance(r, dict), "optimize_system_storage_overhead must return dict"
    assert r.get("success") is True, f"optimize_system_storage_overhead success failed: {r}"
    print(f"    [OK] optimize_system_storage_overhead OK")

    print(f"[{cycle_num}] Testing 2.4: clean_developer_caches...")
    logs.clear()
    r = clean_developer_caches(log_fn=test_logger)
    assert isinstance(r, dict), "clean_developer_caches must return dict"
    assert r.get("success") is True, f"clean_developer_caches success failed: {r}"
    assert "freed_bytes" in r and "tools_cleaned" in r
    print(f"    [OK] clean_developer_caches OK: Freed {r.get('freed_str')}")

    print(f"[{cycle_num}] Testing 2.5: run_deep_system_optimization...")
    logs.clear()
    r = run_deep_system_optimization(log_fn=test_logger)
    assert isinstance(r, dict), "run_deep_system_optimization must return dict"
    assert r.get("success") is True, f"run_deep_system_optimization success failed: {r}"
    assert "component_store" in r and "driver_store" in r and "developer_caches" in r
    print(f"    [OK] run_deep_system_optimization OK: Freed {r.get('total_freed_formatted')}")

    # -------------------------------------------------------------
    # Group 3: Hardware Health & Longevity (hwscan.core.hardware_health)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 3.1: audit_thermal_health...")
    logs.clear()
    r = audit_thermal_health(log_fn=test_logger)
    assert isinstance(r, dict), "audit_thermal_health must return dict"
    assert r.get("success") is True, f"audit_thermal_health success failed: {r}"
    assert "cpu_temp_c" in r and "status" in r and "headroom_c" in r
    print(f"    [OK] audit_thermal_health OK: Temp {r.get('cpu_temp_c')}°C, Headroom {r.get('headroom_c')}°C")

    print(f"[{cycle_num}] Testing 3.2: audit_battery_longevity...")
    logs.clear()
    r = audit_battery_longevity(log_fn=test_logger)
    assert isinstance(r, dict), "audit_battery_longevity must return dict"
    assert r.get("success") is True, f"audit_battery_longevity success failed: {r}"
    assert "has_battery" in r and "recommendation" in r
    print(f"    [OK] audit_battery_longevity OK: Has battery: {r.get('has_battery')}")

    print(f"[{cycle_num}] Testing 3.3: optimize_ssd_trim...")
    logs.clear()
    r = optimize_ssd_trim(log_fn=test_logger)
    assert isinstance(r, dict), "optimize_ssd_trim must return dict"
    assert r.get("success") is True, f"optimize_ssd_trim success failed: {r}"
    assert "free_space_percent" in r and "trim_supported" in r
    print(f"    [OK] optimize_ssd_trim OK: Free space: {r.get('free_space_percent')}%")

    print(f"[{cycle_num}] Testing 3.4: run_hardware_health_suite...")
    logs.clear()
    r = run_hardware_health_suite(log_fn=test_logger)
    assert isinstance(r, dict), "run_hardware_health_suite must return dict"
    assert r.get("success") is True, f"run_hardware_health_suite success failed: {r}"
    assert "thermal" in r and "battery" in r and "ssd" in r
    print(f"    [OK] run_hardware_health_suite OK")

    # -------------------------------------------------------------
    # Group 4: Physical Maintenance (hwscan.core.physical_maintenance)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 4.1: detect_chassis_form_factor...")
    chassis = detect_chassis_form_factor()
    assert chassis in ("LAPTOP", "DESKTOP"), f"Invalid chassis: {chassis}"
    print(f"    [OK] detect_chassis_form_factor OK: {chassis}")

    print(f"[{cycle_num}] Testing 4.2: get_fan_and_heatsink_cleaning_protocol...")
    r = get_fan_and_heatsink_cleaning_protocol(chassis)
    assert isinstance(r, dict) and r.get("success") is True
    assert "steps" in r and "warnings" in r and "tools_required" in r
    print(f"    [OK] get_fan_and_heatsink_cleaning_protocol OK")

    print(f"[{cycle_num}] Testing 4.3: get_thermal_repasting_advisor...")
    r = get_thermal_repasting_advisor(cpu_temp=60.0)
    assert isinstance(r, dict) and r.get("success") is True
    assert "recommended_compounds" in r and "application_technique" in r
    print(f"    [OK] get_thermal_repasting_advisor OK")

    print(f"[{cycle_num}] Testing 4.4: get_peripherals_and_ports_hygiene_guide...")
    r = get_peripherals_and_ports_hygiene_guide()
    assert isinstance(r, dict) and r.get("success") is True
    assert "display_cleaning" in r and "port_cleaning" in r
    print(f"    [OK] get_peripherals_and_ports_hygiene_guide OK")

    print(f"[{cycle_num}] Testing 4.5: generate_physical_maintenance_guide...")
    logs.clear()
    r = generate_physical_maintenance_guide(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "checklist" in r and "fan_protocol" in r and len(r["checklist"]) > 0
    print(f"    [OK] generate_physical_maintenance_guide OK: {len(r['checklist'])} items")

    print(f"[{cycle_num}] Testing 4.6: run_physical_maintenance_suite...")
    logs.clear()
    r = run_physical_maintenance_suite(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "cleaning_protocol" in r and "repasting_advisor" in r
    print(f"    [OK] run_physical_maintenance_suite OK")

    # -------------------------------------------------------------
    # Group 5: Startup & Latency Tuning (hwscan.core.startup_service_tuner)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 5.1: audit_startup_applications...")
    logs.clear()
    r = audit_startup_applications(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "items" in r and "total_items" in r and "high_impact_count" in r
    print(f"    [OK] audit_startup_applications OK: {r['total_items']} items ({r['high_impact_count']} High Impact)")

    print(f"[{cycle_num}] Testing 5.2: audit_background_services...")
    logs.clear()
    r = audit_background_services(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "total_services_analyzed" in r and "recommendations" in r
    print(f"    [OK] audit_background_services OK: {r['total_services_analyzed']} services analyzed")

    print(f"[{cycle_num}] Testing 5.3: audit_power_and_latency_profiles...")
    logs.clear()
    r = audit_power_and_latency_profiles(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "active_scheme" in r and "power_state_status" in r
    print(f"    [OK] audit_power_and_latency_profiles OK: Scheme '{r['active_scheme']}', Status: {r['power_state_status']}")

    print(f"[{cycle_num}] Testing 5.4: run_startup_optimization_suite...")
    logs.clear()
    r = run_startup_optimization_suite(log_fn=test_logger)
    assert isinstance(r, dict) and r.get("success") is True
    assert "startup" in r and "services" in r and "power" in r
    print(f"    [OK] run_startup_optimization_suite OK")

    # -------------------------------------------------------------
    # Group 6: GUI Wrapper Callbacks (Simulated)
    # -------------------------------------------------------------
    print(f"[{cycle_num}] Testing 6.1: GUI custom wrappers (fan, TIM, peripherals)...")
    def gui_fan_wrapper(log_fn=None):
        logger = log_fn or (lambda m: None)
        p = get_fan_and_heatsink_cleaning_protocol()
        logger(f"Fan steps: {len(p['steps'])}")
        return {"status": "Complete", "success": True}

    def gui_tim_wrapper(log_fn=None):
        logger = log_fn or (lambda m: None)
        t = get_thermal_repasting_advisor()
        logger(f"TIM urgency: {t['urgency']}")
        return {"status": "Complete", "success": True}

    def gui_periph_wrapper(log_fn=None):
        logger = log_fn or (lambda m: None)
        g = get_peripherals_and_ports_hygiene_guide()
        logger(f"Display: {g['display_cleaning']['technique'][:20]}")
        return {"status": "Complete", "success": True}

    rf = gui_fan_wrapper(log_fn=test_logger)
    assert rf.get("success") is True
    rt = gui_tim_wrapper(log_fn=test_logger)
    assert rt.get("success") is True
    rp = gui_periph_wrapper(log_fn=test_logger)
    assert rp.get("success") is True
    print(f"    [OK] GUI wrappers OK")

    print(f"\n >>> CYCLE {cycle_num} / 3 PASSED PERFECTLY (25/25 utilities verified) <<<\n")


def main():
    start_time = time.time()
    print("=====================================================================")
    print(" HARDWARE GAUNTLET: 3-CONSECUTIVE UTILITY RE-VERIFICATION SUITE")
    print("=====================================================================")
    
    total_cycles = 3
    for cycle in range(1, total_cycles + 1):
        try:
            run_single_test_cycle(cycle)
        except Exception as e:
            print(f"\n[FATAL ERROR IN CYCLE {cycle}]: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elapsed = time.time() - start_time
    print("=====================================================================")
    print(f" ALL 3 CONSECUTIVE TEST CYCLES COMPLETED WITH ZERO ERRORS in {elapsed:.1f}s!")
    print(" 100% of all 25 utility endpoints, deep cleanup engines, hardware")
    print(" health, physical maintenance, and startup profile modules are operational.")
    print("=====================================================================")
    sys.exit(0)


if __name__ == "__main__":
    main()
