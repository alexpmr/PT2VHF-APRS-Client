"""Regressões da distribuição Linux ARM64/Raspberry Pi (mesma v1.15.6)."""
from __future__ import annotations

import io
import platform
import tarfile
from pathlib import Path

import pytest

from pt2vhf_aprs import updater


@pytest.mark.parametrize("machine,expected", [
    ("aarch64", "PT2VHF_APRS_Client_Linux_arm64_v1.15.6.tar.gz"),
    ("arm64", "PT2VHF_APRS_Client_Linux_arm64_v1.15.6.tar.gz"),
    ("x86_64", "PT2VHF_APRS_Client_Linux_x86_64_v1.15.6.tar.gz"),
])
def test_tar_asset_arch(monkeypatch, machine, expected):
    monkeypatch.setattr(platform, "machine", lambda: machine)
    monkeypatch.setattr(updater, "current_update_mode", lambda: "linux-tar")
    assert updater.desired_asset_name("1.15.6") == expected


@pytest.mark.parametrize("machine,expected", [
    ("aarch64", "PT2VHF_APRS_Client_arm64_v1.15.6.AppImage"),
    ("x86_64", "PT2VHF_APRS_Client_x86_64_v1.15.6.AppImage"),
])
def test_appimage_asset_arch(monkeypatch, machine, expected):
    monkeypatch.setattr(platform, "machine", lambda: machine)
    monkeypatch.setattr(updater, "current_update_mode", lambda: "linux-appimage")
    assert updater.desired_asset_name("1.15.6") == expected


def test_arm64_tar_upgrade_extracts_matching_architecture(tmp_path, monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path / "staging")
    archive = tmp_path / "arm64.tar.gz"
    target = "PT2VHF_APRS_Client_Linux_arm64_v1.15.6"
    payload = b"verified arm64 payload"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo(target)
        info.size = len(payload)
        info.mode = 0o755
        tar.addfile(info, io.BytesIO(payload))
    result = updater._prepare_linux_tar({"path": str(archive), "version": "1.15.6"})
    assert result.name == target
    assert result.read_bytes() == payload
    assert result.stat().st_mode & 0o111


def test_arm64_tar_upgrade_does_not_silently_select_x86(tmp_path, monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path / "staging")
    archive = tmp_path / "bad.tar.gz"
    data = b"x86-64"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("PT2VHF_APRS_Client_Linux_x86_64_v1.15.6")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    with pytest.raises(ValueError, match="arm64"):
        updater._prepare_linux_tar({"path": str(archive), "version": "1.15.6"})


def test_linux_spec_builds_correct_native_bootloader():
    spec = (Path(__file__).resolve().parents[1] / "linux/PT2VHF_APRS_Client_Linux.spec").read_text()
    assert "platform.machine()" in spec
    assert "name=f'PT2VHF_APRS_Client_Linux_{ARCH}'" in spec
