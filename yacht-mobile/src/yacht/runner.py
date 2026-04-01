from __future__ import annotations

import shutil
import subprocess
import tarfile
from pathlib import Path

from .cache import blob_path, yacht_home


def materialize_rootfs(layer_digests: list[str], key: str) -> Path:
    rootfs = yacht_home() / "rootfs" / key
    rootfs.mkdir(parents=True, exist_ok=True)

    marker = rootfs / ".yacht_layers_done"
    if marker.exists():
        return rootfs

    for d in layer_digests:
        layer = blob_path(d)
        if not layer.exists():
            raise FileNotFoundError(f"missing layer blob {d}; run pull with layers")
        with tarfile.open(layer, "r:*") as tf:
            tf.extractall(rootfs)
    marker.write_text("ok", encoding="utf-8")
    return rootfs


def run_local(rootfs: Path, argv: list[str]) -> int:
    proot = shutil.which("proot")
    if not proot:
        raise RuntimeError("proot not found; cannot run locally on this host")

    if not argv:
        argv = ["/bin/sh"]

    cmd = [
        proot,
        "-R",
        str(rootfs),
        "-b",
        "/dev",
        "-b",
        "/proc",
        "-w",
        "/",
        *argv,
    ]
    return subprocess.call(cmd)
