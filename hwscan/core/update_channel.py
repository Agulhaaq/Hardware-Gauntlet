"""Hardware Gauntlet - Update Channel & Dynamic Modular Hot-Patch Engine.

Enables seamless in-place updates via dedicated channels (Stable, Beta, Nightly)
without recompiling or replacing the 34 MB standalone portable executable.
"""

import os
import sys
import json
import shutil
import zipfile
import hashlib
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple, Callable

from hwscan import __version__

CHANNELS = ("stable", "beta", "nightly")
DEFAULT_CHANNEL = "stable"
GITHUB_REPO = "Agulhaaq/Hardware-Gauntlet"
MANIFEST_URL_TEMPLATE = "https://raw.githubusercontent.com/{repo}/main/channels/{channel}.json"


@dataclass
class ChannelManifest:
    channel: str = "stable"
    version: str = "1.0.0"
    min_app_version: str = "1.0.0"
    release_date: str = ""
    patch_url: str = ""
    patch_sha256: str = ""
    patch_size_bytes: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChannelManifest":
        return cls(
            channel=data.get("channel", "stable"),
            version=data.get("version", "1.0.0"),
            min_app_version=data.get("min_app_version", "1.0.0"),
            release_date=data.get("release_date", ""),
            patch_url=data.get("patch_url", ""),
            patch_sha256=data.get("patch_sha256", ""),
            patch_size_bytes=int(data.get("patch_size_bytes", 0)),
            notes=list(data.get("notes", []))
        )


def get_base_directory() -> str:
    """Return the runtime directory where the executable or source resides."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_patch_directory(base_dir: Optional[str] = None) -> str:
    """Return the path to the active hot-patch directory."""
    root = base_dir or get_base_directory()
    return os.path.join(root, "patches")


def get_config_path(config_path: Optional[str] = None) -> str:
    """Return the configuration file path for the update channel preference."""
    if config_path:
        return config_path
    return os.path.join(get_base_directory(), "channel_config.json")


def get_current_channel(config_path: Optional[str] = None) -> str:
    """Read the active update channel ('stable', 'beta', or 'nightly')."""
    cfg_file = get_config_path(config_path)
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                ch = data.get("channel", DEFAULT_CHANNEL).lower()
                if ch in CHANNELS:
                    return ch
        except Exception:
            pass
    return DEFAULT_CHANNEL


def set_current_channel(channel: str, config_path: Optional[str] = None) -> bool:
    """Save the active update channel preference."""
    ch = channel.lower().strip()
    if ch not in CHANNELS:
        return False
    cfg_file = get_config_path(config_path)
    try:
        data = {}
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["channel"] = ch
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def compute_file_sha256(filepath: str) -> str:
    """Calculate the SHA-256 hex digest of a local file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def verify_checksum(filepath: str, expected_sha256: str) -> bool:
    """Verify that a file matches the expected SHA-256 checksum."""
    if not os.path.exists(filepath):
        return False
    actual = compute_file_sha256(filepath)
    return actual == expected_sha256.strip().lower()


def init_patch_loader(override_dir: Optional[str] = None) -> bool:
    """Dynamically load and prepend the patches directory to sys.path on startup.
    
    This ensures that patched modules are loaded in-place of frozen executable code
    without needing to replace the original binary.
    """
    patch_dir = override_dir or get_patch_directory()
    if os.path.isdir(patch_dir):
        # Verify that the directory contains Python modules
        has_py = False
        for root, _, files in os.walk(patch_dir):
            if any(f.endswith(".py") for f in files):
                has_py = True
                break
        if has_py:
            if patch_dir in sys.path:
                sys.path.remove(patch_dir)
            sys.path.insert(0, patch_dir)
            return True
    return False


