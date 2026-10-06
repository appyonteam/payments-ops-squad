#!/usr/bin/env python3
"""Build one .zip per skill for Claude web and app (Settings > Capabilities > Skills).

Each zip holds ``<name>/SKILL.md`` at its root plus the skill's other files. Agents become
skills: their frontmatter is reduced to ``name`` and ``description`` (tools and
disallowedTools only mean something to Claude Code subagents). Every zip carries the MIT
license of this project; zips of the adapted Stripe skills also carry the upstream license.

Usage: build_dist.py [ROOT] [OUT]   (defaults: . and dist)
"""
import glob
import json
import os
import re
import sys
import zipfile

SKIP_NAMES = {".DS_Store", "__pycache__"}
NAME_RE = re.compile(r"^[a-z0-9-]+$")
FIXED_TIME = (2026, 1, 1, 0, 0, 0)  # reproducible archives


def split_frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("missing frontmatter")
    return m.group(1), text[m.end():]


def frontmatter_fields(fm):
    fields = {}
    for line in fm.splitlines():
        m = re.match(r"([A-Za-z_-]+):\s?(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2)
    return fields


def unquote(value):
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def quote(value):
    # A JSON string is a valid YAML double-quoted scalar. Plain scalars that contain ": " are
    # tolerated by Claude Code but rejected by strict YAML parsers, so zips always quote.
    return json.dumps(unquote(value), ensure_ascii=False)


def normalize_skill(text):
    """Quote the description line of a SKILL.md frontmatter; everything else is kept."""
    fm, body = split_frontmatter(text)
    lines = [("description: " + quote(line[len("description: "):]) if line.startswith("description: ") else line)
             for line in fm.splitlines()]
    return "---\n%s\n---\n%s" % ("\n".join(lines), body)


def agent_to_skill(text):
    fm, body = split_frontmatter(text)
    f = frontmatter_fields(fm)
    return "---\nname: %s\ndescription: %s\n---\n%s" % (f["name"], quote(f["description"]), body)


def upstream_license(root):
    with open(os.path.join(root, "THIRD_PARTY_NOTICES.md"), encoding="utf-8") as fh:
        notices = fh.read()
    m = re.search(r"```text\n(MIT License\n\nCopyright \(c\) 2026 Erencan.*?)```", notices, re.S)
    if not m:
        raise ValueError("upstream MIT text not found in THIRD_PARTY_NOTICES.md")
    return ("The skill in this archive is adapted from appeeky/stripe-skills "
            "(https://github.com/appeeky/stripe-skills), distributed under this license:\n\n" + m.group(1))


def _write(z, arcname, data):
    info = zipfile.ZipInfo(arcname, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, data)


def _zip(out, name, files, extra):
    """files: list of (arc_relpath, bytes); extra: dict of arc_relpath -> str."""
    if not NAME_RE.match(name) or len(name) > 64:
        raise ValueError("invalid skill name: %r" % name)
    path = os.path.join(out, name + ".zip")
    with zipfile.ZipFile(path, "w") as z:
        for rel, data in sorted(files):
            _write(z, "%s/%s" % (name, rel), data)
        for rel, data in sorted(extra.items()):
            _write(z, "%s/%s" % (name, rel), data.encode("utf-8"))
    return path


def _dir_files(src_dir):
    res = []
    for dp, dns, fns in os.walk(src_dir):
        dns[:] = sorted(d for d in dns if d not in SKIP_NAMES)
        for fn in sorted(fns):
            if fn in SKIP_NAMES:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, src_dir).replace(os.sep, "/")
            with open(p, "rb") as fh:
                data = fh.read()
            if rel == "SKILL.md":
                data = normalize_skill(data.decode("utf-8")).encode("utf-8")
            res.append((rel, data))
    return res


def build(root, out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(root, "LICENSE"), encoding="utf-8") as fh:
        own_license = fh.read()
    stripe_license = upstream_license(root)
    res = []
    for a in sorted(glob.glob(os.path.join(root, "agents", "*.md"))):
        name = os.path.basename(a)[:-3]
        with open(a, encoding="utf-8") as fh:
            skill = agent_to_skill(fh.read())
        res.append(_zip(out, name, [("SKILL.md", skill.encode("utf-8"))], {"LICENSE.txt": own_license}))
    for d in sorted(glob.glob(os.path.join(root, "skills", "stripe", "*"))):
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            res.append(_zip(out, os.path.basename(d), _dir_files(d),
                            {"LICENSE.txt": own_license, "THIRD_PARTY_LICENSE.txt": stripe_license}))
    for d in sorted(glob.glob(os.path.join(root, "skills", "*"))):
        if os.path.basename(d) != "stripe" and os.path.isfile(os.path.join(d, "SKILL.md")):
            res.append(_zip(out, os.path.basename(d), _dir_files(d), {"LICENSE.txt": own_license}))
    return res


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    out = sys.argv[2] if len(sys.argv) > 2 else "dist"
    zips = build(root, out)
    for z in zips:
        print(z)
    print("%d packages" % len(zips), file=sys.stderr)
