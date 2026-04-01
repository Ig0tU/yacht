from __future__ import annotations

from typing import Any

import yaml

from .remote_exec import RemoteDocker


def _env_to_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [f"{k}={v}" for k, v in raw.items()]
    if isinstance(raw, list):
        return [str(v) for v in raw]
    raise ValueError("environment must be dict or list")


def _cmd_to_list(raw: Any) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, str):
        return raw.split()
    raise ValueError("command must be list or string")


def compose_up_from_yaml(remote: RemoteDocker, compose_yaml: str) -> list[dict[str, str]]:
    doc = yaml.safe_load(compose_yaml)
    if not isinstance(doc, dict) or not isinstance(doc.get("services"), dict):
        raise ValueError("compose yaml must define services")
    started: list[dict[str, str]] = []
    for name, service in doc["services"].items():
        if not isinstance(service, dict) or not service.get("image"):
            raise ValueError(f"service {name} must define image")
        cid = remote.run(
            image=str(service["image"]),
            command=_cmd_to_list(service.get("command")),
            env=_env_to_list(service.get("environment")),
        )
        started.append({"service": str(name), "container_id": cid, "image": str(service["image"])})
    return started
