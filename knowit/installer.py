"""
Installs fzf and bat into ~/.knowit/bin/ so knowit uses its own
managed binaries, independent of whatever the host may have installed.
"""
import platform
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from knowit._paths import BAT_BIN, BIN_DIR, FZF_BIN

# Pinned versions — update here to upgrade bundled tools
FZF_VERSION = "0.70.0"
BAT_VERSION = "0.25.0"


def _detect_platform():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "darwin"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    if machine in ("x86_64", "amd64"):
        arch = "amd64"
        arch_bat = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
        arch_bat = "aarch64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    return os_name, arch, arch_bat


def _download(url, dest_path):
    print(f"  Downloading {url}")
    urllib.request.urlretrieve(url, dest_path)


def _make_executable(path):
    p = Path(path)
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _install_fzf(os_name, arch):
    filename = f"fzf-{FZF_VERSION}-{os_name}_{arch}.tar.gz"
    url = f"https://github.com/junegunn/fzf/releases/download/v{FZF_VERSION}/{filename}"

    with tempfile.TemporaryDirectory() as tmp:
        archive = str(Path(tmp) / filename)
        _download(url, archive)
        with tarfile.open(archive, "r:gz") as tar:
            member = tar.getmember("fzf")
            member.name = "fzf"
            tar.extract(member, path=tmp)
        import shutil
        shutil.move(str(Path(tmp) / "fzf"), FZF_BIN)

    _make_executable(FZF_BIN)
    print(f"  fzf {FZF_VERSION} installed to {FZF_BIN}")


def _install_bat(os_name, arch, arch_bat):
    if os_name == "linux":
        triple = f"{arch_bat}-unknown-linux-musl"
    else:
        triple = f"{arch_bat}-apple-darwin"

    dirname = f"bat-v{BAT_VERSION}-{triple}"
    filename = f"{dirname}.tar.gz"
    url = f"https://github.com/sharkdp/bat/releases/download/v{BAT_VERSION}/{filename}"

    with tempfile.TemporaryDirectory() as tmp:
        archive = str(Path(tmp) / filename)
        _download(url, archive)
        with tarfile.open(archive, "r:gz") as tar:
            bat_member_name = f"{dirname}/bat"
            member = tar.getmember(bat_member_name)
            member.name = "bat"
            tar.extract(member, path=tmp)
        import shutil
        shutil.move(str(Path(tmp) / "bat"), BAT_BIN)

    _make_executable(BAT_BIN)
    print(f"  bat {BAT_VERSION} installed to {BAT_BIN}")


def install():
    print(f"Installing knowit tools into {BIN_DIR} ...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    try:
        os_name, arch, arch_bat = _detect_platform()
    except RuntimeError as e:
        print(f"[!] {e}", file=sys.stderr)
        sys.exit(1)

    try:
        _install_fzf(os_name, arch)
    except Exception as e:
        print(f"[!] Failed to install fzf: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        _install_bat(os_name, arch, arch_bat)
    except Exception as e:
        print(f"[!] Failed to install bat: {e}", file=sys.stderr)
        sys.exit(1)

    print("Done. Run 'knowit browse' to get started.")
