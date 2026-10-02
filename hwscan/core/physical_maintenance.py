"""Hardware Gauntlet - Physical Hardware Maintenance & Inspection Guide Module.

Provides step-by-step physical maintenance guidance, fan blowout and bearing protection
protocols, thermal paste application advisors, and port/display hygiene standards.
Cross-platform compatible across Windows, Linux, and macOS.
"""

from __future__ import annotations

import platform
import sys
from typing import Any, Callable, Dict, List, Optional

import psutil


def _default_logger(msg: str) -> None:
    pass


def detect_chassis_form_factor() -> str:
    """Detect whether system is a Laptop/Notebook or a Desktop/Workstation.
    
    Uses battery presence, battery charge capability, and platform chassis indicators.
    """
    try:
        batt = psutil.sensors_battery()
        if batt is not None:
            return "LAPTOP"
    except Exception:
        pass

    # Platform-specific fallbacks
    if sys.platform == "win32":
        try:
            import subprocess
            cmd = "powershell -NoProfile -Command \"(Get-CimInstance -ClassName Win32_SystemEnclosure).ChassisTypes[0]\""
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            val = res.stdout.strip()
            if val in ("8", "9", "10", "11", "12", "14", "30", "31", "32"):  # Laptop / Notebook / Subnotebook / Convertible
                return "LAPTOP"
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        try:
            import os
            if os.path.exists("/sys/class/power_supply/BAT0") or os.path.exists("/sys/class/power_supply/BAT1"):
                return "LAPTOP"
            with open("/sys/class/dmi/id/chassis_type", "r") as f:
                chassis = f.read().strip()
                if chassis in ("8", "9", "10", "11", "12", "14", "30", "31", "32"):
                    return "LAPTOP"
        except Exception:
            pass

    return "DESKTOP"


def get_fan_and_heatsink_cleaning_protocol(chassis_type: str = "auto") -> Dict[str, Any]:
    """Retrieve detailed fan bearing protection and heatsink dust extraction protocols."""
    if chassis_type == "auto":
        chassis_type = detect_chassis_form_factor()

    is_laptop = chassis_type.upper() == "LAPTOP"

    tools = [
        "Canned compressed air (held strictly vertical) or electric air duster",
        "Non-conductive probe (wooden toothpick, plastic spudger, or cotton swab)",
        "Soft-bristled antistatic detailing brush",
        "ESD-safe anti-static wrist strap or grounded work surface",
        "Phillips #0 / #00 screwdriver (for laptops) or #2 screwdriver (for desktops)"
    ]

    warnings = [
        "CRITICAL: Always immobilize fan blades using a toothpick or probe before applying compressed air! Unrestricted high-speed spinning generates reverse Back-EMF voltage that can fry motherboard fan headers, and will destroy sleeve/fluid bearings.",
        "Keep the compressed air canister upright at all times (> 45 degrees); never invert or shake during use, as liquid refrigerant propellant can freeze and crack delicate silicon dies.",
        "Always power off the computer, disconnect AC power, and disconnect the internal battery (laptop) or switch off PSU toggle (desktop) before servicing."
    ]

    if is_laptop:
        steps = [
            "1. Power down completely, unplug charger, and press power button for 15s to discharge capacitors.",
            "2. Remove bottom panel screws and lift casing carefully, being mindful of ribbon cables and audio jacks.",
            "3. Disconnect internal battery connector before touching heatsinks or fans.",
            "4. Gently hold blower fan blades static with a toothpick.",
            "5. Direct short bursts of compressed air through exhaust fin stacks from the inside OUTWARD, dislodging the compacted dust felt/blanket.",
            "6. Brush loose dust from fan blades with an antistatic brush.",
            "7. Reconnect battery, snap chassis into place, and secure screws."
        ]
    else:
        steps = [
            "1. Shut down PC, toggle PSU rocker switch to '0', and unplug the main power cable.",
            "2. Press and hold power button on the front panel for 10 seconds to bleed residual capacitance.",
            "3. Open side tempered glass or steel panel in a dust-tolerant area.",
            "4. Hold intake, exhaust, and CPU heatsink/AIO fan blades static with a finger or wooden probe.",
            "5. Blow compressed air through radiator fins and heatsink aluminum towers in short bursts.",
            "6. Clean lower power supply dust filter mesh by sliding it out and vacuuming/rinsing (ensure fully dry before reinsertion).",
            "7. Wipe chassis bottom interior with a dry microfiber cloth and reassemble."
        ]

    return {
        "chassis": chassis_type,
        "tools_required": tools,
        "warnings": warnings,
        "steps": steps
    }


