import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "coordinator_lock.py"


class CoordinatorLockTests(unittest.TestCase):
    def run_cli(self, lock_path, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--lock-path", str(lock_path), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_acquire_creates_lock_with_five_required_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "state" / "coordinator.lock"
            result = self.run_cli(lock_path, "acquire")
            self.assertEqual(result.returncode, 0, result.stderr)
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(lock),
                {"pid", "hostname", "started_at", "ttl_seconds", "holder"},
            )
            self.assertIsInstance(lock["pid"], int)
            self.assertGreater(lock["pid"], 0)
            self.assertEqual(lock["ttl_seconds"], 3600)
            self.assertTrue(lock["hostname"])
            self.assertTrue(lock["holder"])

    def test_double_acquire_exits_two_and_names_existing_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "coordinator.lock"
            first = self.run_cli(lock_path, "acquire")
            self.assertEqual(first.returncode, 0, first.stderr)
            existing_pid = json.loads(lock_path.read_text(encoding="utf-8"))["pid"]
            second = self.run_cli(lock_path, "acquire")
            self.assertEqual(second.returncode, 2)
            self.assertIn(str(existing_pid), second.stderr)

    def test_acquire_release_acquire_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "coordinator.lock"
            first = self.run_cli(lock_path, "acquire")
            release = self.run_cli(lock_path, "release")
            second = self.run_cli(lock_path, "acquire")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(release.returncode, 0, release.stderr)
            self.assertFalse("no lock" in release.stdout)
            self.assertEqual(second.returncode, 0, second.stderr)

    def test_expired_lock_is_taken_over_with_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "coordinator.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat().replace("+00:00", "Z")
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": 424242,
                        "hostname": "old-host",
                        "started_at": old,
                        "ttl_seconds": 60,
                        "holder": "previous",
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(lock_path, "acquire", "--ttl", "90")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARNING", result.stderr)
            self.assertEqual(json.loads(lock_path.read_text(encoding="utf-8"))["ttl_seconds"], 90)

    def test_status_without_lock_prints_no_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "missing.lock"
            result = self.run_cli(lock_path, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "no lock")

    def test_release_without_lock_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(Path(directory) / "missing.lock", "release")
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
