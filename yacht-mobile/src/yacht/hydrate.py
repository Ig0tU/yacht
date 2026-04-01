from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HydrationReport:
    score: float
    mode: str
    reasons: list[str]
    suggested_fixes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "mode": self.mode,
            "reasons": self.reasons,
            "suggested_fixes": self.suggested_fixes,
        }


def build_hydration_report(config: dict[str, Any], manifest: dict[str, Any]) -> HydrationReport:
    score = 1.0
    reasons: list[str] = []
    fixes: list[str] = []

    os_name = str(config.get("os", "linux"))
    arch = str(config.get("architecture", ""))
    cfg = config.get("config", {}) if isinstance(config.get("config"), dict) else {}

    if os_name != "linux":
        score -= 1.0
        reasons.append(f"unsupported os={os_name} for mobile local runtime")
        fixes.append("publish linux image variant")

    if arch and arch != "arm64":
        score -= 0.35
        reasons.append(f"image architecture is {arch}, not arm64")
        fixes.append("publish multi-arch image including linux/arm64")

    user = str(cfg.get("User", "")).strip()
    if user in ("", "0", "root"):
        score -= 0.1
        reasons.append("container runs as root by default")
        fixes.append("set non-root user in Dockerfile")

    entry = " ".join((cfg.get("Entrypoint") or []) + (cfg.get("Cmd") or []))
    risky_tokens = ("dockerd", "containerd", "iptables", "systemd", "kubelet")
    if any(t in entry for t in risky_tokens):
        score -= 0.45
        reasons.append("entrypoint appears to require privileged/kernel-level features")
        fixes.append("split privileged operations into remote sidecar")

    ports = cfg.get("ExposedPorts") or {}
    if isinstance(ports, dict):
        for p in ports:
            try:
                num = int(str(p).split("/", 1)[0])
                if num < 1024:
                    score -= 0.05
                    reasons.append(f"exposes privileged port {num}")
                    fixes.append("use unprivileged port mapping (>1024)")
                    break
            except ValueError:
                continue

    if manifest.get("layers") and len(manifest["layers"]) > 20:
        score -= 0.1
        reasons.append("large layer count may degrade mobile startup")
        fixes.append("squash or reduce layers")

    score = max(0.0, min(1.0, score))
    if score >= 0.75:
        mode = "local"
    elif score >= 0.45:
        mode = "local-hydrated"
    else:
        mode = "remote"

    if not reasons:
        reasons.append("no major compatibility blockers detected")
    if not fixes:
        fixes.append("none")

    return HydrationReport(score=score, mode=mode, reasons=reasons, suggested_fixes=fixes)
