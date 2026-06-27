# Agent-Ready run archive

Per-website **before[] / after[]** boxes for every Agent-Ready analyze or apply run.

## Layout

```text
agent-ready-sites/
  {host}/                    # e.g. obolla.com
    SITE.json                # site index (last run, totals)
    runs/
      {timestamp}_{id}/      # one run = one box
        RUN.json             # metadata + change summary
        CHANGELOG.md         # human-readable what changed
        before/              # live origin snapshot
        after/               # proposed fix-pack files
        diffs/               # unified diffs per file
```

## When files are written

| Action | API / MCP | `RUN.json` action |
|--------|-----------|-------------------|
| Analyze + fix pack | `POST /api/v1/agent-ready/analyze` | `analyze` |
| Apply fix pack | `POST /api/v1/agent-ready/apply` or MCP `apply_agent_ready_fix` | `apply_agent_ready_fix` |

API responses include `run_archive`: `{ run_id, path, changed_count, git }`.

## List archives

```http
GET /api/v1/agent-ready/archive/sites
GET /api/v1/agent-ready/archive/runs?url=https://obolla.com
GET /api/v1/agent-ready/archive/runs/obolla.com/{run_id}
```

## Git

Runs auto-commit into this repo when `AGENT_READY_ARCHIVE_GIT=1` (default) and `.git` is found.

```powershell
# Commit any pending archive changes + push
pwsh -NoProfile -File scripts/push-agent-ready-archive.ps1
```

Optional auto-push after each run: `AGENT_READY_ARCHIVE_GIT_PUSH=1`.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_READY_ARCHIVE_ROOT` | `<repo>/agent-ready-sites` | Archive root path |
| `AGENT_READY_ARCHIVE_GIT` | `1` | Auto `git commit` per run |
| `AGENT_READY_ARCHIVE_GIT_PUSH` | `0` | Auto `git push` after commit |