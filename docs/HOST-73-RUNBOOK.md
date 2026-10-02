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

Reverified on 2026-10-02 during the Phase 0–8 repository audit:
- SSH login to `nomos-erp` succeeded with `/root/.ssh/ntap_office_demo_ed25519`.
- Repository `/root/nomos_erp` matched `origin/main` with 0 ahead / 0 behind before the audit documentation commit and had a clean working tree.
- The three historical stashes remained preserved and untouched.
- PostgreSQL and Redis Compose services were healthy.
- Runtime PostgreSQL was upgraded from stale Alembic `0009_phase8_procurement` to `0012_phase9_sales (head)`.
- Full PostgreSQL pytest run with the host 73 API environment: **61 passed**.
- GitHub `main` gate immediately before this audit documentation update was run `37000290630`: **SUCCESS**, including Ruff, mypy, migrations, PostgreSQL tests, dependency audits, Web lint/typecheck/tests/build and full-history Gitleaks.

After any documentation/code commit, fast-forward host 73 again before beginning implementation so runtime HEAD equals `origin/main`.

## Rule for future sessions

If SSH fails: use `10.10.110.73` rather than bare `73`; confirm TCP/22 and host key; use `/root/.ssh/ntap_office_demo_ed25519` with `IdentitiesOnly=yes`; verify hostname `nomos-erp`; enter `/root/nomos_erp`; inspect Git status/remote/stashes before mutation.

Do not guess the host, repo path, key, or Git state.
