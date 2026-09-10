/**
 * M.I.A.Lock hosted runtime.
 * Hosted /v1 never touches DOWNLOADS KV.
 * Map / search-options / queries are hosted stubs. Live Leaflet map is local CLI.
 * /v1/mesh/* PROXY to aziel-runtime via AZIEL_RUNTIME (handled in index.js before this catch-all).
 * Author: Aziel Eliab.
 */
import { meshOpenApiPaths, meshPointer } from "./mesh.js";
import SEARCH_MODES from "./search-modes.json";
import SAMPLE_INDEX from "./sample-index.json";
import SAMPLE_COVERAGE from "./sample-coverage.json";
import { hostedDoeMatch } from "./doe-match.js";

const PRODUCT = "mialock";
const VERSION = "0.1.1";
const AUTHOR = "Aziel Eliab";
const MOTTO =
  "Search broadly. Match probabilistically. Challenge every hit. Preserve provenance. Verify before action.";
const HOST = "https://mialock-download-tracker.vibelock.workers.dev";
const CATALOG = "https://aziel-runtime.vibelock.workers.dev";
const TETHER = "https://azieltether-download-tracker.vibelock.workers.dev";
const LIMITATION =
  "THIS IS: purpose-bound missing-person investigative software — per-person historical event maps (date × time × event × duration), Doe descriptor matching (leads only), uncertainty ellipses, and coverage-heat layers (search intensity / negative evidence — not presence). THIS IS NOT: live location tracking, an identification, a crawler of restricted law-enforcement systems, or automated accusation. Doe hit ≠ ID. Author Aziel Eliab.";
const COVERAGE_FRAMING =
  "Heat = search coverage intensity / negative-evidence weight — not a probability of presence.";

const EXAMPLE_PAYLOAD = {
  mode: "doe_cold",
  name: "Elena Vargas",
  aliases: "Elena Vargas",
  jurisdiction: "US-IL-COOK",
  year_from: "1994",
  year_to: "1995",
  age_band: "20-30",
  sex: "female",
  height_cm: 165,
  build: "slim",
  scars_marks: "tattoo left wrist",
  clothing: "red jacket",
};

