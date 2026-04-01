from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageRef:
    registry: str
    repository: str
    reference: str

    @property
    def canonical(self) -> str:
        return f"{self.registry}/{self.repository}:{self.reference}"


def parse_image_ref(raw: str) -> ImageRef:
    raw = raw.strip()
    if not raw:
        raise ValueError("image reference cannot be empty")

    registry = "registry-1.docker.io"
    repository = raw
    reference = "latest"

    if "@" in raw:
        raw, reference = raw.split("@", 1)
    elif ":" in raw.rsplit("/", 1)[-1]:
        raw, reference = raw.rsplit(":", 1)

    parts = raw.split("/", 1)
    if len(parts) == 2 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        registry = parts[0]
        repository = parts[1]
    else:
        repository = raw

    if "/" not in repository and registry == "registry-1.docker.io":
        repository = f"library/{repository}"

    return ImageRef(registry=registry, repository=repository, reference=reference)
