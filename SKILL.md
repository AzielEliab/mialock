---
name: mialock
description: Use when mapping missing-person events (date×time×event×duration), planning archive/newspaper searches, or John/Jane Doe cold-case query families. Purpose-bound investigative assist. Doe hits are leads only — never auto-ID. Author Aziel Eliab.
---

# M.I.A.Lock

Host: `https://mialock-download-tracker.vibelock.workers.dev`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Health |
| GET | `/v1/skill` | This skill |
| GET | `/v1/example` | Sample payload |
| GET | `/download` | Counted tarball |

OpenAPI: https://mialock-download-tracker.vibelock.workers.dev/openapi.json

Catalog: https://aziel-runtime.vibelock.workers.dev/p/mialock/

AzielTether: https://azieltether-download-tracker.vibelock.workers.dev/

```bash
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
python -m mialock map
python -m mialock search-options
```

Boundaries: purpose-bound missing-person / authorized investigative use. Hit ≠ ID. No live tracking. No restricted LE scraping. Author Aziel Eliab.
