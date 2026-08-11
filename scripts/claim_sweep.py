#!/usr/bin/env python3
"""Reject new documentation claims that contradict shipped product source."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


API_PATH_RE = re.compile(r"/api/[A-Za-z0-9_?&=./:{}-]+")
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
ACTION_RE = re.compile(
    r"\b(click|select|choose|open|go to|navigate to|toggle|turn on|turn off|press|set|"
    r"enter|enable|disable|check|uncheck|type|fill|upload|download|connect|disconnect|"
    r"save|delete|remove|add|create|pick|switch|expand|collapse|tap|find|search|"
    r"generate|send|submit)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?")
DIGEST_HEX_LENGTH = 32
DIGEST_RE = re.compile(rf"[0-9a-f]{{{DIGEST_HEX_LENGTH}}}")


@dataclass(frozen=True)
class Claim:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class RetiredClaim:
    word_count: int
    digest: str


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:DIGEST_HEX_LENGTH]


def normalize_api_path(value: str) -> str:
    path = value.rstrip(".,;:)")
    path = path.split("?", 1)[0]
    return path if path == "/api/" else path.rstrip("/")


def normalize_ui_label(value: str) -> str:
    value = value.replace(r"\_", "_")
    return " ".join(value.strip(" `.:").split())


def ui_labels(text: str) -> list[str]:
    if not ACTION_RE.search(text):
        return []
    labels: list[str] = []
    for match in BOLD_RE.finditer(text):
        labels.extend(
            label
            for part in match.group(1).split("→")
            if (label := normalize_ui_label(part))
        )
    return labels


def retired_match(text: str, retired_claims: list[RetiredClaim]) -> bool:
    words = [word.lower().replace("’", "'") for word in WORD_RE.findall(text)]
    for retired in retired_claims:
        for start in range(len(words) - retired.word_count + 1):
            candidate = " ".join(words[start : start + retired.word_count])
            if digest(candidate) == retired.digest:
                return True
    return False


def validate_claims(
    claims: list[Claim],
    api_hashes: set[str],
    ui_hashes: set[str],
    retired_claims: list[RetiredClaim],
) -> list[str]:
    """Return source-backed claim violations."""
    errors: list[str] = []
    for claim in claims:
        location = f"{claim.path}:{claim.line}"
        for match in API_PATH_RE.finditer(claim.text):
            path = normalize_api_path(match.group(0))
            if digest(path) not in api_hashes:
                errors.append(f"{location}: undocumented source route: {path}")
        for label in ui_labels(claim.text):
            if digest(label) not in ui_hashes:
                errors.append(f'{location}: UI label absent from portal source: "{label}"')
        if retired_match(claim.text, retired_claims):
            errors.append(f"{location}: retired claim reintroduced")
    return errors


def load_hashes(manifest_path: Path) -> tuple[set[str], set[str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError(f"{manifest_path}: unsupported schema_version")

    def checked_hashes(key: str, count_key: str) -> set[str]:
        values = manifest.get(key)
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not DIGEST_RE.fullmatch(value) for value in values
        ):
            raise ValueError(f"{manifest_path}: invalid {key}")
        if values != sorted(set(values)) or manifest.get(count_key) != len(values):
            raise ValueError(f"{manifest_path}: inconsistent {key}")
        return set(values)

    return checked_hashes("api_path_hashes", "api_path_count"), checked_hashes(
        "ui_label_hashes", "ui_label_count"
    )


def load_retired_claims(path: Path) -> list[RetiredClaim]:
    claims: list[RetiredClaim] = []
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            count, claim_digest = line.split()
            word_count = int(count)
            if word_count < 1 or not DIGEST_RE.fullmatch(claim_digest):
                raise ValueError
            claims.append(RetiredClaim(word_count, claim_digest))
        except ValueError as error:
            raise ValueError(f"{path}:{number}: expected '<word-count> <sha256>'") from error
    return claims


def all_mdx_claims(root: Path) -> list[Claim]:
    claims: list[Claim] = []
    for path in sorted(root.rglob("*.mdx")):
        relative = path.relative_to(root).as_posix()
        claims.extend(
            Claim(relative, line_number, text)
            for line_number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        )
    return claims


def added_mdx_claims(root: Path, base_ref: str) -> list[Claim]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", "--diff-filter=ACMR", f"{base_ref}...HEAD", "--", "*.mdx"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    claims: list[Claim] = []
    current_path = ""
    next_line = 0
    for raw_line in result.stdout.splitlines():
        if raw_line.startswith("+++ b/"):
            current_path = raw_line[6:]
            continue
        if raw_line.startswith("@@"):
            match = re.search(r"\+(\d+)", raw_line)
            next_line = int(match.group(1)) if match else 0
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            claims.append(Claim(current_path, next_line, raw_line[1:]))
            next_line += 1
    return claims


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=Path("guard/source-inventory.json"))
    parser.add_argument("--denylist", type=Path, default=Path("guard/retired-claims.sha256"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="scan every MDX line")
    mode.add_argument("--base-ref", help="scan MDX lines added since this git ref")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    denylist_path = args.denylist if args.denylist.is_absolute() else root / args.denylist
    api_hashes, ui_hashes = load_hashes(manifest_path)
    retired_claims = load_retired_claims(denylist_path)
    claims = all_mdx_claims(root) if args.all else added_mdx_claims(root, args.base_ref)
    errors = validate_claims(claims, api_hashes, ui_hashes, retired_claims)
    if errors:
        print("Documentation claim sweep failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Documentation claim sweep passed: {len(claims)} line(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