def get_thermal_repasting_advisor(cpu_temp: Optional[float] = None) -> Dict[str, Any]:
    """Provide thermal interface material (TIM) selection, repasting schedule, and pump-out prevention advice."""
    urgency = "PREVENTATIVE"
    if cpu_temp is not None and cpu_temp >= 85.0:
        urgency = "URGENT (Elevated Thermals Detected)"

    compounds = [
        {
            "name": "Honeywell PTM7950 Phase-Change Material",
            "best_for": "Laptops & Direct-Die Cooling",
            "advantage": "Eliminates thermal paste pump-out effect; solid at room temp, melts at 45°C into ultra-thin thermal layer; lasts 5+ years without drying."
        },
        {
            "name": "Thermal Grizzly Kryonaut Extreme / Arctic MX-6",
            "best_for": "Desktop CPUs with Integrated Heat Spreaders (IHS)",
            "advantage": "High thermal conductivity (> 14 W/mK), high viscosity resists degradation, non-conductive and non-capacitive."
        },
        {
            "name": "Noctua NT-H2",
            "best_for": "All-Round Long-Term Reliability",
            "advantage": "Very low dry-out tendency, balanced viscosity, effortless cleanup with included cleaning wipes."
        }
    ]

    warnings = [
        "NEVER use Liquid Metal (Gallium alloy) on aluminum heatsinks! Gallium aggressively amalgamates with aluminum, causing brittle structural failure and catastrophic heatpipe disintegration within hours.",
        "Ensure thermal paste is 100% non-conductive to prevent electrical short-circuits across exposed SMD capacitors around the CPU/GPU die.",
        "Clean old, baked-on paste thoroughly using 99% Isopropyl Alcohol (IPA) and lint-free wipes until the copper coldplate and silicon die shine mirror-clean."
    ]

    application = [
        "Direct-Die (Laptops / Delidded): Thin, uniform manual spread across the entire silicon surface using a spatula so zero bare silicon is exposed.",
        "Desktop CPU with IHS (AM4/AM5/LGA1700): Centered pea-sized dot (~4mm) or five-point dice pattern. The mounting pressure of the heatsink will spread it evenly without air bubbles."
    ]

    return {
        "urgency": urgency,
        "recommended_compounds": compounds,
        "application_technique": application,
        "warnings": warnings,
        "interval_years": "2 to 3 years for conventional paste, 5+ years for PTM7950 phase-change pads"
    }


def get_peripherals_and_ports_hygiene_guide() -> Dict[str, Any]:
    """Provide safe cleaning procedures for display screens, ports, and keyboard keycaps."""
    return {
        "display_cleaning": {
            "technique": "Use an ultra-soft, clean microfiber cloth lightly dampened with distilled water or dedicated 70% screen cleaning solution. Wipe in gentle horizontal or vertical strokes.",
            "avoid": "NEVER use Windex, ammonia, acetone, paper towels, or household glass cleaner. These dissolve anti-reflective (AR) and oleophobic matte coatings permanently."
        },
        "port_cleaning": {
            "technique": "Inspect USB-C, Thunderbolt, and HDMI ports with a flashlight. Use a carved non-conductive wooden toothpick or plastic dental flosser to gently hook compacted pocket lint out.",
            "avoid": "NEVER insert metal pins, paperclips, or needles into USB-C ports, as shorting VBUS (up to 48V under PD 3.1) directly into CC pins will fry the controller."
        },
        "keyboard_cleaning": {
            "technique": "Turn keyboard or laptop at a 75-degree angle. Use short bursts of compressed air in a zig-zag sweep. Wipe key surfaces with 70% Isopropyl Alcohol on a microfiber cloth.",
            "avoid": "Never spray liquids directly onto the keyboard deck; liquids seep through membrane switch cuts into the battery or motherboard."
        },
        "prohibited_substances": [
            "Acetone / Nail Polish Remover (melts ABS plastics instantly)",
            "Bleach / Chlorine agents",
            "Ammonia / Window Cleaner",
            "Abrasive melamine sponges (Magic Erasers) on glossy or matte finishes"
        ]
    }


