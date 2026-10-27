import subprocess
import unittest
from pathlib import Path


class AtomicGitClaimIntegrationTests(unittest.TestCase):
    def test_bash_integration_suite(self):
        script = Path(__file__).with_name("test_claim_task.sh")
        result = subprocess.run(["bash", str(script)], text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("Atomic Git claim integration tests passed.", result.stdout)


class RemoteArgumentInjectionTests(unittest.TestCase):
    """A remote that starts with '-' would be parsed by git as an option such as --upload-pack."""

    def test_option_shaped_remote_is_rejected_before_git_runs(self):
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        for script, extra in (
            ("claim_task.py", ["--task-id", "T1"]),
            ("release_claim.py", ["--task-id", "T1"]),
            ("list_claims.py", []),
        ):
            for remote in ("--upload-pack=touch pwned", "--receive-pack=touch pwned", "-x"):
                with self.subTest(script=script, remote=remote):
                    result = subprocess.run(
                        ["python3", str(scripts / script), *extra, f"--remote={remote}"],
                        text=True,
                        capture_output=True,
                        timeout=30,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("not an option", result.stderr)


if __name__ == "__main__":
    unittest.main()