def get_active_patch_metadata(base_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return active patch metadata if a hot-patch is currently loaded."""
    patch_dir = get_patch_directory(base_dir)
    meta_path = os.path.join(patch_dir, "patch_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def create_patch_bundle(
    source_dir: str,
    output_zip: str,
    channel: str = "stable",
    version: str = "1.0.1",
    notes: Optional[List[str]] = None
) -> ChannelManifest:
    """Package source Python files into a compact patch ZIP and generate its manifest."""
    os.makedirs(os.path.dirname(os.path.abspath(output_zip)), exist_ok=True)
    notes_list = notes or [f"Release update {version}"]

    # Collect files
    ignore_dirs = {"__pycache__", ".git", ".pytest_cache", "build", "dist", ".venv", "venv"}
    ignore_exts = {".pyc", ".pyo", ".pyd", ".exe", ".spec"}

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        meta = {
            "channel": channel,
            "version": version,
            "base_version": __version__,
            "notes": notes_list
        }
        zf.writestr("patch_meta.json", json.dumps(meta, indent=2))

        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ignore_exts:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(os.path.abspath(source_dir)))
                zf.write(full_path, rel_path)

    sha = compute_file_sha256(output_zip)
    size = os.path.getsize(output_zip)

    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return ChannelManifest(
        channel=channel,
        version=version,
        min_app_version=__version__,
        release_date=now_iso,
        patch_url="",
        patch_sha256=sha,
        patch_size_bytes=size,
        notes=notes_list
    )


def apply_patch_bundle(
    patch_zip_path: str,
    expected_sha256: str,
    target_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """Validate checksum and extract patch ZIP into the active patch directory."""
    if not os.path.exists(patch_zip_path):
        return False, f"Patch file not found: {patch_zip_path}"

    if expected_sha256:
        if not verify_checksum(patch_zip_path, expected_sha256):
            return False, f"Checksum verification failed for {os.path.basename(patch_zip_path)}"

    dest_dir = target_dir or get_patch_directory()
    try:
        # Create or clear existing patch directory
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(dest_dir, exist_ok=True)

        with zipfile.ZipFile(patch_zip_path, "r") as zf:
            zf.extractall(dest_dir)

        # Prepend to runtime path immediately
        init_patch_loader(override_dir=dest_dir)
        return True, f"Patch applied successfully to {dest_dir}"
    except Exception as ex:
        return False, f"Failed to apply patch: {str(ex)}"


def rollback_patch(target_dir: Optional[str] = None) -> Tuple[bool, str]:
    """Remove the active patch directory to revert application to factory standalone binary."""
    dest_dir = target_dir or get_patch_directory()
    if os.path.exists(dest_dir):
        try:
            shutil.rmtree(dest_dir, ignore_errors=True)
            if dest_dir in sys.path:
                sys.path.remove(dest_dir)
            return True, "Patch rolled back. Reverted to factory standalone executable."
        except Exception as ex:
            return False, f"Rollback failed: {str(ex)}"
    return True, "No active patch installed. System already in factory state."


def check_for_updates(
    channel: Optional[str] = None,
    custom_manifest_url: Optional[str] = None,
    timeout_sec: int = 5
) -> Tuple[bool, Optional[ChannelManifest], str]:
    """Check the specified update channel for newer patch releases."""
    active_channel = (channel or get_current_channel()).lower()
    url = custom_manifest_url or MANIFEST_URL_TEMPLATE.format(repo=GITHUB_REPO, channel=active_channel)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"HardwareGauntlet-Updater/{__version__}"}
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            manifest = ChannelManifest.from_dict(data)

            # Version comparison
            curr_v = tuple(int(x) for x in __version__.split(".") if x.isdigit())
            new_v = tuple(int(x) for x in manifest.version.split(".") if x.isdigit())

            active_patch = get_active_patch_metadata()
            if active_patch:
                patch_v = tuple(int(x) for x in active_patch.get("version", "0.0.0").split(".") if x.isdigit())
                curr_v = max(curr_v, patch_v)

            if new_v > curr_v:
                return True, manifest, f"New version {manifest.version} available on channel '{active_channel}'"
            return False, manifest, f"Up to date. Active version is {manifest.version} on channel '{active_channel}'"
    except Exception as err:
        return False, None, f"Update check unavailable: {str(err)}"


def download_and_apply_patch(
    manifest: ChannelManifest,
    temp_dir: Optional[str] = None,
    log_fn: Optional[Callable[[str], None]] = None
) -> Tuple[bool, str]:
    """Download patch from manifest URL and apply it in-place."""
    def log(msg: str):
        if log_fn:
            log_fn(msg)

    if not manifest.patch_url:
        return False, "Manifest does not specify a patch URL."

    t_dir = temp_dir or os.path.join(get_base_directory(), ".tmp_update")
    os.makedirs(t_dir, exist_ok=True)
    dl_path = os.path.join(t_dir, f"patch-{manifest.version}.zip")

    try:
        log(f"Downloading patch from {manifest.patch_url}...")
        urllib.request.urlretrieve(manifest.patch_url, dl_path)
        log("Verifying checksum integrity...")
        success, msg = apply_patch_bundle(dl_path, manifest.patch_sha256)
        return success, msg
    except Exception as ex:
        return False, f"Download failed: {str(ex)}"
    finally:
        shutil.rmtree(t_dir, ignore_errors=True)
