"""Developer tool to package and publish updates to the Hardware Gauntlet Update Channel.

Allows pushing code fixes, new diagnostics, or UI enhancements as lightweight
modular hot-patch bundles without recompiling the 34 MB standalone executable.

Usage:
    python scripts/push_update.py --channel stable --version 1.0.1 --notes "Added new diagnostics"
    python scripts/push_update.py --channel beta --apply-local
"""

import os
import sys
import json
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hwscan import __version__
from hwscan.core.update_channel import (
    CHANNELS,
    DEFAULT_CHANNEL,
    create_patch_bundle,
    apply_patch_bundle
)


def main():
    parser = argparse.ArgumentParser(
        description="Publish modular updates to the Hardware Gauntlet Update Channel"
    )
    parser.add_argument(
        "--channel",
        choices=CHANNELS,
        default=DEFAULT_CHANNEL,
        help=f"Target update channel (default: {DEFAULT_CHANNEL})"
    )
    parser.add_argument(
        "--version",
        default="1.0.1",
        help="Update version string (e.g., 1.0.1)"
    )
    parser.add_argument(
        "--notes",
        nargs="+",
        default=["Modular patch release", "Performance and stability enhancements"],
        help="Release notes describing this update"
    )
    parser.add_argument(
        "--apply-local",
        action="store_true",
        help="Immediately apply the generated patch bundle locally to test with HardwareGauntlet.exe"
    )

    args = parser.parse_args()

    print("=" * 60)
    print(" [*] HARDWARE GAUNTLET - UPDATE CHANNEL PUBLISHER")
    print("=" * 60)
    print(f"[*] Target Channel: {args.channel.upper()}")
    print(f"[*] Target Version: {args.version} (Base: v{__version__})")

    # Destination paths
    patch_dir = os.path.join(REPO_ROOT, "dist", "patches")
    channels_dir = os.path.join(REPO_ROOT, "channels")
    os.makedirs(patch_dir, exist_ok=True)
    os.makedirs(channels_dir, exist_ok=True)

    out_zip = os.path.join(patch_dir, f"{args.channel}-patch-v{args.version}.zip")
    src_dir = os.path.join(REPO_ROOT, "hwscan")

    print(f"[*] Compressing module tree from: {src_dir}")
    manifest = create_patch_bundle(
        source_dir=src_dir,
        output_zip=out_zip,
        channel=args.channel,
        version=args.version,
        notes=args.notes
    )

    # Set public patch URL format
    manifest.patch_url = (
        f"https://raw.githubusercontent.com/Agulhaaq/Hardware-Gauntlet/main/dist/patches/"
        f"{args.channel}-patch-v{args.version}.zip"
    )

    # Write channel manifest
    manifest_file = os.path.join(channels_dir, f"{args.channel}.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    print(f"[+] Generated Patch ZIP: {out_zip} ({manifest.patch_size_bytes} bytes)")
    print(f"[+] Computed SHA-256: {manifest.patch_sha256}")
    print(f"[+] Channel Manifest: {manifest_file}")

    if args.apply_local:
        print("\n[*] Applying patch bundle locally into ./patches/ ...")
        success, msg = apply_patch_bundle(out_zip, manifest.patch_sha256)
        print(f"[{'+' if success else '!'}] {msg}")

    print("\n[+] Update ready! To distribute, simply push with git:")
    print(f"    git add channels/ dist/patches/")
    print(f'    git commit -m "release({args.channel}): publish v{args.version} hot-patch"')
    print(f"    git push origin main")
    print("=" * 60)


if __name__ == "__main__":
    main()