const SKILL = `---
name: M.I.A.Lock
description: Use when mapping documented missing-person events (date × time × event × duration), ranking Doe descriptor compatibility leads, reading adapter coverage reports, or describing map layers (uncertainty ellipses + coverage heat). Purpose-bound investigative use. Doe hit ≠ ID. Coverage heat ≠ presence. Dual surface: Worker /v1 + catalog MCP. This Worker /v1/mesh/* PROXY to aziel-runtime via AZIEL_RUNTIME. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Author Aziel Eliab.
---

# M.I.A.Lock

**Missing Individual Autonomous Lock** v0.1.1. Per-person historical event map, archive / Doe cold-case search options, Doe descriptor matching, uncertainty ellipses, and coverage-heat layers.

Author: **Aziel Eliab**.

**THIS IS:** purpose-bound missing-person investigative software — documented historical pins (date × time × event × duration), ranked Doe *compatibility leads*, adapter coverage reports, and map layers.

**THIS IS NOT:** live location tracking, an identification, a crawler of restricted law-enforcement systems, or automated accusation. Doe hit ≠ ID. Coverage heat is search intensity / negative-evidence weight — not a probability of presence. Hosted \`/v1\` does not increment downloads.

Always send \`User-Agent: Mozilla/5.0\`. Cloudflare Workers may 403 an empty agent.

## Endpoints (this Worker)

Host: \`https://mialock-download-tracker.vibelock.workers.dev\`

| Method | Path | What |
|--------|------|------|
| GET | \`/v1/health\` | Liveness. Does not increment downloads. |
| GET | \`/v1/skill\` | This markdown. Does not increment downloads. |
| GET | \`/v1/example\` | Sample query / Doe-match payload. Does not increment downloads. |
| GET | \`/v1/map\` | Sample casebook index stub. Live Leaflet map is local CLI \`mialock map\` (ellipses + coverage heat toggles; \`doe_cold\` shows lead cards). |
| GET | \`/v1/search-options\` | List archive / Doe / cold-case search modes. |
| GET/POST | \`/v1/queries\` | Render query families for a mode. Search plans only. Doe leads ≠ ID. |
| GET/POST | \`/v1/doe-match\` | Rank Doe / unidentified notices vs a named-subject descriptor. Compatibility leads only with score + field match/mismatch. Never an ID. |
| GET | \`/v1/coverage\` | Sample adapter coverage report + heat cells. Heat = search intensity / negative evidence — not presence. |
| GET | \`/v1/mesh\` | PROXY suite mesh status. Default OFF. QNM live|locked|isolated. Never enables. |
| GET | \`/v1/mesh/nodes\` | PROXY Live Nodes roster (5-minute presence). |
| POST | \`/v1/mesh/{enable,disable,join,heartbeat,leave,broadcast}\` | PROXY. Bearer required to enable. No auto-heal. Anon-broadcast is not a publish path. |

OpenAPI: \`https://mialock-download-tracker.vibelock.workers.dev/openapi.json\`

Catalog OpenAPI: \`https://aziel-runtime.vibelock.workers.dev/openapi.json\`

MCP: \`POST https://aziel-runtime.vibelock.workers.dev/mcp\`

AzielTether: \`https://azieltether-download-tracker.vibelock.workers.dev/\`

Catalog aliases under \`/p/mialock/…\`.

## How to call (Mozilla/5.0)

\`\`\`bash
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/search-options
curl -s -A 'Mozilla/5.0' -X POST https://mialock-download-tracker.vibelock.workers.dev/v1/queries \\
  -H 'content-type: application/json' \\
  -d '{"mode":"doe_cold","name":"Elena Vargas","jurisdiction":"US-IL-COOK","age_band":"20-30","sex":"female"}'
curl -s -A 'Mozilla/5.0' -X POST https://mialock-download-tracker.vibelock.workers.dev/v1/doe-match \\
  -H 'content-type: application/json' \\
  -d '{"age_band":"20-30","sex":"female","height_cm":165,"build":"slim","scars_marks":"tattoo left wrist","clothing":"red jacket","jurisdiction":"US-IL-COOK","time_window_from":"1994-09-02","time_window_to":"1995-12-31"}'
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/coverage?subject=subj-elena-cold-demo
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/skill
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/mesh
\`\`\`

Grok: import this OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools. Toolkit ops: \`doe-match\`, \`coverage\`, \`queries\`, \`search-options\`, \`map\` (local layers described here).

## Local (after one-click install)

\`\`\`bash
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
python -m mialock map
python -m mialock doe-match --subject subj-elena-cold-demo
python -m mialock coverage --subject subj-elena-cold-demo
python -m mialock geojson subj-elena-cold-demo --mode doe_cold
\`\`\`

Then open http://127.0.0.1:8765 (this computer only). Toggle **Uncertainty ellipses** and **Coverage heat**. Set Search mode to \`doe_cold\` for lead cards + field breakdown. The live map is local. Hosted \`/v1/map\` is a sample index stub.

Map layers:

- Uncertainty ellipses — semi-axes from location uncertainty / jurisdiction footprint / time-window geo soft-band. Not live location.
- Coverage heat — where adapters were searched vs dead-ends / low coverage. Not a presence probability.

## Honest banner

${LIMITATION}

Apache-2.0 (or the repo LICENSE). Forks are welcome and always allowed.

## Catalog + local CLI

Author: **Aziel Eliab**. Honest scope: purpose-bound missing-person event map. Doe leads ≠ ID. Not live tracking.

- Catalog product: https://aziel-runtime.vibelock.workers.dev/p/mialock/
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- Catalog MCP: \`POST https://aziel-runtime.vibelock.workers.dev/mcp\`
- This Worker skill: \`GET https://mialock-download-tracker.vibelock.workers.dev/v1/skill\`
- This Worker OpenAPI: https://mialock-download-tracker.vibelock.workers.dev/openapi.json
- Sample payload: \`GET https://mialock-download-tracker.vibelock.workers.dev/v1/example\`
- Suite mesh: \`GET https://mialock-download-tracker.vibelock.workers.dev/v1/mesh\` PROXY (default OFF)
- AzielTether: https://azieltether-download-tracker.vibelock.workers.dev/v1/skill

Counted download (gzip HTTP 200, no 302): https://mialock-download-tracker.vibelock.workers.dev/download?asset=mialock-0.1.1.tar.gz
GitHub: https://github.com/AzielEliab/mialock
`;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, X-Aziel-Runtime-Token, User-Agent, MCP-Protocol-Version, mcp-session-id",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function listModes() {
  return Object.values(SEARCH_MODES).map((mode) => ({
    mode_id: mode.mode_id,
    title: mode.title,
    summary: mode.summary,
    cold_case: mode.cold_case,
    doe_match: mode.doe_match,
    archive: mode.archive,
    event_classes: mode.event_classes,
    adapter_families: mode.adapter_families,
    query_family_count: (mode.query_families || []).length,
  }));
}

