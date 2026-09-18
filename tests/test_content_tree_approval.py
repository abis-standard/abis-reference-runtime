"""M-229F.1 content-tree approval architecture tests — synthetic only."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DISCLOSURE = REPO_ROOT / "scripts" / "disclosure"


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def compute_hash(repo: Path, source: str = "index") -> str:
    hash_script = repo / "scripts" / "disclosure" / "compute-content-tree-hash.py"
    proc = subprocess.run(
        ["python3", str(hash_script), str(repo), "--source", source],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def write_approval(repo: Path, content_hash: str, **overrides: object) -> Path:
    approval_dir = repo / ".abis"
    approval_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    payload = {
        "schema_version": "1.1",
        "approval_id": "00000000-0000-4000-8000-000000000001",
        "binding_type": "content_tree",
        "approved_content_hash": content_hash,
        "status": "PASS",
        "controls_passed": [
            "M229D-003",
            "M229D-005",
            "M229D-009",
            "M229D-010",
        ],
        "issued_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "review_context_hash": content_hash,
    }
    payload.update(overrides)
    path = approval_dir / "disclosure-approval.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def verify(repo: Path) -> subprocess.CompletedProcess[str]:
    verify_script = repo / "scripts" / "disclosure" / "verify-private-approval.sh"
    return subprocess.run(
        ["bash", str(verify_script)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


class ContentTreeApprovalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        run_git(self.repo, "init")
        run_git(self.repo, "config", "user.email", "test@example.com")
        run_git(self.repo, "config", "user.name", "Test User")
        (self.repo / "README.md").write_text("# demo\n", encoding="utf-8")
        disclosure = self.repo / "scripts" / "disclosure"
        disclosure.mkdir(parents=True)
        for name in (
            "compute-content-tree-hash.py",
            "verify-private-approval.sh",
        ):
            (disclosure / name).write_text(
                (CANONICAL_DISCLOSURE / name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-m", "init")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_t14_generate_and_verify_pass(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "add approval")
        result = verify(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("M229D-PRIVATE-APPROVAL PASS", result.stdout)

    def test_t15_approval_artifact_does_not_change_content_hash(self) -> None:
        before = compute_hash(self.repo, "index")
        write_approval(self.repo, before)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        after = compute_hash(self.repo, "index")
        self.assertEqual(before, after)

    def test_self_reference_hash_stable(self) -> None:
        hash_before = compute_hash(self.repo, "index")
        write_approval(self.repo, hash_before)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        hash_after = compute_hash(self.repo, "index")
        self.assertEqual(hash_before, hash_after)

    def test_t16_source_change_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "approval")
        (self.repo / "README.md").write_text("# changed\n", encoding="utf-8")
        run_git(self.repo, "add", "README.md")
        run_git(self.repo, "commit", "-m", "change source")
        result = verify(self.repo)
        self.assertNotEqual(result.returncode, 0)

    def test_t17_documentation_change_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "approval")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "guide.md").write_text("docs\n", encoding="utf-8")
        run_git(self.repo, "add", "docs/guide.md")
        run_git(self.repo, "commit", "-m", "docs")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t18_workflow_change_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "approval")
        workflow = self.repo / ".github" / "workflows"
        workflow.mkdir(parents=True)
        (workflow / "disclosure-gate.yml").write_text("name: gate\n", encoding="utf-8")
        run_git(self.repo, "add", ".github/workflows/disclosure-gate.yml")
        run_git(self.repo, "commit", "-m", "workflow")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t19_allowlist_change_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "approval")
        (self.repo / "public-allowlist.yml").write_text("allowed_paths: []\n", encoding="utf-8")
        run_git(self.repo, "add", "public-allowlist.yml")
        run_git(self.repo, "commit", "-m", "allowlist")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t20_metadata_only_change_same_content_hash(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        approval_path = write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "approval")
        data = json.loads(approval_path.read_text(encoding="utf-8"))
        data["approval_id"] = "00000000-0000-4000-8000-000000000099"
        approval_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "metadata")
        self.assertEqual(compute_hash(self.repo, "head"), content_hash)
        result = verify(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_t21_expired_approval_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        write_approval(self.repo, content_hash, expires_at=past)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "expired")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t22_schema_10_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        approval = self.repo / ".abis" / "disclosure-approval.json"
        approval.parent.mkdir(parents=True, exist_ok=True)
        approval.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "public_commit_sha": "deadbeef",
                    "status": "PASS",
                    "controls_passed": [
                        "M229D-003",
                        "M229D-005",
                        "M229D-009",
                        "M229D-010",
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "legacy")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t23_missing_approval_blocks(self) -> None:
        approval = self.repo / ".abis" / "disclosure-approval.json"
        if approval.exists():
            approval.unlink()
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t24_malformed_approval_blocks(self) -> None:
        approval = self.repo / ".abis" / "disclosure-approval.json"
        approval.parent.mkdir(parents=True, exist_ok=True)
        approval.write_text("{not-json", encoding="utf-8")
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "bad")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t25_missing_control_blocks(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(
            self.repo,
            content_hash,
            controls_passed=["M229D-003"],
        )
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "controls")
        self.assertNotEqual(verify(self.repo).returncode, 0)

    def test_t27_content_unchanged_across_final_commit(self) -> None:
        content_hash = compute_hash(self.repo, "index")
        write_approval(self.repo, content_hash)
        run_git(self.repo, "add", ".abis/disclosure-approval.json")
        run_git(self.repo, "commit", "-m", "final")
        self.assertEqual(compute_hash(self.repo, "head"), content_hash)
        self.assertEqual(verify(self.repo).returncode, 0)

    def test_security_hash_changes_after_public_source_change(self) -> None:
        approved = compute_hash(self.repo, "index")
        (self.repo / "src.py").write_text("print('x')\n", encoding="utf-8")
        run_git(self.repo, "add", "src.py")
        changed = compute_hash(self.repo, "index")
        self.assertNotEqual(approved, changed)


if __name__ == "__main__":
    unittest.main()
