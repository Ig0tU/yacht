from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import blob_path
from .image_ref import ImageRef

ACCEPT_MANIFEST = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


@dataclass
class PulledImage:
    manifest: dict[str, Any]
    config: dict[str, Any]
    config_digest: str
    layer_digests: list[str]
    platform: dict[str, str]


class RegistryClient:
    def __init__(self, ref: ImageRef):
        self.ref = ref
        self.token: str | None = None

    def _url(self, path: str) -> str:
        return f"https://{self.ref.registry}{path}"

    def _request(
        self,
        path: str,
        *,
        accept: str | None = None,
        raw: bool = False,
    ) -> tuple[Any, dict[str, str]]:
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(self._url(path), headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                h = {k.lower(): v for k, v in resp.headers.items()}
                return (body if raw else json.loads(body.decode("utf-8"))), h
        except urllib.error.HTTPError as e:
            if e.code != 401:
                raise
            auth = e.headers.get("www-authenticate", "")
            if not auth.lower().startswith("bearer "):
                raise
            self.token = self._fetch_token(auth)
            return self._request(path, accept=accept, raw=raw)

    def _fetch_token(self, challenge: str) -> str:
        fields: dict[str, str] = {}
        for part in challenge[len("Bearer ") :].split(","):
            k, v = part.strip().split("=", 1)
            fields[k] = v.strip('"')
        query = urllib.parse.urlencode(
            {
                "service": fields.get("service", ""),
                "scope": fields.get("scope", f"repository:{self.ref.repository}:pull"),
            }
        )
        token_url = f"{fields['realm']}?{query}"
        with urllib.request.urlopen(token_url) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("token") or body["access_token"]

    def pull(self, *, platform: str = "linux/arm64", with_layers: bool = False) -> PulledImage:
        base_path = f"/v2/{self.ref.repository}/manifests/{self.ref.reference}"
        manifest, _ = self._request(base_path, accept=ACCEPT_MANIFEST)
        media_type = manifest.get("mediaType", "")

        if media_type in (
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
        ):
            manifest = self._select_platform_manifest(manifest, platform)

        config_desc = manifest["config"]
        config_digest = config_desc["digest"]
        config = self.fetch_blob_json(config_digest)
        layers = [x["digest"] for x in manifest.get("layers", [])]
        if with_layers:
            for d in layers:
                self.fetch_blob_to_cache(d)

        return PulledImage(
            manifest=manifest,
            config=config,
            config_digest=config_digest,
            layer_digests=layers,
            platform={
                "os": str(config.get("os", "linux")),
                "architecture": str(config.get("architecture", "")),
            },
        )

    def _select_platform_manifest(self, index_doc: dict[str, Any], platform: str) -> dict[str, Any]:
        want_os, want_arch = platform.split("/", 1)
        manifests = index_doc.get("manifests", [])
        selected = None
        for m in manifests:
            p = m.get("platform", {})
            if p.get("os") == want_os and p.get("architecture") == want_arch:
                selected = m
                break
        if selected is None and manifests:
            selected = manifests[0]
        if selected is None:
            raise RuntimeError("image index has no manifests")

        child, _ = self._request(
            f"/v2/{self.ref.repository}/manifests/{selected['digest']}",
            accept=selected.get("mediaType", ACCEPT_MANIFEST),
        )
        return child

    def fetch_blob_to_cache(self, digest: str) -> Path:
        out = blob_path(digest)
        if out.exists():
            return out
        out.parent.mkdir(parents=True, exist_ok=True)
        body = self._fetch_blob_bytes(digest)
        out.write_bytes(body)
        return out

    def fetch_blob_json(self, digest: str) -> dict[str, Any]:
        p = self.fetch_blob_to_cache(digest)
        return json.loads(p.read_text(encoding="utf-8"))

    def _fetch_blob_bytes(self, digest: str) -> bytes:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        req = urllib.request.Request(
            self._url(f"/v2/{self.ref.repository}/blobs/{digest}"),
            headers=headers,
            method="GET",
        )
        try:
            with opener.open(req) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get("Location")
                if not location:
                    raise
                # Signed blob URLs typically reject registry Authorization headers.
                with urllib.request.urlopen(location) as resp2:
                    return resp2.read()
            if e.code == 401:
                auth = e.headers.get("www-authenticate", "")
                if auth.lower().startswith("bearer "):
                    self.token = self._fetch_token(auth)
                    return self._fetch_blob_bytes(digest)
            raise