def generate_physical_maintenance_guide(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Generate a comprehensive customized physical maintenance plan for the current system."""
    logger = log_fn or _default_logger
    form_factor = detect_chassis_form_factor()

    logger(f"[PHYSICAL-MAINTENANCE] Detected Form Factor: {form_factor}")
    logger(f"[PHYSICAL-MAINTENANCE] Evaluating chassis maintenance protocols and TIM schedules...")

    fan_protocol = get_fan_and_heatsink_cleaning_protocol(form_factor)
    tim_advisor = get_thermal_repasting_advisor()
    peripherals = get_peripherals_and_ports_hygiene_guide()

    checklist = [
        {"item": "Exhaust fin stack & blower fan de-dusting", "frequency": "Every 6-12 Months", "priority": "High"},
        {"item": "Thermal interface material (TIM) inspection/repasting", "frequency": "Every 24-36 Months", "priority": "Medium-High"},
        {"item": "Port lint extraction (USB-C / Thunderbolt)", "frequency": "Every 6 Months", "priority": "Medium"},
        {"item": "Keyboard debris blowout & surface sanitization", "frequency": "Every 3 Months", "priority": "Regular"},
        {"item": "Display panel anti-glare safe cleaning", "frequency": "As Needed (Bi-weekly)", "priority": "Regular"}
    ]

    logger(f"[PHYSICAL-MAINTENANCE] Generated {len(checklist)} maintenance checklist items.")
    for item in checklist:
        logger(f"  * {item['item']} ({item['frequency']}) - Priority: {item['priority']}")

    return {
        "form_factor": form_factor,
        "checklist": checklist,
        "fan_protocol": fan_protocol,
        "tim_advisor": tim_advisor,
        "peripherals_guide": peripherals
    }


def run_physical_maintenance_suite(log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Run full interactive physical maintenance diagnostic suite and output actionable guidance."""
    logger = log_fn or _default_logger
    logger("=================================================================")
    logger("   HARDWARE GAUNTLET: PHYSICAL MAINTENANCE & CLEANING ADVISOR    ")
    logger("=================================================================")

    form_factor = detect_chassis_form_factor()
    logger(f"[SYSTEM-PROFILE] Chassis Type: {form_factor} | Platform: {platform.system()} {platform.release()}")

    # Fan protocol
    logger("\n[1/3] FAN & HEATSINK CLEANING SAFETY PROTOCOL:")
    protocol = get_fan_and_heatsink_cleaning_protocol(form_factor)
    for warn in protocol["warnings"]:
        logger(f"  [!] {warn}")
    for step in protocol["steps"][:4]:
        logger(f"  -> {step}")

    # TIM repasting
    logger("\n[2/3] THERMAL PASTE & TIM PUMP-OUT ADVISORY:")
    tim = get_thermal_repasting_advisor()
    logger(f"  Status: {tim['urgency']} | Recommended Repaste Cycle: {tim['interval_years']}")
    logger(f"  Top Recommended Compound: {tim['recommended_compounds'][0]['name']}")
    logger(f"    Best for: {tim['recommended_compounds'][0]['best_for']}")

    # Port & screen care
    logger("\n[3/3] PORT & PERIPHERAL HYGIENE:")
    peripherals = get_peripherals_and_ports_hygiene_guide()
    logger(f"  Display: {peripherals['display_cleaning']['technique'][:90]}...")
    logger(f"  USB-C Ports: {peripherals['port_cleaning']['technique'][:90]}...")

    logger("\n[COMPLETED] Physical maintenance checklist and safety guidelines generated.")
    logger("=================================================================")

    return {
        "form_factor": form_factor,
        "cleaning_protocol": protocol,
        "repasting_advisor": tim,
        "peripherals_guide": peripherals
    }
