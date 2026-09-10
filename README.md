# M.I.A.Lock

Per-person event map, archive / John·Jane Doe cold-case search options, Doe descriptor matching, uncertainty ellipses, and coverage-heat layers.

**Author:** Aziel Eliab · Apache-2.0 · Forks welcome.

Purpose-bound legitimate missing-person / authorized investigative use. Doe hits are compatibility leads only — never auto-identification. Coverage heat is search intensity / negative-evidence weight — not a probability of presence. No live tracking.

## One-click download (counted)

[https://mialock-download-tracker.vibelock.workers.dev/download](https://mialock-download-tracker.vibelock.workers.dev/download)

Live count: [https://mialock-download-tracker.vibelock.workers.dev/count](https://mialock-download-tracker.vibelock.workers.dev/count)

```bash
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
# or
python -m mialock map
python -m mialock doe-match --subject subj-elena-cold-demo
python -m mialock coverage --subject subj-elena-cold-demo
```

Open http://127.0.0.1:8765/ — toggle **Uncertainty ellipses** and **Coverage heat**. Set Search mode to `doe_cold` for ranked lead cards + field-level match/mismatch.

## AI / skill

- Skill: https://mialock-download-tracker.vibelock.workers.dev/v1/skill
- Suite mesh proxy: [https://mialock-download-tracker.vibelock.workers.dev/v1/mesh](https://mialock-download-tracker.vibelock.workers.dev/v1/mesh) — default OFF; QNM live / locked / isolated
- OpenAPI: https://mialock-download-tracker.vibelock.workers.dev/openapi.json
- Toolkit ops: `doe-match`, `coverage`, `queries`, `search-options`, `map`
- Catalog: https://aziel-runtime.vibelock.workers.dev/p/mialock/
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`. Suite mesh `/v1/mesh/*` PROXY via `AZIEL_RUNTIME` (default OFF; QNM-BUILD-1.0 live|locked|isolated; no Node Gate). Catalog MCP `mesh_*` + FragGate `slug=mesh`.

## AzielTether

Survival mesh for downloaded software: https://azieltether-download-tracker.vibelock.workers.dev/

## iPhone & Android

Flutter sources: [`mobile/`](mobile/). Application id
`com.azieeliab.mialock`. Screens call the hosted Worker
(`/v1/map`, `/v1/search-options`, `/v1/queries`, `/v1/doe-match`,
`/v1/coverage`). Doe hits are compatibility leads — never an
identification. Coverage heat ≠ presence. Not a store listing.
Not a separate repo. Worker UI stays on the download tracker.

```bash
cd mobile
flutter create --org com.azieeliab --project-name mialock .
flutter pub get
flutter run
```

Open `android/` in Android Studio, or `ios/Runner.xcworkspace` in Xcode
after `flutter create`. This tree does not ship store IPAs.

## Everblooming sigil

Visual brand mark only. Public identity remains Aziel Eliab.
