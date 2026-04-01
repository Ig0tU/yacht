from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__
from .cache import ensure_dirs, image_dir, image_key, read_json, write_json
from .compose_support import compose_up
from .hydrate import build_hydration_report
from .image_ref import parse_image_ref
from .remote_docker import RemoteDocker, RemoteProfile, load_profile, save_profile
from .registry import RegistryClient
from .runner import materialize_rootfs, run_local


def cmd_pull(args: argparse.Namespace) -> int:
    ref = parse_image_ref(args.image)
    client = RegistryClient(ref)
    pulled = client.pull(platform=args.platform, with_layers=args.layers)
    out = image_dir(ref)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "ref.json", {"canonical": ref.canonical})
    write_json(out / "manifest.json", pulled.manifest)
    write_json(out / "config.json", pulled.config)
    write_json(
        out / "meta.json",
        {
            "config_digest": pulled.config_digest,
            "layer_digests": pulled.layer_digests,
            "platform": pulled.platform,
        },
    )
    print(f"pulled {ref.canonical}")
    print(f"cached at {out}")
    print(f"layers cached: {len(pulled.layer_digests) if args.layers else 0}")
    return 0


def _load_local_image(image: str) -> tuple[Path, dict, dict, dict]:
    ref = parse_image_ref(image)
    d = image_dir(ref)
    if not d.exists():
        raise FileNotFoundError("image not found in cache; run `yacht pull` first")
    return d, read_json(d / "manifest.json"), read_json(d / "config.json"), read_json(d / "meta.json")


def cmd_inspect(args: argparse.Namespace) -> int:
    _, manifest, config, meta = _load_local_image(args.image)
    summary = {
        "os": config.get("os"),
        "architecture": config.get("architecture"),
        "entrypoint": (config.get("config") or {}).get("Entrypoint"),
        "cmd": (config.get("config") or {}).get("Cmd"),
        "user": (config.get("config") or {}).get("User"),
        "exposed_ports": list(((config.get("config") or {}).get("ExposedPorts") or {}).keys()),
        "layers": len(manifest.get("layers", [])),
        "config_digest": meta.get("config_digest"),
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_hydrate(args: argparse.Namespace) -> int:
    d, manifest, config, _ = _load_local_image(args.image)
    report = build_hydration_report(config, manifest)
    write_json(d / "hydration.json", report.to_dict())
    print(json.dumps(report.to_dict(), indent=2))
    return 0


def _entry_argv(config: dict, override: list[str]) -> list[str]:
    if override:
        return override
    cfg = config.get("config", {}) if isinstance(config.get("config"), dict) else {}
    entry = cfg.get("Entrypoint") or []
    cmd = cfg.get("Cmd") or []
    return [*entry, *cmd]


def cmd_run(args: argparse.Namespace) -> int:
    ref = parse_image_ref(args.image)
    local_cached = True
    try:
        d, manifest, config, meta = _load_local_image(args.image)
    except FileNotFoundError:
        local_cached = False
        manifest = {}
        config = {}
        meta = {}
        d = image_dir(ref)
    report = build_hydration_report(config, manifest) if local_cached else None
    if report:
        write_json(d / "hydration.json", report.to_dict())

    selected_mode = args.mode
    if selected_mode == "auto":
        selected_mode = "remote" if (report is None or report.mode == "remote") else "local"

    if selected_mode == "remote":
        profile = load_profile()
        remote = RemoteDocker(profile)
        remote.ensure_image(args.image)
        cid = remote.create_container(image=args.image, command=args.command or None)
        remote.start_container(cid)
        print(json.dumps({"mode": "remote", "container_id": cid, "image": args.image}, indent=2))
        if args.logs:
            print(remote.logs(cid, tail=args.tail))
        return 0

    if not shutil.which("proot"):
        print("local runtime unavailable: proot not found")
        print("falling back to remote recommendation")
        if report:
            print(json.dumps(report.to_dict(), indent=2))
        print("next step: connect a remote Docker host and route this run through it")
        return 0

    # Ensure layers are present for local execution.
    missing = []
    for digest in meta.get("layer_digests", []):
        p = Path.home() / ".yacht" / "blobs" / digest.split(":", 1)[0] / digest.split(":", 1)[1]
        if not p.exists():
            missing.append(digest)
    if missing:
        client = RegistryClient(ref)
        for digest in missing:
            client.fetch_blob_to_cache(digest)

    rootfs = materialize_rootfs(meta.get("layer_digests", []), image_key(ref))
    argv = _entry_argv(config, args.command)
    if not argv:
        argv = ["/bin/sh"]
    return run_local(rootfs, argv)


def cmd_remote_connect(args: argparse.Namespace) -> int:
    profile = RemoteProfile(host=args.host, token=args.token, api_version=args.api_version)
    client = RemoteDocker(profile)
    pong = client.ping()
    save_profile(profile)
    print(json.dumps({"status": "connected", "host": args.host, "ping": pong}, indent=2))
    return 0


def cmd_remote_status(args: argparse.Namespace) -> int:
    profile = load_profile()
    client = RemoteDocker(profile)
    pong = client.ping()
    print(
        json.dumps(
            {"host": profile.host, "api_version": profile.api_version, "connected": pong == "OK", "ping": pong},
            indent=2,
        )
    )
    return 0


def cmd_compose_up(args: argparse.Namespace) -> int:
    profile = load_profile()
    remote = RemoteDocker(profile)
    started = compose_up(remote, Path(args.file))
    print(json.dumps({"started": started, "count": len(started)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="yacht", description="Yacht mobile container shim (MVP)")
    p.add_argument("--version", action="version", version=f"yacht-mobile {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pull = sub.add_parser("pull", help="pull OCI/Docker image to local cache")
    pull.add_argument("image")
    pull.add_argument("--platform", default="linux/arm64")
    pull.add_argument("--layers", action="store_true", help="also cache layer blobs")
    pull.set_defaults(func=cmd_pull)

    inspect = sub.add_parser("inspect", help="show cached image metadata")
    inspect.add_argument("image")
    inspect.set_defaults(func=cmd_inspect)

    hydrate = sub.add_parser("hydrate", help="compute mobile compatibility profile")
    hydrate.add_argument("image")
    hydrate.set_defaults(func=cmd_hydrate)

    run = sub.add_parser("run", help="run cached image in local or remote mode")
    run.add_argument("image")
    run.add_argument("--mode", choices=["auto", "local", "remote"], default="auto")
    run.add_argument("--logs", action="store_true")
    run.add_argument("--tail", type=int, default=100)
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(func=cmd_run)

    remote = sub.add_parser("remote", help="manage remote Docker target")
    remote_sub = remote.add_subparsers(dest="remote_cmd", required=True)
    remote_connect = remote_sub.add_parser("connect", help="connect to remote Docker API host")
    remote_connect.add_argument("--host", required=True, help="e.g. https://docker.example.com")
    remote_connect.add_argument("--token", default=None, help="optional bearer token")
    remote_connect.add_argument("--api-version", default="v1.43")
    remote_connect.set_defaults(func=cmd_remote_connect)
    remote_status = remote_sub.add_parser("status", help="check remote connection")
    remote_status.set_defaults(func=cmd_remote_status)

    compose = sub.add_parser("compose", help="compose subset commands")
    compose_sub = compose.add_subparsers(dest="compose_cmd", required=True)
    compose_up_cmd = compose_sub.add_parser("up", help="start compose services remotely")
    compose_up_cmd.add_argument("-f", "--file", default="docker-compose.yml")
    compose_up_cmd.set_defaults(func=cmd_compose_up)

    return p


def main() -> None:
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(code)
