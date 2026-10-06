# Installation

payments-ops-squad installs in three ways. Pick one per machine: the plugin and the install script provide the same agents and
skills, so installing both creates duplicates.

## 1. Claude Code plugin (recommended)

Requirements: Claude Code, Python 3 (for the documentation fetcher).

```bash
claude plugin marketplace add appyonteam/payments-ops-squad
claude plugin install payments-ops-squad@payments-ops-marketplace
```

Restart Claude Code. Check with `/agents` (16 specialists) and by typing `/payments-ops-squad:` to list the commands:

| Command | Skill |
|---|---|
| `/payments-ops-squad:pay-export` | `analyze-export` |
| `/payments-ops-squad:pay-incident` | `investigate-incident` |
| `/payments-ops-squad:pay-decline` | `explain-decline` |
| `/payments-ops-squad:pay-workflow` | `review-workflow` |
| `/payments-ops-squad:pay-ask` | `ask-payments` |
| `/payments-ops-squad:pay-docs` | `fetch-docs` |

Update: `claude plugin marketplace update payments-ops-marketplace`, then `claude plugin update payments-ops-squad@payments-ops-marketplace`.
Remove: `claude plugin uninstall payments-ops-squad`.

## 2. Claude Code install script (no namespace)

```bash
git clone https://github.com/appyonteam/payments-ops-squad.git
cd payments-ops-squad
bash install/install.sh                    # user scope, into ~/.claude
bash install/install.sh --scope project    # project scope, into ./.claude of the current folder
```

Windows (PowerShell):

```powershell
.\install\install.ps1
.\install\install.ps1 -Scope project
```

What the script copies:

- `agents/*.md` to `<dest>/agents/` (16 files)
- every skill to `<dest>/skills/<name>/` (43 folders; the Stripe skills are flattened out of `skills/stripe/`)
- `commands/*.md` to `<dest>/commands/` (6 files; commands have no namespace, for example `/pay-export`)
- `tools/fetch_doc.py`, `knowledge/INDEX.md` and `knowledge/sources.json` to `<dest>/payments-ops-squad/`
- an empty documentation cache at `<dest>/payments-ops-squad/knowledge/`

If any target already exists, the script lists the conflicts, writes nothing and exits with code 2. Run it again with `--force`
(`-Force` on Windows) to overwrite them. To remove the install, delete the files listed above.

On Windows, if `python3` is not on the PATH, run the fetcher with `python` or `py -3`.

## 3. Claude web and desktop app

1. Open the latest GitHub Release of `appyonteam/payments-ops-squad` and download the zips you want (one per skill; 59 in total:
   16 specialists, 35 Stripe skills and 8 use-case skills).
2. In Claude, go to **Settings > Capabilities > Skills** and upload each zip.
3. Skills require a Pro, Max, Team or Enterprise plan with code execution enabled. On Team and Enterprise an owner may need to
   enable skills for the organization first.

Limitations on web and app: there are no subagents (each specialist is a skill whose checklist Claude applies directly), there
are no slash commands, and the documentation fetcher does not run. Skills then read the official documentation online and say so
in their Sources.

To build the zips yourself: `python3 tools/build_dist.py . dist`.

## Documentation cache

`tools/fetch_doc.py` stores official documentation pages in the first of these folders: `$PAYMENTS_OPS_KNOWLEDGE`,
`${CLAUDE_PLUGIN_DATA}/knowledge/`, the script install folder `<dest>/payments-ops-squad/knowledge/`, or
`~/.claude/payments-ops-squad/knowledge/`. Pages are kept for 14 days. To clear the cache, delete the folder. See
[knowledge/INDEX.md](../knowledge/INDEX.md).

## Safety

Agents are instructed to be read-only; this is not technically enforced (they can run Bash). Connect only restricted, read-only
API keys. Three Stripe skills (`checkout-implementation`, `webhook-implementation`, `stripe-billing-context`) generate code or
files when asked.