function renderQueries(modeId, tokens) {
  const mode = SEARCH_MODES[modeId];
  if (!mode) return null;
  const defaults = {
    name: tokens.name || "{name}",
    aliases: tokens.aliases || "{aliases}",
    jurisdiction: tokens.jurisdiction || "{jurisdiction}",
    jurisdiction_or_region: tokens.jurisdiction_or_region || tokens.jurisdiction || "{jurisdiction_or_region}",
    year_from: tokens.year_from || "{year_from}",
    year_to: tokens.year_to || "{year_to}",
    decade: tokens.decade || (String(tokens.year_from || "").length >= 4 ? `${String(tokens.year_from).slice(0, 3)}0s` : "{decade}"),
    age_band: tokens.age_band || "{age_band}",
    sex: tokens.sex || "{sex}",
    date_window: tokens.date_window || "{date_window}",
    distinguishing_marks: tokens.distinguishing_marks || "{distinguishing_marks}",
    estimated_year_of_death: tokens.estimated_year_of_death || "{estimated_year_of_death}",
    hair: tokens.hair || "{hair}",
    height_band: tokens.height_band || "{height_band}",
    last_seen_year: tokens.last_seen_year || "{last_seen_year}",
  };
  const pairs = Object.entries(defaults).map(([k, v]) => [`{${k}}`, v]);
  const sub = (text) => {
    let out = text;
    for (const [key, val] of pairs) out = out.replaceAll(key, val);
    return out;
  };
  const families = (mode.query_families || []).map((qf) => ({
    family_id: qf.family_id,
    title: qf.title,
    event_classes: qf.event_classes,
    template: qf.template,
    rendered: sub(qf.template),
    notes: qf.notes || "",
  }));
  return {
    mode_id: mode.mode_id,
    title: mode.title,
    summary: mode.summary,
    cold_case: mode.cold_case,
    doe_match: mode.doe_match,
    archive: mode.archive,
    event_classes: mode.event_classes,
    queries: families,
    boundary:
      "Search plans only. Archive publication dates are not event dates. Doe hits are compatibility leads — never confirmed identity. Doe leads ≠ ID.",
    product: PRODUCT,
    version: VERSION,
    author: AUTHOR,
  };
}

function readTokens(src) {
  const get = (k) => {
    if (src == null) return "";
    if (typeof src.get === "function") {
      const v = src.get(k);
      return v == null ? "" : String(v);
    }
    const v = src[k];
    return v == null ? "" : String(v);
  };
  return {
    mode: get("mode") || get("mode_id"),
    name: get("name"),
    aliases: get("aliases"),
    jurisdiction: get("jurisdiction"),
    jurisdiction_or_region: get("jurisdiction_or_region"),
    year_from: get("year_from") || get("yearFrom"),
    year_to: get("year_to") || get("yearTo"),
    decade: get("decade"),
    age_band: get("age_band") || get("ageBand"),
    sex: get("sex"),
    date_window: get("date_window"),
    distinguishing_marks: get("distinguishing_marks"),
    estimated_year_of_death: get("estimated_year_of_death"),
    hair: get("hair"),
    height_band: get("height_band"),
    last_seen_year: get("last_seen_year"),
    height_cm: get("height_cm") || get("heightCm"),
    height_band: get("height_band"),
    build: get("build"),
    scars_marks: get("scars_marks") || get("distinguishing_marks"),
    clothing: get("clothing"),
    time_window_from: get("time_window_from") || get("timeFrom"),
    time_window_to: get("time_window_to") || get("timeTo"),
    subject: get("subject") || get("subject_id"),
  };
}

