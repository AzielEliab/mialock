---
name: mialock
description: Use when mapping missing-person events (date×time×event×duration), ranking Doe descriptor compatibility leads, reading adapter coverage reports, or describing map layers (uncertainty ellipses + coverage heat). Purpose-bound investigative assist. Doe hit ≠ ID. Coverage heat ≠ presence. Author Aziel Eliab.
---

# M.I.A.Lock

Host: `https://mialock-download-tracker.vibelock.workers.dev`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Health |
| GET | `/v1/skill` | This skill |
| GET | `/v1/example` | Sample payload |
| GET | `/v1/map` | Sample index stub; live map is local CLI |
| GET | `/v1/search-options` | Archive / Doe / cold-case modes |
| GET/POST | `/v1/queries` | Render query families |
| GET/POST | `/v1/doe-match` | Rank Doe notices vs a named-subject descriptor (leads only) |
| GET | `/v1/coverage` | Adapter coverage report + heat cells (not presence) |
| GET | `/download` | Counted tarball |

OpenAPI: https://mialock-download-tracker.vibelock.workers.dev/openapi.json

Catalog: https://aziel-runtime.vibelock.workers.dev/p/mialock/

AzielTether: https://azieltether-download-tracker.vibelock.workers.dev/

```bash
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
python -m mialock map
python -m mialock doe-match --subject subj-elena-cold-demo
python -m mialock coverage --subject subj-elena-cold-demo
```

Local map (http://127.0.0.1:8765): toggle uncertainty ellipses and coverage heat. `doe_cold` mode shows descriptor-match lead cards + field breakdown.

Boundaries: purpose-bound missing-person / authorized investigative use. Doe hit ≠ ID. Coverage heat ≠ presence. No live tracking. No restricted LE scraping. Author Aziel Eliab.
