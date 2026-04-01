from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .remote_docker import RemoteDocker


@dataclass
class ComposeService:
    name: str
    image: str
    command: list[str] | None
    env: list[str]
    container_name: str | None


def _normalize_env(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [f"{k}={v}" for k, v in raw.items()]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    raise ValueError("environment must be dict or list")


def _normalize_command(raw: Any) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        # Docker accepts string command through shell; keep simple split for MVP.
        return raw.strip().split()
    raise ValueError("command must be list or string")


def parse_compose(path: Path) -> list[ComposeService]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "services" not in doc:
        raise ValueError("compose file missing services")
    services_doc = doc["services"]
    if not isinstance(services_doc, dict):
        raise ValueError("services must be mapping")

    services: list[ComposeService] = []
    for name, raw in services_doc.items():
        if not isinstance(raw, dict):
            raise ValueError(f"service {name} must be mapping")
        image = raw.get("image")
        if not image:
            raise ValueError(f"service {name} missing image")
        services.append(
            ComposeService(
                name=str(name),
                image=str(image),
                command=_normalize_command(raw.get("command")),
                env=_normalize_env(raw.get("environment")),
                container_name=str(raw["container_name"]) if "container_name" in raw else None,
            )
        )
    return services


def compose_up(remote: RemoteDocker, compose_file: Path) -> list[dict[str, str]]:
    started: list[dict[str, str]] = []
    for svc in parse_compose(compose_file):
        remote.ensure_image(svc.image)
        cid = remote.create_container(
            image=svc.image,
            command=svc.command,
            env=svc.env,
            name=svc.container_name or svc.name,
        )
        remote.start_container(cid)
        started.append({"service": svc.name, "container_id": cid, "image": svc.image})
    return started
