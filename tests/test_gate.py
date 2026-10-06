import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
import gate  # noqa: E402

TERM = "SECRETWORD"
# Sensitive-looking fixtures are assembled at runtime so this file itself passes the gate.
U = "_"
AT = "@"


def _tree(files):
    d = tempfile.mkdtemp()
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return d


def _rules(hits):
    return {h[2] for h in hits}


class TestContent(unittest.TestCase):
    def test_clean(self):
        d = _tree({"b.md": "nothing here\nversion 1.2.3 and localhost 127.0.0.1 and 0.0.0.0\n"})
        self.assertEqual(gate.scan(d, [TERM]), [])

    def test_denylist_case_insensitive_by_default(self):
        d = _tree({"a.md": "ok\nthe secretword appears\nand Secretword too\n"})
        self.assertEqual(gate.scan(d, [TERM]), [("a.md", 2, "denylist#1"), ("a.md", 3, "denylist#1")])
        d = _tree({"b.md": "ok\nthe SECRETWORD appears\n"})
        self.assertEqual(gate.scan(d, ["secretword"]), [("b.md", 2, "denylist#1")])
        self.assertEqual(gate.scan(d, [r"re:\bsecret\w+"]), [("b.md", 2, "denylist#1")])

    def test_denylist_case_sensitive_flag(self):
        d = _tree({"a.md": "the secretword appears\nthe SECRETWORD appears\n"})
        self.assertEqual(gate.scan(d, [TERM], case_sensitive=True), [("a.md", 2, "denylist#1")])
        deny = os.path.join(tempfile.mkdtemp(), "deny.txt")
        with open(deny, "w", encoding="utf-8") as f:
            f.write("secretword\n")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(["--denylist", deny, "--root", d]), 1)
            d2 = _tree({"a.md": "the SECRETWORD appears\n"})
            self.assertEqual(gate.main(["--denylist", deny, "--root", d2, "--case-sensitive"]), 0)

    def test_denylist_term(self):
        d = _tree({"a.md": "ok\nthe SECRETWORD appears\n"})
        self.assertEqual(gate.scan(d, ["x", TERM]), [("a.md", 2, "denylist#2")])

    def test_denylist_regex_entry(self):
        d = _tree({"a.md": "Anabel is fine\nask Ana about it\n"})
        self.assertEqual(gate.scan(d, [r"re:\bAna\b"]), [("a.md", 2, "denylist#1")])

    def test_stripe_ids(self):
        d = _tree({"a.md": "account acct" + U + "1ABCDEFGH12\npayment pi" + U + "3XYZabcdefgh\n"})
        hits = gate.scan(d, [])
        self.assertEqual([(h[1], h[2]) for h in hits], [(1, "stripe_id"), (2, "stripe_id")])

    def test_stripe_id_false_positives(self):
        d = _tree({"a.md": "status in_progress\nfield sub_total\nch_fallback route\npi_XXXX placeholder\n"})
        self.assertEqual(gate.scan(d, []), [])

    def test_secret_keys(self):
        for prefix in ("sk~live~", "rk~live~", "sk~test~", "rk~test~", "whsec~"):
            d = _tree({"a.md": "key " + prefix.replace("~", U) + "abc\n"})
            self.assertIn("secret_key", _rules(gate.scan(d, [])), prefix)

    def test_email_and_allowlist(self):
        d = _tree({"a.md": "mail someone" + AT + "corp.example.org\n"})
        self.assertEqual(_rules(gate.scan(d, [])), {"email"})
        d = _tree({"a.md": "you@example.com user@example.com payments-ops-squad@users.noreply.github.com\n"})
        self.assertEqual(gate.scan(d, []), [])

    def test_userinfo_url(self):
        d = _tree({"a.md": "rtsp://u:p" + AT + "h/stream\n"})
        self.assertIn("userinfo_url", _rules(gate.scan(d, [])))

    def test_ipv4(self):
        d = _tree({"a.md": "server 10." + "20.30.40 up\n"})
        self.assertEqual(_rules(gate.scan(d, [])), {"ipv4"})

    def test_cpf_cnpj_phone(self):
        d = _tree({"a.md": "cpf 123.456." + "789-09\ncnpj 12.345." + "678/0001-90\nphone +55 (51) 9" + "9999-1234\n"})
        hits = gate.scan(d, [])
        self.assertIn((1, "cpf"), [(h[1], h[2]) for h in hits])
        self.assertIn((2, "cnpj"), [(h[1], h[2]) for h in hits])
        self.assertIn((3, "phone_br"), [(h[1], h[2]) for h in hits])


class TestPaths(unittest.TestCase):
    def test_file_name(self):
        d = _tree({"notes-SECRETWORD.md": "clean\n"})
        self.assertEqual(gate.scan(d, [TERM]), [("notes-[REDACTED].md", 0, "denylist#1")])

    def test_dir_name(self):
        d = _tree({os.path.join("SECRETWORD", "a.md"): "clean\n"})
        self.assertEqual(gate.scan(d, [TERM]), [("[REDACTED]", 0, "denylist#1")])

    def test_skips_git_and_vendor(self):
        d = _tree({
            os.path.join(".git", "x"): "SECRETWORD\n",
            os.path.join("knowledge", "vendor", "y.md"): "SECRETWORD\n",
        })
        self.assertEqual(gate.scan(d, [TERM]), [])


class TestZip(unittest.TestCase):
    def test_scan_zip_dir(self):
        dist = tempfile.mkdtemp()
        with zipfile.ZipFile(os.path.join(dist, "skill-a.zip"), "w") as z:
            z.writestr("skill-a/SKILL.md", "---\nname: skill-a\n---\nhas SECRETWORD\n")
        with zipfile.ZipFile(os.path.join(dist, "skill-b.zip"), "w") as z:
            z.writestr("skill-b/SKILL.md", "---\nname: skill-b\n---\nclean\n")
        hits = gate.scan_zip_dir(dist, [TERM])
        self.assertEqual(hits, [("skill-a.zip!skill-a/SKILL.md", 4, "denylist#1")])


class TestNoLeak(unittest.TestCase):
    def test_cli_never_prints_term(self):
        d = _tree({"SECRETWORD-file.md": "line with SECRETWORD and mail a" + AT + "b.example.org\n"})
        deny = os.path.join(tempfile.mkdtemp(), "deny.txt")
        with open(deny, "w") as f:
            f.write("# comment\n" + TERM + "\n")
        p = subprocess.run([sys.executable, os.path.join(TOOLS, "gate.py"), "--denylist", deny, "--root", d],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        out = p.stdout + p.stderr
        self.assertNotIn(TERM, out)
        self.assertNotIn("a" + AT + "b.example.org", out)
        self.assertIn("denylist#1", out)

    def test_main_output_format(self):
        d = _tree({"a.md": "SECRETWORD\n"})
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gate.report(gate.scan(d, [TERM]))
        self.assertEqual(code, 1)
        self.assertEqual(buf.getvalue().strip(), "a.md:1:denylist#1")


if __name__ == "__main__":
    unittest.main()