function openapiSpec() {
  return {
    openapi: "3.1.0",
    info: {
      title: "M.I.A.Lock runtime",
      version: VERSION,
      description:
        "Purpose-bound missing-person event map, Doe descriptor matching, coverage reports, and map-layer descriptions (uncertainty ellipses + coverage heat). Hosted map is a stub; live Leaflet map is local CLI mialock map. Doe hit ≠ ID. Coverage heat ≠ presence. " +
        MOTTO +
        " Suite mesh /v1/mesh/* PROXY to aziel-runtime (AZIEL_RUNTIME). Default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Aziel Eliab only.",
    },
    servers: [{ url: HOST }],
    paths: {
      "/v1/example": {
        get: {
          operationId: "mialockExample",
          summary: "Sample JSON payload. Does not increment downloads.",
          responses: { "200": { description: "OK" } },
        },
      },
      "/v1/skill": {
        get: {
          operationId: "mialock_skill",
          summary: "Return skill markdown. Does not increment download KV.",
          responses: { "200": { description: "markdown" } },
        },
      },
      "/v1/health": {
        get: {
          operationId: "health",
          summary: "Liveness",
          responses: { "200": { description: "ok", content: { "application/json": { schema: { type: "object" } } } } },
        },
      },
      "/v1/map": {
        get: {
          operationId: "map",
          summary: "Sample casebook index stub. Live Leaflet map is local CLI mialock map (uncertainty ellipses + coverage heat toggles; doe_cold shows lead cards). Not live tracking.",
          responses: { "200": { description: "sample index", content: { "application/json": { schema: { type: "object" } } } } },
        },
      },
      "/v1/search-options": {
        get: {
          operationId: "searchOptions",
          summary: "List archive / Doe / cold-case search modes.",
          responses: { "200": { description: "modes", content: { "application/json": { schema: { type: "object" } } } } },
        },
      },
      "/v1/queries": {
        get: {
          operationId: "queriesGet",
          summary: "Render query families for a search mode (query string). Search plans only. Doe leads ≠ ID.",
          parameters: [
            { name: "mode", in: "query", required: true, schema: { type: "string" } },
            { name: "name", in: "query", schema: { type: "string" } },
            { name: "jurisdiction", in: "query", schema: { type: "string" } },
          ],
          responses: { "200": { description: "rendered queries" } },
        },
        post: {
          operationId: "queries",
          summary: "Render query families for a search mode. Search plans only. Doe leads ≠ ID.",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  required: ["mode"],
                  properties: {
                    mode: { type: "string", enum: ["active", "archives", "doe_cold", "cold_missing"] },
                    name: { type: "string" },
                    aliases: { type: "string" },
                    jurisdiction: { type: "string" },
                    year_from: { type: "string" },
                    year_to: { type: "string" },
                    age_band: { type: "string" },
                    sex: { type: "string" },
                    height_cm: { type: "number" },
                    scars_marks: { type: "string" },
                    clothing: { type: "string" },
                  },
                },
              },
            },
          },
          responses: { "200": { description: "rendered queries", content: { "application/json": { schema: { type: "object" } } } } },
        },
      },
      "/v1/doe-match": {
        get: {
          operationId: "doeMatchGet",
          summary: "Rank Doe / unidentified notices vs a named-subject descriptor (query string). Compatibility leads only. Doe hit ≠ ID.",
          parameters: [
            { name: "age_band", in: "query", schema: { type: "string" } },
            { name: "sex", in: "query", schema: { type: "string" } },
            { name: "jurisdiction", in: "query", schema: { type: "string" } },
            { name: "height_cm", in: "query", schema: { type: "string" } },
            { name: "scars_marks", in: "query", schema: { type: "string" } },
            { name: "clothing", in: "query", schema: { type: "string" } },
            { name: "time_window_from", in: "query", schema: { type: "string" } },
            { name: "time_window_to", in: "query", schema: { type: "string" } },
          ],
          responses: { "200": { description: "ranked compatibility leads + field breakdown" } },
        },
        post: {
          operationId: "doeMatch",
          summary: "Rank Doe / unidentified notices vs a named-subject descriptor. Compatibility leads only with score and field-level match/mismatch. Never an identification.",
          requestBody: {
            required: false,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    age_band: { type: "string" },
                    sex: { type: "string" },
                    height_cm: { type: "number" },
                    height_band: { type: "string" },
                    build: { type: "string" },
                    scars_marks: { type: "string" },
                    clothing: { type: "string" },
                    jurisdiction: { type: "string" },
                    time_window_from: { type: "string" },
                    time_window_to: { type: "string" },
                    notices: { type: "array", items: { type: "object" } },
                  },
                },
              },
            },
          },
          responses: { "200": { description: "ranked compatibility leads + excluded mismatches" } },
        },
      },
      ...meshOpenApiPaths(),
      "/v1/coverage": {
        get: {
          operationId: "coverage",
          summary: "Adapter coverage report and heat cells. Heat = search coverage intensity / negative-evidence weight — not a probability of presence.",
          parameters: [
            { name: "subject", in: "query", schema: { type: "string" }, description: "Subject id (default subj-elena-cold-demo)" },
          ],
          responses: { "200": { description: "coverage report + geojson heat cells" } },
        },
      },
    },
  };
}

