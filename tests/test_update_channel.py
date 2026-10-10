"""Unit and integration tests for Update Channel and Dynamic Patch Overlay Engine."""

import os
import sys
import json
import zipfile
import hashlib
import tempfile
import pytest

from hwscan.core.update_channel import (
    CHANNELS,
    DEFAULT_CHANNEL,
    get_current_channel,
    set_current_channel,
    get_patch_directory,
    create_patch_bundle,
    verify_checksum,
    apply_patch_bundle,
    rollback_patch,
    init_patch_loader,
    ChannelManifest
)


def test_channel_constants():
    assert "stable" in CHANNELS
    assert "beta" in CHANNELS
    assert "nightly" in CHANNELS
    assert DEFAULT_CHANNEL == "stable"


def test_channel_preference_roundtrip(tmp_path):
    config_file = str(tmp_path / "channel_config.json")
    
    # Default channel
    ch = get_current_channel(config_path=config_file)
    assert ch == "stable"

    # Set to beta
    success = set_current_channel("beta", config_path=config_file)
    assert success
    assert get_current_channel(config_path=config_file) == "beta"

    # Set to nightly
    success = set_current_channel("nightly", config_path=config_file)
    assert success
    assert get_current_channel(config_path=config_file) == "nightly"

    # Invalid channel rejected
    success = set_current_channel("invalid_channel", config_path=config_file)
    assert not success
    assert get_current_channel(config_path=config_file) == "nightly"


def test_create_patch_bundle(tmp_path):
    # Create mock source package
    src_dir = tmp_path / "src_pkg"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("# init", encoding="utf-8")
    (src_dir / "module.py").write_text("VALUE = 42", encoding="utf-8")
    pycache = src_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "module.pyc").write_text("binary", encoding="utf-8")

    out_zip = str(tmp_path / "test_patch.zip")
    manifest = create_patch_bundle(
        source_dir=str(src_dir),
        output_zip=out_zip,
        channel="stable",
        version="1.0.1",
        notes=["Test note 1", "Test note 2"]
    )

    assert os.path.exists(out_zip)
    assert manifest.version == "1.0.1"
    assert manifest.channel == "stable"
    assert len(manifest.patch_sha256) == 64
    assert manifest.patch_size_bytes > 0

    # Ensure __pycache__ was excluded
    with zipfile.ZipFile(out_zip, "r") as zf:
        names = zf.namelist()
        assert any("module.py" in n for n in names)
        assert not any("__pycache__" in n for n in names)


def test_verify_checksum(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Hardware Gauntlet Update Engine", encoding="utf-8")
    
    hasher = hashlib.sha256()
    hasher.update(test_file.read_bytes())
    correct_sha = hasher.hexdigest()

    assert verify_checksum(str(test_file), correct_sha)
    assert not verify_checksum(str(test_file), "0" * 64)


def test_apply_and_rollback_patch(tmp_path):
    patch_zip = tmp_path / "patch.zip"
    with zipfile.ZipFile(str(patch_zip), "w") as zf:
        zf.writestr("hwscan/patched.py", "PATCHED = True\n")
        zf.writestr("patch_meta.json", json.dumps({"version": "1.0.1"}))

    hasher = hashlib.sha256()
    hasher.update(patch_zip.read_bytes())
    sha = hasher.hexdigest()

    target_patch_dir = str(tmp_path / "patches")
    
    # 1. Apply with valid checksum
    success, msg = apply_patch_bundle(str(patch_zip), sha, target_dir=target_patch_dir)
    assert success
    assert "Patch applied successfully" in msg
    assert os.path.exists(os.path.join(target_patch_dir, "hwscan", "patched.py"))

    # 2. Apply with invalid checksum fails
    bad_success, bad_msg = apply_patch_bundle(str(patch_zip), "bad_hash", target_dir=target_patch_dir)
    assert not bad_success
    assert "Checksum verification failed" in bad_msg

    # 3. Rollback removes the patch dir
    rb_success, rb_msg = rollback_patch(target_dir=target_patch_dir)
    assert rb_success
    assert not os.path.exists(os.path.join(target_patch_dir, "hwscan", "patched.py"))


def test_init_patch_loader(tmp_path, monkeypatch):
    target_patch_dir = str(tmp_path / "patches")
    os.makedirs(os.path.join(target_patch_dir, "hwscan"), exist_ok=True)
    with open(os.path.join(target_patch_dir, "hwscan", "test_hot.py"), "w", encoding="utf-8") as f:
        f.write("HOT_RELOAD = True\n")

    orig_sys_path = list(sys.path)
    try:
        loaded = init_patch_loader(override_dir=target_patch_dir)
        assert loaded is True
        assert sys.path[0] == target_patch_dir
    finally:
        sys.path = orig_sys_path


def test_zip_slip_rejection(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    with zipfile.ZipFile(str(bad_zip), "w") as zf:
        zf.writestr("../evil.txt", "exploit")
    hasher = hashlib.sha256()
    hasher.update(bad_zip.read_bytes())
    sha = hasher.hexdigest()

    target_dir = str(tmp_path / "patches")
    success, msg = apply_patch_bundle(str(bad_zip), sha, target_dir=target_dir)
    assert not success
    assert "traversal" in msg.lower()
