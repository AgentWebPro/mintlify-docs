#!/usr/bin/env python3
"""Build opaque docs-claim inventories from AgentWeb source checkouts."""

import argparse
import json
from pathlib import Path
import re
import subprocess

try:
    from scripts.claim_sweep import digest, normalize_api_path, normalize_ui_label
except ModuleNotFoundError:  # Direct `python3 scripts/build_source_inventory.py` invocation.
    from claim_sweep import digest, normalize_api_path, normalize_ui_label


IMPORT_RE = re.compile(r'import\s+(\w+)\s+from\s+["\'](\./routes/[^"\']+)["\']')
MOUNT_RE = re.compile(r'app\.use\(\s*["\']([^"\']+)["\']\s*,(.+)\);')
ROUTE_RE = re.compile(
    r'(?:router|app)\.(?:get|post|put|patch|delete|options|head|use|route)\(\s*(["\'])(/[^"\']*)\1',
    re.DOTALL,
)
JSX_TEXT_RE = re.compile(r">([^<{]+)<")
UI_VALUE_KEYS = (
    "aria-label",
    "title",
    "placeholder",
    "label",
    "buttonText",
    "ctaText",
    "tabLabel",
    "displayName",
)
UI_VALUE_PATTERNS = tuple(
    re.compile(
        rf"\b(?:{'|'.join(UI_VALUE_KEYS)})\s*(?:=|:)\s*(?:\{{\s*)?{quote}"
        rf"((?:\\.|[^{quote}\\\n])*){quote}"
    )
    for quote in ('"', "'", "`")
)


def revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def source_api_paths(agentweb_root: Path) -> set[str]:
    app_path = agentweb_root / "backend/src/app.ts"
    app_source = app_path.read_text(encoding="utf-8")
    imports = {name: path for name, path in IMPORT_RE.findall(app_source)}
    paths: set[str] = set()

    for match in ROUTE_RE.finditer(app_source):
        path = normalize_api_path(match.group(2))
        if path.startswith("/api/"):
            paths.add(path)

    for match in MOUNT_RE.finditer(app_source):
        base = normalize_api_path(match.group(1))
        if not base.startswith("/api"):
            continue
        paths.add(base)
        identifiers = re.findall(r"\b[A-Za-z_$][\w$]*\b", match.group(2))
        router_name = next((name for name in reversed(identifiers) if name in imports), None)
        if not router_name:
            continue
        route_path = (app_path.parent / imports[router_name]).with_suffix(".ts")
        if not route_path.exists():
            continue
        route_source = route_path.read_text(encoding="utf-8")
        for route_match in ROUTE_RE.finditer(route_source):
            child = route_match.group(2)
            if "${" in child:
                continue
            paths.add(normalize_api_path(f"{base}/{child.lstrip('/')}"))
    return paths


def _decoded_literal(value: str) -> str:
    return (
        value.replace(r"\n", " ")
        .replace(r"\t", " ")
        .replace(r'\"', '"')
        .replace(r"\'", "'")
        .replace(r"\`", "`")
        .replace("\\\\", "\\")
    )


def source_ui_labels(portal_root: Path) -> set[str]:
    labels: set[str] = set()
    for path in sorted((portal_root / "src").rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        relative = path.relative_to(portal_root / "src")
        if (
            any(part in {"__tests__", "test", "tests", "fixtures", "__mocks__"} for part in relative.parts)
            or ".test." in path.name
            or ".spec." in path.name
        ):
            continue
        source = path.read_text(encoding="utf-8")
        candidates = [
            _decoded_literal(match.group(1))
            for pattern in UI_VALUE_PATTERNS
            for match in pattern.finditer(source)
        ]
        candidates.extend(match.group(1) for match in JSX_TEXT_RE.finditer(source))
        for candidate in candidates:
            if "${" in candidate or "\n" in candidate:
                continue
            label = normalize_ui_label(candidate)
            if 1 <= len(label) <= 160:
                labels.add(label)
    return labels


def build_inventory(agentweb_root: Path, portal_root: Path) -> dict[str, object]:
    api_paths = source_api_paths(agentweb_root)
    ui_labels = source_ui_labels(portal_root)
    return {
        "schema_version": 1,
        "agentweb_revision": revision(agentweb_root),
        "portal_revision": revision(portal_root),
        "api_path_count": len(api_paths),
        "ui_label_count": len(ui_labels),
        "api_path_hashes": sorted(digest(path) for path in api_paths),
        "ui_label_hashes": sorted(digest(label) for label in ui_labels),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentweb-root", type=Path, required=True)
    parser.add_argument("--portal-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory = build_inventory(args.agentweb_root.resolve(), args.portal_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {inventory['api_path_count']} API paths and "
        f"{inventory['ui_label_count']} UI labels to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
