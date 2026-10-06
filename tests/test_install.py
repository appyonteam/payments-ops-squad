import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "install", "install.sh")


@unittest.skipIf(shutil.which("bash") is None, "bash not available")
class InstallShTest(unittest.TestCase):
    """Runs install.sh against a temporary HOME only, never the real one."""

    def run_install(self, home, *args, cwd=None):
        env = dict(os.environ, HOME=home)
        return subprocess.run(["bash", SCRIPT, *args], env=env, cwd=cwd or home,
                              capture_output=True, text=True)

    def test_user_scope_counts_and_conflicts(self):
        home = tempfile.mkdtemp()
        r = self.run_install(home)
        self.assertEqual(r.returncode, 0, r.stderr)
        dest = os.path.join(home, ".claude")
        agents = [f for f in os.listdir(os.path.join(dest, "agents")) if f.endswith(".md")]
        skills = [d for d in os.listdir(os.path.join(dest, "skills"))
                  if os.path.isfile(os.path.join(dest, "skills", d, "SKILL.md"))]
        commands = [f for f in os.listdir(os.path.join(dest, "commands")) if f.endswith(".md")]
        self.assertEqual(len(agents), 21)
        self.assertEqual(len(skills), 35 + 8)
        self.assertEqual(len(commands), 6)
        self.assertNotIn("stripe", os.listdir(os.path.join(dest, "skills")))
        pkg = os.path.join(dest, "payments-ops-squad")
        self.assertTrue(os.path.isfile(os.path.join(pkg, "tools", "fetch_doc.py")))
        self.assertTrue(os.path.isfile(os.path.join(pkg, "knowledge", ".payments-ops-cache")))

        again = self.run_install(home)
        self.assertEqual(again.returncode, 2)
        self.assertIn("already exist", again.stderr)

        forced = self.run_install(home, "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertIn("overwritten (--force)", forced.stdout)

    def test_project_scope(self):
        home, project = tempfile.mkdtemp(), tempfile.mkdtemp()
        r = self.run_install(home, "--scope", "project", cwd=project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(os.path.join(project, ".claude", "agents")))
        self.assertFalse(os.path.exists(os.path.join(home, ".claude")))

    def test_bad_scope(self):
        r = self.run_install(tempfile.mkdtemp(), "--scope", "everywhere")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