function aiHtml() {
  return `<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M.I.A.Lock — use with Grok, ChatGPT, Venice</title>
<style>
  :root { color-scheme: dark; }
  body { font: 16px/1.45 system-ui, sans-serif; max-width: 42rem; margin: 3rem auto; padding: 0 1.25rem; background: #0e1014; color: #e8eaef; }
  code { background: #151922; padding: .15rem .4rem; border-radius: 4px; }
  a { color: #c9d4ff; }
  .motto { color: #9aa3b2; font-style: italic; }
</style>
<body>
  <h1>M.I.A.Lock live API</h1>
  <p class="motto">${MOTTO}</p>
  <p>${LIMITATION}</p>
  <h2>ChatGPT (GPT Actions)</h2>
  <p>Paste this OpenAPI URL into GPT Actions:</p>
  <p><code>${HOST}/openapi.json</code></p>
  <h2>Grok / xAI</h2>
  <p>Custom tool pointing at <code>GET ${HOST}/v1/search-options</code>, <code>POST ${HOST}/v1/queries</code>, <code>POST ${HOST}/v1/doe-match</code>, and <code>GET ${HOST}/v1/coverage</code>.</p>
  <h2>Venice</h2>
  <p>Custom HTTP tool from the same OpenAPI URL.</p>
  <h2>MCP catalog</h2>
  <p>The shared catalog is <code>${CATALOG}/mcp</code> (catalog <code>mesh_*</code> + FragGate <code>slug=mesh</code>).</p>
  <p>Suite mesh: <code>GET ${HOST}/v1/mesh</code> PROXY to aziel-runtime. Default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Author: Aziel Eliab only.</p>
  <p>AzielTether: <a href="${TETHER}/">${TETHER}</a></p>
  <p><a href="/openapi.json">openapi.json</a> · <a href="/v1/health">health</a> · <a href="/v1/mesh">/v1/mesh</a> · <a href="/">downloads</a></p>
</body>
</html>`;
}

