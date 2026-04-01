from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import yacht_home


@dataclass
class RemoteProfile:
    host: str
    token: str | None = None
    api_version: str = "v1.43"

    def base_url(self) -> str:
        return f"{self.host.rstrip('/')}/{self.api_version}"


def _profile_path() -> Path:
    return yacht_home() / "remote.json"


def save_profile(profile: RemoteProfile) -> None:
    p = _profile_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {"host": profile.host, "token": profile.token, "api_version": profile.api_version},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_profile() -> RemoteProfile:
    p = _profile_path()
    if not p.exists():
        raise FileNotFoundError("no remote profile configured; run `yacht remote connect`")
    data = json.loads(p.read_text(encoding="utf-8"))
    return RemoteProfile(
        host=str(data["host"]),
        token=data.get("token"),
        api_version=str(data.get("api_version", "v1.43")),
    )


class RemoteDocker:
    def __init__(self, profile: RemoteProfile):
        self.profile = profile

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | str:
        url = f"{self.profile.base_url()}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        data = None
        headers = {"Content-Type": "application/json"}
        if self.profile.token:
            headers["Authorization"] = f"Bearer {self.profile.token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
            if not payload.strip():
                return ""
            ct = (resp.headers.get("Content-Type") or "").lower()
            if "application/json" in ct or payload.lstrip().startswith(("{", "[")):
                return json.loads(payload)
            return payload

    def ping(self) -> str:
        out = self._request("GET", "/_ping")
        if isinstance(out, str):
            return out.strip()
        return str(out)

    def ensure_image(self, image: str) -> None:
        self._request("POST", "/images/create", query={"fromImage": image})

    def create_container(
        self,
        *,
        image: str,
        command: list[str] | None,
        env: list[str] | None = None,
        name: str | None = None,
    ) -> str:
        body: dict[str, Any] = {"Image": image}
        if command:
            body["Cmd"] = command
        if env:
            body["Env"] = env
        path = "/containers/create"
        if name:
            path += f"?{urllib.parse.urlencode({'name': name})}"
        out = self._request("POST", path, body=body)
        if not isinstance(out, dict) or "Id" not in out:
            raise RuntimeError(f"unexpected create response: {out}")
        return str(out["Id"])

    def start_container(self, container_id: str) -> None:
        self._request("POST", f"/containers/{container_id}/start")

    def logs(self, container_id: str, tail: int = 100) -> str:
        out = self._request(
            "GET",
            f"/containers/{container_id}/logs",
            query={"stdout": "1", "stderr": "1", "tail": str(tail)},
        )
        return out if isinstance(out, str) else json.dumps(out)
