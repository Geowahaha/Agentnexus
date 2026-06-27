# AgentNexus Runbook

Use this skill as a portable AI visibility audit/improvement pack. Do not store or paste API tokens, account secrets, private keys, passwords, or bearer tokens in AgentNexus prompts, memory, or logs.

## Recommended Setup

Import or attach the entire `audit-ai-visibility` folder.

Primary files:

- `README.md`: install, portability, and troubleshooting guide.
- `SKILL.md`: main process.
- `references/portable-agent-prompt.md`: prompt to paste into AgentNexus.
- `scripts/audit_ai_visibility.mjs`: cross-platform Node.js audit script.
- `scripts/audit-ai-visibility.bat`: Windows wrapper for agents that prefer batch commands.
- `references/pinpoint-case-study.md`: before/after example and traffic-lift reasoning.

## Command Options

JSON output for automation:

```bat
scripts\audit-ai-visibility.bat https://example.com
```

Markdown output for human review:

```bat
scripts\audit-ai-visibility.bat https://example.com --markdown
```

Cross-platform direct Node command:

```bash
node scripts/audit_ai_visibility.mjs https://example.com --markdown
```

Portable runtime check on Windows:

```bat
scripts\verify-portable.bat
```

## AgentNexus Workflow

1. Read `references/portable-agent-prompt.md`.
2. Run the audit command against the target production URL.
3. Parse `likelyIssues` from JSON output, or read the Markdown report.
4. If fixes require hosting/CDN access, use only existing authenticated environments or dashboard instructions. Do not ask the user to paste secrets.
5. After fixes, rerun the same audit command and compare before/after.
6. Summarize likely traffic drivers separately from measurement changes.

## Safe Fix Guidance

- Fix policy conflicts first: `robots.txt`, response headers, `llms.txt`, `ai.txt`, and `agents.txt` should not contradict each other.
- Use `ai-train=no, search=yes, ai-input=yes` when the business wants AI assistants to answer from public content but does not want training use.
- Keep private routes such as `/api/`, admin paths, internal files, and confirmation pages out of public AI usage.
- For Cloudflare Pages, deploy a clean public/static bundle only.
- For `www` errors, prefer a 301 redirect to the canonical host or add `www` as a valid hosting custom domain.
