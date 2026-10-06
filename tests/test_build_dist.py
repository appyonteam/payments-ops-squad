import os
import re
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import build_dist  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS, STRIPE, OWN = 21, 35, 8


class BuildDistTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp()
        cls.zips = build_dist.build(ROOT, cls.out)

    def test_count(self):
        self.assertEqual(len(self.zips), AGENTS + STRIPE + OWN)
        self.assertEqual(len(set(self.zips)), len(self.zips))

    def test_layout_and_frontmatter(self):
        agent_names = {f[:-3] for f in os.listdir(os.path.join(ROOT, "agents")) if f.endswith(".md")}
        for z in self.zips:
            skill = os.path.basename(z)[:-4]
            with zipfile.ZipFile(z) as f:
                names = f.namelist()
                self.assertIn("%s/SKILL.md" % skill, names, z)
                self.assertIn("%s/LICENSE.txt" % skill, names, z)
                for n in names:
                    self.assertTrue(n.startswith(skill + "/"), n)
                    self.assertNotIn("..", n)
                text = f.read("%s/SKILL.md" % skill).decode("utf-8")
            self.assertTrue(text.startswith("---\nname: "), z)
            fm, _ = build_dist.split_frontmatter(text)
            fields = build_dist.frontmatter_fields(fm)
            name = fields["name"]
            self.assertTrue(fields["description"].startswith('"'), z)  # quoted: valid strict YAML
            desc = build_dist.unquote(fields["description"])
            self.assertEqual(name, skill)
            self.assertLessEqual(len(name), 64)
            self.assertRegex(name, r"^[a-z0-9-]+$")
            self.assertTrue(desc.strip(), z)
            self.assertLessEqual(len(desc), 1024, z)
            if skill in agent_names:
                self.assertEqual(sorted(fields), ["description", "name"], z)
                self.assertNotIn("tools:", fm)
                self.assertIn("_Created by Vitor Dvorschi (Appyon). MIT License._", text)

    def test_stripe_zips_carry_upstream_license(self):
        stripe = {os.path.basename(d) for d in os.listdir(os.path.join(ROOT, "skills", "stripe"))}
        for z in self.zips:
            skill = os.path.basename(z)[:-4]
            with zipfile.ZipFile(z) as f:
                has = "%s/THIRD_PARTY_LICENSE.txt" % skill in f.namelist()
                if has:
                    self.assertIn("Copyright (c) 2026 Erencan", f.read("%s/THIRD_PARTY_LICENSE.txt" % skill).decode())
            self.assertEqual(has, skill in stripe, z)

    def test_reproducible(self):
        out2 = tempfile.mkdtemp()
        zips2 = build_dist.build(ROOT, out2)
        for a, b in zip(sorted(self.zips), sorted(zips2)):
            with open(a, "rb") as fa, open(b, "rb") as fb:
                self.assertEqual(fa.read(), fb.read(), a)

    def test_rejects_bad_name(self):
        with self.assertRaises(ValueError):
            build_dist._zip(tempfile.mkdtemp(), "Bad_Name", [("SKILL.md", b"x")], {})


if __name__ == "__main__":
    unittest.main()
