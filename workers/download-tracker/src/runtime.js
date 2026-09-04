/**
 * M.I.A.Lock hosted runtime.
 * Hosted /v1 never touches DOWNLOADS KV.
 * Map / search-options / queries are hosted stubs. Live Leaflet map is local CLI.
 * Author: Aziel Eliab.
 */
import SEARCH_MODES from "./search-modes.json";
import SAMPLE_INDEX from "./sample-index.json";

const PRODUCT = "mialock";
const VERSION = "0.1.0";
const AUTHOR = "Aziel Eliab";
const MOTTO =
  "Search broadly. Match probabilistically. Challenge every hit. Preserve provenance. Verify before action.";
const HOST = "https://mialock-download-tracker.vibelock.workers.dev";
const CATALOG = "https://aziel-runtime.vibelock.workers.dev";
const TETHER = "https://azieltether-download-tracker.vibelock.workers.dev";
const LIMITATION =
  "THIS IS: purpose-bound missing-person investigative software — per-person historical event maps (date × time × event × duration) plus archive / Doe cold-case search options. THIS IS NOT: live location tracking, an identification, a crawler of restricted law-enforcement systems, or automated accusation. Doe leads ≠ ID. Author Aziel Eliab.";

const EXAMPLE_PAYLOAD = {
  mode: "doe_cold",
  name: "Christina Green",
  aliases: '"Christy Green" OR "Tina Green"',
  jurisdiction: "Illinois",
  year_from: "1990",
  year_to: "1999",
  age_band: "20-30",
  sex: "female",
};

const SKILL = `---
name: M.I.A.Lock
description: Use when mapping documented missing-person events (date × time × event × duration) or listing archive/Doe cold-case search options. Purpose-bound investigative use. Doe leads ≠ ID. Hosted /v1 via this Worker or aziel-runtime. Author Aziel Eliab.
---

# M.I.A.Lock

**Missing Individual Autonomous Lock.** Per-person historical event map plus archive / Doe cold-case search options.

Author: **Aziel Eliab**.

**THIS IS:** purpose-bound missing-person investigative software — documented historical pins (date × time × event × duration) and search *plans*.

**THIS IS NOT:** live location tracking, an identification, a crawler of restricted law-enforcement systems, or automated accusation. Doe leads ≠ ID. Hosted \`/v1\` does not increment downloads.

Always send \`User-Agent: Mozilla/5.0\`. Cloudflare Workers may 403 an empty agent.

## Endpoints (this Worker)

Host: \`https://mialock-download-tracker.vibelock.workers.dev\`

| Method | Path | What |
|--------|------|------|
| GET | \`/v1/health\` | Liveness. Does not increment downloads. |
| GET | \`/v1/skill\` | This markdown. Does not increment downloads. |
| GET | \`/v1/example\` | Sample query payload. Does not increment downloads. |
| GET | \`/v1/map\` | Sample casebook index stub. Live Leaflet map is local CLI \`mialock map\`. |
| GET | \`/v1/search-options\` | List archive / Doe / cold-case search modes. |
| GET/POST | \`/v1/queries\` | Render query families for a mode. Search plans only. Doe leads ≠ ID. |

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
  -d '{"mode":"doe_cold","name":"Christina Green","jurisdiction":"Illinois","age_band":"20-30","sex":"female"}'
curl -s -A 'Mozilla/5.0' https://mialock-download-tracker.vibelock.workers.dev/v1/skill
\`\`\`

Grok: import the catalog OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.

## Local (after one-click install)

\`\`\`bash
curl -fsSL https://mialock-download-tracker.vibelock.workers.dev/install.sh | bash
mialock map
\`\`\`

Then open http://127.0.0.1:8765 (this computer only). The live map is local. Hosted \`/v1/map\` is a sample index stub.

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
- AzielTether: https://azieltether-download-tracker.vibelock.workers.dev/v1/skill

Counted download (gzip HTTP 200, no 302): https://mialock-download-tracker.vibelock.workers.dev/download?asset=mialock-0.1.0.tar.gz
GitHub: https://github.com/AzielEliab/mialock
`;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, mcp-session-id",
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
  };
}

function openapiSpec() {
  return {
    openapi: "3.1.0",
    info: {
      title: "M.I.A.Lock runtime",
      version: VERSION,
      description:
        "Purpose-bound missing-person event map and archive/Doe search options. Hosted map is a stub; live Leaflet map is local CLI mialock map. Doe leads ≠ ID. " +
        MOTTO,
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
          summary: "Sample casebook index stub. Live Leaflet map is local CLI mialock map. Not live tracking.",
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
                  },
                },
              },
            },
          },
          responses: { "200": { description: "rendered queries", content: { "application/json": { schema: { type: "object" } } } } },
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
  <p>Custom tool pointing at <code>GET ${HOST}/v1/search-options</code> and <code>POST ${HOST}/v1/queries</code>.</p>
  <h2>Venice</h2>
  <p>Custom HTTP tool from the same OpenAPI URL.</p>
  <h2>MCP catalog</h2>
  <p>The shared catalog is <code>${CATALOG}/mcp</code>.</p>
  <p>AzielTether: <a href="${TETHER}/">${TETHER}</a></p>
  <p><a href="/openapi.json">openapi.json</a> · <a href="/v1/health">health</a> · <a href="/">downloads</a></p>
</body>
</html>`;
}

export async function handleRuntimeApi(request, url) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
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
      note: "Hosted map is a sample casebook index stub. Live Leaflet map is local CLI: mialock map (127.0.0.1:8765). Historical documented events only — not live tracking. Doe leads ≠ ID.",
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

  return json({ error: "not found" }, 404);
}
