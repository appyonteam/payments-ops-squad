#!/usr/bin/env bash
# Install payments-ops-squad without the plugin system: copies agents, skills, commands and the
# documentation fetcher into ~/.claude (user scope) or ./.claude (project scope).
#
# Usage: install/install.sh [--scope user|project] [--force]
#
# Without --force nothing is overwritten: if any target already exists the script lists the
# conflicts, writes nothing and exits 2.
set -euo pipefail

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
}

SCOPE="user"
FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --scope)
      [ $# -ge 2 ] || { echo "install: --scope needs user or project" >&2; exit 1; }
      SCOPE="$2"; shift 2 ;;
    --scope=*) SCOPE="${1#--scope=}"; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "install: unknown option $1" >&2; usage >&2; exit 1 ;;
  esac
done

case "$SCOPE" in
  user) DEST="${HOME}/.claude" ;;
  project) DEST="$(pwd)/.claude" ;;
  *) echo "install: --scope must be user or project" >&2; exit 1 ;;
esac

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG="${DEST}/payments-ops-squad"

# Build the list of units to install: "<kind>|<source>|<target>".
UNITS=()
for f in "$SRC"/agents/*.md; do
  UNITS+=("agent|$f|$DEST/agents/$(basename "$f")")
done
for d in "$SRC"/skills/*/ "$SRC"/skills/stripe/*/; do
  d="${d%/}"
  [ -f "$d/SKILL.md" ] || continue
  UNITS+=("skill|$d|$DEST/skills/$(basename "$d")")
done
for f in "$SRC"/commands/*.md; do
  UNITS+=("command|$f|$DEST/commands/$(basename "$f")")
done
UNITS+=("support|$SRC/tools/fetch_doc.py|$PKG/tools/fetch_doc.py")
UNITS+=("support|$SRC/knowledge/INDEX.md|$PKG/INDEX.md")
UNITS+=("support|$SRC/knowledge/sources.json|$PKG/sources.json")

CONFLICTS=()
for u in "${UNITS[@]}"; do
  target="${u##*|}"
  if [ -e "$target" ]; then CONFLICTS+=("$target"); fi
done

if [ "${#CONFLICTS[@]}" -gt 0 ] && [ "$FORCE" -ne 1 ]; then
  echo "install: ${#CONFLICTS[@]} target(s) already exist; nothing was written:" >&2
  for c in "${CONFLICTS[@]}"; do echo "  $c" >&2; done
  echo "install: run again with --force to overwrite them." >&2
  exit 2
fi

n_agent=0; n_skill=0; n_command=0; n_support=0
for u in "${UNITS[@]}"; do
  kind="${u%%|*}"; rest="${u#*|}"; src="${rest%%|*}"; target="${rest#*|}"
  mkdir -p "$(dirname "$target")"
  if [ -d "$src" ]; then
    rm -rf "$target"
    cp -R "$src" "$target"
  else
    cp "$src" "$target"
  fi
  case "$kind" in
    agent) n_agent=$((n_agent + 1)) ;;
    skill) n_skill=$((n_skill + 1)) ;;
    command) n_command=$((n_command + 1)) ;;
    support) n_support=$((n_support + 1)) ;;
  esac
done

# Knowledge cache for documentation fetched on demand. The marker lets fetch_doc.py find it.
mkdir -p "$PKG/knowledge"
: > "$PKG/knowledge/.payments-ops-cache"

echo "payments-ops-squad installed (${SCOPE} scope) into ${DEST}"
echo "  agents:   ${n_agent}"
echo "  skills:   ${n_skill}"
echo "  commands: ${n_command}"
echo "  tools:    ${PKG}/tools/fetch_doc.py"
echo "  cache:    ${PKG}/knowledge/"
if [ "${#CONFLICTS[@]}" -gt 0 ]; then
  echo "  overwritten (--force): ${#CONFLICTS[@]}"
fi
echo "Restart Claude Code to load the new agents, skills and commands."
