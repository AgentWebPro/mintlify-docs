from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from scripts.build_source_inventory import source_api_paths, source_ui_labels
from scripts.claim_sweep import (
    Claim,
    RetiredClaim,
    added_mdx_claims,
    digest,
    load_hashes,
    load_retired_claims,
    validate_claims,
)


class ClaimSweepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api_hashes = {digest("/api/emma/books")}
        self.ui_hashes = {digest("Settings"), digest("API Keys")}
        self.retired = [RetiredClaim(2, digest("retired guarantee"))]

    def test_rejects_documented_api_path_missing_from_source(self) -> None:
        errors = validate_claims(
            [Claim("guide.mdx", 8, "POST /api/emma/not-a-real-route")],
            self.api_hashes,
            self.ui_hashes,
            self.retired,
        )

        self.assertTrue(any("/api/emma/not-a-real-route" in error for error in errors))

    def test_rejects_and_names_bold_ui_label_missing_from_source(self) -> None:
        errors = validate_claims(
            [Claim("guide.mdx", 12, "Click **Imaginary control** to continue.")],
            self.api_hashes,
            self.ui_hashes,
            self.retired,
        )

        self.assertTrue(any("Imaginary control" in error for error in errors))

    def test_rejects_reintroduced_retired_claim(self) -> None:
        errors = validate_claims(
            [Claim("guide.mdx", 19, "This is a retired guarantee from the old page.")],
            self.api_hashes,
            self.ui_hashes,
            self.retired,
        )

        self.assertTrue(any("retired claim" in error for error in errors))

    def test_accepts_source_backed_claims(self) -> None:
        errors = validate_claims(
            [
                Claim("guide.mdx", 4, "GET /api/emma/books"),
                Claim("guide.mdx", 5, "Click **Settings → API Keys**."),
            ],
            self.api_hashes,
            self.ui_hashes,
            self.retired,
        )

        self.assertEqual([], errors)

    def test_builds_registered_paths_from_mount_and_router_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            routes = root / "backend/src/routes"
            routes.mkdir(parents=True)
            (root / "backend/src/app.ts").write_text(
                'import booksRoutes from "./routes/books";\n'
                'app.use("/api/books", authenticateToken, booksRoutes);\n',
                encoding="utf-8",
            )
            (routes / "books.ts").write_text(
                'router.get("/:bookId", handler);\nrouter.post("/", handler);\n',
                encoding="utf-8",
            )

            self.assertEqual(
                {"/api/books", "/api/books/:bookId"},
                source_api_paths(root),
            )

    def test_builds_ui_labels_from_literals_and_jsx_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src/components/Settings.tsx"
            source.parent.mkdir(parents=True)
            source.write_text(
                'const label = "API Keys";\nexport const View = () => <button>Save changes</button>;\n',
                encoding="utf-8",
            )

            labels = source_ui_labels(root)

            self.assertIn("API Keys", labels)
            self.assertIn("Save changes", labels)

    def test_reads_only_mdx_lines_added_since_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "claim-sweep@example.com"], cwd=root, check=True
            )
            subprocess.run(["git", "config", "user.name", "Claim Sweep"], cwd=root, check=True)
            guide = root / "guide.mdx"
            guide.write_text("# Existing\n", encoding="utf-8")
            subprocess.run(["git", "add", "guide.mdx"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            guide.write_text("# Existing\nClick **Imaginary control**.\n", encoding="utf-8")
            subprocess.run(["git", "add", "guide.mdx"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "change"], cwd=root, check=True)

            self.assertEqual(
                [Claim("guide.mdx", 2, "Click **Imaginary control**.")],
                added_mdx_claims(root, base),
            )

    def test_rejects_inconsistent_source_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "api_path_count": 2,
                        "ui_label_count": 0,
                        "api_path_hashes": [digest("/api/one")],
                        "ui_label_hashes": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "inconsistent api_path_hashes"):
                load_hashes(path)

    def test_rejects_invalid_retired_claim_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "retired.sha256"
            path.write_text("0 not-a-digest\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "expected '<word-count> <sha256>'"):
                load_retired_claims(path)


if __name__ == "__main__":
    unittest.main()
