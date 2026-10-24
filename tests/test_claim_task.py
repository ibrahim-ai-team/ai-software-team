import subprocess
import unittest
from pathlib import Path


class AtomicGitClaimIntegrationTests(unittest.TestCase):
    def test_bash_integration_suite(self):
        script = Path(__file__).with_name("test_claim_task.sh")
        result = subprocess.run(["bash", str(script)], text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("Atomic Git claim integration tests passed.", result.stdout)


if __name__ == "__main__":
    unittest.main()
