# 3.0.1

- Strengthen source binding, product review, canonical ledger and blocked recovery order.
- Preserve state across interrupted writes and detect pause changes during postflight.
- macOS/Codex/Python 3.13 scoped validation; no remote publication performed.

# Change notes

## 3.0.0 — 2026-10-22

This stable-version package contains the completed lifecycle refactor previously maintained locally on the 2.0.4 baseline. It supports software and Skill development, task readiness and authorization, current-object verification, failure preservation and handover.

Recent fixes include evidence appropriate to the actual execution channel, predeclared negative tests, separation of current acceptance from failure history, read compatibility for older completed tasks, and literal empty argv preservation.

The distribution is now a self-contained `pm-skills` directory with bilingual instructions, explicit installation/update/backup/removal tools, a version record and a file manifest. The core lifecycle rule body is unchanged by packaging. macOS and Codex are the supported release scope; other environments are reported in `docs/support.md`.

This file describes the local 3.0.0 package. It does not mean a GitHub push, tag or Release has occurred. Historical experiment failures remain in project records and are not reclassified as successful.
