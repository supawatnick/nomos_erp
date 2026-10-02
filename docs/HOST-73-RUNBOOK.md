# Host 72 → Host 73 SSH / Runtime Runbook

> Source of truth for NOMOS ERP remote development access. Read this before any build, test, migration, database, or runtime work.

## Host roles

- **Host 72 / control host**: orchestration only. Do not use it as the ERP runtime/build/test/database host.
- **Host 73 / runtime host**:
  - IP: `10.10.110.73`
  - verified hostname: `nomos-erp`
  - SSH user: `root`
  - NOMOS ERP repository: `/root/nomos_erp`
  - Git remote: `git@github.com:supawatnick/nomos_erp.git`

## Verified SSH identity from host 72

The working private key on host 72 is `/root/.ssh/ntap_office_demo_ed25519`.

Do **not** confuse it with `/root/.ssh/nomos_erp_73_github`. That key was tested against SSH login to host 73 and was rejected.

Verified command:

```bash
ssh -i /root/.ssh/ntap_office_demo_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes root@10.10.110.73 hostname
```

Expected output: `nomos-erp`.

## Important SSH pitfall

Do **not** run plain `ssh 73` unless an explicit SSH alias exists. Without a configured alias, OpenSSH interprets `73` as numeric IPv4 `0.0.0.73`, which times out.

Use the explicit IP + identity command as the reliable fallback.

Recommended alias if host-level SSH config is available:

```sshconfig
Host 73
    HostName 10.10.110.73
    User root
    IdentityFile /root/.ssh/ntap_office_demo_ed25519
    IdentitiesOnly yes
    BatchMode yes
    ConnectTimeout 5
```

## Pre-work verification

Before changing ERP code:

```bash
ssh -i /root/.ssh/ntap_office_demo_ed25519 -o IdentitiesOnly=yes root@10.10.110.73 \
  "hostname && cd /root/nomos_erp && git remote -v && git status --short --branch && git log -1 --oneline --decorate && git stash list"
```

Required facts: hostname `nomos-erp`; repo `/root/nomos_erp`; origin `supawatnick/nomos_erp`; inspect working tree and stashes before mutation.

## Safe sync procedure

Fetch and inspect divergence first:

```bash
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
```

Only fast-forward when local has no unique commits:

```bash
git merge --ff-only origin/main
```

Never use `git reset --hard`, `git clean`, force push, or drop/apply stashes merely to make the tree look clean.

## Preserved stashes

Verified on 2026-10-02:

```text
stash@{0}: On main: phase1-npm-lock-before-sync
stash@{1}: On main: phase1-presync-local-work-2
stash@{2}: On main: phase1-presync-local-work
```

They are **not disposable**. Review contents and purpose before any apply/pop/drop.

## Last verified state

Reverified on 2026-10-02 at the Phase 11 final documentation/runtime closure:
- SSH login to `nomos-erp` succeeded from host 72 using `/root/.ssh/ntap_office_demo_ed25519` with `IdentitiesOnly=yes`.
- Repository `/root/nomos_erp` was fast-forwarded to final Phase 11 documentation commit `2fb48d7aa7c9cf4406cc3b9195607fc66e26b22f`.
- Repository matched `origin/main`: **0 ahead / 0 behind**, with a clean working tree.
- The three historical stashes remained preserved and untouched.
- Runtime dependencies were synchronized from `apps/api/requirements.txt`.
- Runtime PostgreSQL was upgraded through Alembic `0015_phase11_reporting (head)`.
- Full PostgreSQL/API suite on host 73 with the API environment: **70 passed**.
- Final Phase 11 documentation CI run `37007719034`: **SUCCESS**, including Ruff, mypy, Alembic, PostgreSQL tests, pip-audit, npm audit high, Web lint/typecheck/tests/build and full-history Gitleaks.
- Phase 11 is therefore runtime-synchronized and closed; Phase 12 may start from this baseline.

After any later documentation/code commit, fast-forward host 73 again before implementation so runtime HEAD equals `origin/main`.

## Rule for future sessions

If SSH fails: use `10.10.110.73` rather than bare `73`; confirm TCP/22 and host key; use `/root/.ssh/ntap_office_demo_ed25519` with `IdentitiesOnly=yes`; verify hostname `nomos-erp`; enter `/root/nomos_erp`; inspect Git status/remote/stashes before mutation.

Do not guess the host, repo path, key, or Git state.


## Current Web/API runtime — verified 2026-10-02

Private-network browser entry URL: **http://10.10.110.73/**

Runtime topology:
- Caddy: host-network container, port 80, restart unless-stopped.
- Next.js Web: nomos-web.service, enabled/active, production build on port 3000.
- FastAPI: nomos-api.service, enabled/active, canonical listener 127.0.0.1:8020.
- Caddy proxies /api/*, /health and /ready to FastAPI and all other routes to Next.js.
- Browser uses same-origin API calls; no separate CORS URL is required.

Acceptance evidence:
- / and /login: HTTP 200.
- /health: status ok.
- /ready: status ready.
- /inventory, /procurement, /sales, /finance, /reports and /settings/subscription: HTTP 200.
- Source of truth for the gate: docs/WEB-RUNTIME-ACCEPTANCE.md.

Legacy manually started localhost API listeners observed on 8000/8010 are not the canonical deployed API service. New operational procedures must target nomos-api.service on 8020.
