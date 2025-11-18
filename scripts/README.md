# scripts/ — Project Synth helper scripts

This folder contains several convenience scripts used during development and for running Project Synth.

Which scripts are *recommended* to keep tracked in the repo:
- `bootstrap_knowledge.py` — Bootstrap RAG knowledge base from the repo docs and README.
- `connect_brain.sh` — SSH port-forward helper for remote Brain models; useful for dev setups where the Brain is remote.
- `start_brain_tunnel.sh` — Tunnel helper with recommended ports.
- `run_quick_tests.sh` — Runs quick checks (imports, RAG, Brain) for rapid validation.
- `run_all_tests.sh` — Entrypoint for the full test harness.
- `run_synth.sh` — Simple runner for macOS (or `run_synth_v2.sh` at root).

Optional scripts (macOS/system-specific):
- `install_auto_connect.sh` / `uninstall_auto_connect.sh` — Installs a LaunchAgent to auto-connect to Brain on macOS users.
- `launch.sh` / `launch_synth.sh` — Alternative launch helpers, can be redundant.
- `export_clipboard_to_md.sh` — Utility to export clipboard as Markdown.
- `generate_ssh_key.sh` — Convenience for generating SSH keys for connecting to remote Brain.
- `move_project.sh` — Convenience; not required for running Synth in dev.

Guidelines
- Do NOT commit secrets or `.env` values. Use `.env.example` as a template and keep local `.env` out of GitHub (it's listed in `.gitignore`).
- If you run `install_auto_connect.sh` on macOS, the script uses LaunchAgents; administrative permissions may be required.
- If you want to contribute a change to a script, please test by running `bash scripts/<script>.sh` locally.

Suggested usage
- To bootstrap knowledge (RAG):

```bash
# from repo root
./venv/bin/python3 scripts/bootstrap_knowledge.py
```

- To run quick tests:

```bash
bash scripts/run_quick_tests.sh
```

- To run Synth app (macOS):

```bash
bash run_synth_v2.sh
# or
bash scripts/run_synth.sh
```

If a script is extremely platform-specific or user-specific (e.g. auto connect) you can optionally exclude or keep it commented in the `scripts/README.md`.

---

If you prefer to keep only a small subset of the scripts in the repo, tell me which exactly and I will untrack the other ones and leave them as local-only scripts.