export async function handleRuntimeApi(request, url) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (path === "/v1/mesh" || path.startsWith("/v1/mesh/")) return null;
  const isApi =
    path === "/v1" ||
    path.startsWith("/v1/") ||
    path === "/openapi.json" ||
    path === "/ai" ||
    path.startsWith("/ai/");
  if (!isApi) return null;

  if (path === "/v1/health" && request.method === "GET") {
    return json({
      ok: true,
      author: AUTHOR,
      product: PRODUCT,
      version: VERSION,
      motto: MOTTO,
      note: "Purpose-bound missing-person investigative use. Doe leads ≠ ID. Not live tracking. Hosted /v1 does not increment downloads.",
      mesh: meshPointer(),
    });
  }

  if ((path === "/v1/example") && (request.method === "GET" || request.method === "HEAD")) {
    return json({
      ok: true,
      product: PRODUCT,
      author: AUTHOR,
      example: EXAMPLE_PAYLOAD,
      note: "Sample payload only. Does not increment downloads. Doe leads ≠ ID.",
    });
  }

  if (path === "/openapi.json" && request.method === "GET") return json(openapiSpec());
  if ((path === "/ai" || path.startsWith("/ai/")) && request.method === "GET") {
    return new Response(aiHtml(), { headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() } });
  }
  if (path === "/v1/skill" && request.method === "GET") {
    return new Response(SKILL, {
      status: 200,
      headers: { "Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "private, no-store", ...corsHeaders() },
    });
  }

  if (path === "/v1/map" && request.method === "GET") {
    return json({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      author: AUTHOR,
      hosted: true,
      local: { command: "mialock map", url: "http://127.0.0.1:8765" },
      note: "Hosted map is a sample casebook index stub. Live Leaflet map is local CLI: mialock map (127.0.0.1:8765) with uncertainty-ellipse and coverage-heat toggles; doe_cold shows descriptor-match lead cards. Historical documented events only — not live tracking. Doe hit ≠ ID. Coverage heat ≠ presence.",
      layers: {
        uncertainty_ellipses: "Semi-axes from location uncertainty / jurisdiction footprint / time-window geo soft-band. Toggle on the local map.",
        coverage_heat: COVERAGE_FRAMING,
        doe_cold_leads: "When search mode is doe_cold, the local map shows ranked compatibility lead cards with field-level match/mismatch.",
      },
      ...SAMPLE_INDEX,
    });
  }

  if (path === "/v1/search-options" && request.method === "GET") {
    return json({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      author: AUTHOR,
      modes: listModes(),
      boundary: "Search plans only. Doe leads ≠ ID. Hosted never scrapes restricted systems.",
    });
  }

  if (path === "/v1/queries" && (request.method === "GET" || request.method === "POST")) {
    let tokens;
    if (request.method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "JSON body required" }, 400);
      }
      tokens = readTokens(body || {});
    } else {
      tokens = readTokens(url.searchParams);
    }
    if (!tokens.mode) return json({ error: "mode is required (active|archives|doe_cold|cold_missing)" }, 400);
    const payload = renderQueries(tokens.mode, tokens);
    if (!payload) return json({ error: "unknown search mode", mode: tokens.mode }, 400);
    return json(payload);
  }

  if (path === "/v1/doe-match" && (request.method === "GET" || request.method === "POST")) {
    let tokens;
    if (request.method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        body = {};
      }
      tokens = readTokens(body || {});
      if (body && Array.isArray(body.notices)) tokens.notices = body.notices;
    } else {
      tokens = readTokens(url.searchParams);
    }
    const payload = hostedDoeMatch(tokens);
    payload.product = PRODUCT;
    payload.version = VERSION;
    payload.author = AUTHOR;
    return json(payload);
  }

  if (path === "/v1/coverage" && request.method === "GET") {
    const subject = url.searchParams.get("subject") || url.searchParams.get("subject_id") || "subj-elena-cold-demo";
    const cells = (SAMPLE_COVERAGE.people && SAMPLE_COVERAGE.people[subject]) || [];
    const deadEnds = cells
      .filter((c) => c.result === "zero_compatible_hits")
      .map((c) => ({
        certificate_id: c.cell_id,
        case_id: subject,
        source_id: c.source_id,
        jurisdiction: c.jurisdiction,
        event_classes: c.event_classes,
        coverage_estimate: c.coverage_estimate,
        result: "zero_compatible_hits",
      }));
    return json({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      author: AUTHOR,
      hosted: true,
      case_id: subject,
      subject_id: subject,
      framing: COVERAGE_FRAMING,
      adapters_run: cells.map((c) => ({
        source_id: c.source_id,
        jurisdiction: c.jurisdiction,
        event_classes: c.event_classes,
        coverage_estimate: c.coverage_estimate,
        result: c.result,
      })),
      dead_ends: deadEnds,
      cell_count: cells.length,
      geojson: {
        type: "FeatureCollection",
        properties: { kind: "coverage_heat", subject_id: subject, framing: COVERAGE_FRAMING },
        features: cells.map((c) => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: [c.lon, c.lat] },
          properties: { kind: "coverage_cell", ...c, framing: COVERAGE_FRAMING },
        })),
      },
      local: { command: `python -m mialock coverage --subject ${subject}` },
      note: "Hosted coverage is a sample report stub. Live heat layer is local CLI mialock map. " + COVERAGE_FRAMING,
    });
  }

  return json({ error: "not found", hint: "GET /v1/health GET /v1/skill GET /v1/map GET /v1/mesh" }, 404);
}
