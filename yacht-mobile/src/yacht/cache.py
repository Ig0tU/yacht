from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .image_ref import ImageRef


def yacht_home() -> Path:
    return Path.home() / ".yacht"


def ensure_dirs() -> None:
    for p in (
        yacht_home() / "images",
        yacht_home() / "blobs",
        yacht_home() / "rootfs",
        yacht_home() / "hydration",
    ):
        p.mkdir(parents=True, exist_ok=True)


def image_key(ref: ImageRef) -> str:
    return hashlib.sha256(ref.canonical.encode("utf-8")).hexdigest()[:20]


def image_dir(ref: ImageRef) -> Path:
    return yacht_home() / "images" / image_key(ref)


def blob_path(digest: str) -> Path:
    algo, value = digest.split(":", 1)
    return yacht_home() / "blobs" / algo / value


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
