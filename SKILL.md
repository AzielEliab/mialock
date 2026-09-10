---
name: mialock
description: Use when mapping missing-person events (date×time×event×duration), ranking Doe descriptor compatibility leads, reading adapter coverage reports, or describing map layers (uncertainty ellipses + coverage heat). Purpose-bound investigative assist. Doe hit ≠ ID. Coverage heat ≠ presence. Dual surface: Worker /v1 + catalog MCP. This Worker /v1/mesh/* PROXY to aziel-runtime via AZIEL_RUNTIME. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer is a hub cite / Worker mesh cross-map only (local qnsd in qnm-node; no public qnsd proxy). No Node Gate. No auto-heal. Not anonymity. Author Aziel Eliab.
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
| GET | `/v1/mesh` | PROXY suite mesh status. Default OFF. QNM live|locked|isolated. QNS-CD-1.0 cross-map. Never enables. |
| GET | `/v1/mesh/nodes` | PROXY Live Nodes roster (5-minute presence). Includes QNS-CD-1.0 cross-map. |
| POST | `/v1/mesh/{enable,disable,join,heartbeat,leave,broadcast}` | PROXY. Bearer required to enable. No auto-heal. |
| GET | `/download` | Counted tarball |

OpenAPI: https://mialock-download-tracker.vibelock.workers.dev/openapi.json

Catalog: https://aziel-runtime.vibelock.workers.dev/p/mialock/

AzielTether: https://azieltether-download-tracker.vibelock.workers.dev/

```bash
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/mesh
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
python -m mialock map
python -m mialock doe-match --subject subj-elena-cold-demo
python -m mialock coverage --subject subj-elena-cold-demo
```

Local map (http://127.0.0.1:8765): toggle uncertainty ellipses and coverage heat. `doe_cold` mode shows descriptor-match lead cards + field breakdown.

Boundaries: purpose-bound missing-person / authorized investigative use. Doe hit ≠ ID. Coverage heat ≠ presence. No live tracking. No restricted LE scraping. Worker homepage Live Nodes strip polls `GET /v1/mesh` (default OFF). QNS-CD-1.0 (photon QNS1 packet transfer) is a hub cite / Worker mesh cross-map only — local qnsd in [qnm-node](https://github.com/AzielEliab/qnm-node); runtime cites in [aziel-runtime](https://github.com/AzielEliab/aziel-runtime); AZInterface pair custody. Not a Softwares-tab product. No public qnsd proxy. No Node Gate. No auto-heal. Not anonymity. Author Aziel Eliab.
