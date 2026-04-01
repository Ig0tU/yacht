from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import settings


@dataclass
class RemoteConfig:
    host: str
    token: str
    api_version: str

    @property
    def base_url(self) -> str:
        return f"{self.host.rstrip('/')}/{self.api_version}"


def get_remote() -> RemoteConfig:
    if not settings.remote_docker_host:
        raise RemoteDockerError("REMOTE_DOCKER_HOST is not configured", status_code=400)
    return RemoteConfig(
        host=settings.remote_docker_host,
        token=settings.remote_docker_token,
        api_version=settings.remote_docker_api_version,
    )


class RemoteDockerError(RuntimeError):
    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class RemoteDocker:
    def __init__(self, cfg: RemoteConfig):
        self.cfg = cfg

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | str:
        url = f"{self.cfg.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        headers = {"Content-Type": "application/json"}
        if self.cfg.token:
            headers["Authorization"] = f"Bearer {self.cfg.token}"
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=settings.remote_docker_timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return ""
                ct = (resp.headers.get("Content-Type") or "").lower()
                if "application/json" in ct or raw.lstrip().startswith(("{", "[")):
                    return json.loads(raw)
                return raw
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8") if exc.fp else ""
            message = detail or f"remote docker error: {exc.code}"
            raise RemoteDockerError(message, status_code=502) from exc
        except urllib.error.URLError as exc:
            raise RemoteDockerError(f"remote docker unreachable: {exc.reason}", status_code=502) from exc
        except TimeoutError as exc:
            raise RemoteDockerError("remote docker timed out", status_code=504) from exc

    def ping(self) -> str:
        out = self._request("GET", "/_ping")
        return out if isinstance(out, str) else json.dumps(out)

    def pull(self, image: str) -> None:
        self._request("POST", "/images/create", query={"fromImage": image})

    def run(self, image: str, command: list[str] | None, env: list[str] | None = None) -> str:
        self.pull(image)
        create_body: dict[str, Any] = {"Image": image}
        if command:
            create_body["Cmd"] = command
        if env:
            create_body["Env"] = env
        created = self._request("POST", "/containers/create", body=create_body)
        if not isinstance(created, dict) or "Id" not in created:
            raise RemoteDockerError("container create failed")
        cid = str(created["Id"])
        self._request("POST", f"/containers/{cid}/start")
        return cid
