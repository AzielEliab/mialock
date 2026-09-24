"""Localhost per-person event map for M.I.A.Lock.

Binds 127.0.0.1 by default. Pins show date × time × event × duration.
Basemap tiles require network; app assets are local (vendored Leaflet).
Historical documented events only — not live tracking.
"""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from mialock import __version__
from mialock.coverage import coverage_report
from mialock.doe import match_subject
from mialock.models import PersonCase, casebook_index, load_casebook
from mialock.search_options import list_search_modes, render_queries

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_DIR = Path(__file__).resolve().parent / "data"

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M.I.A.Lock Map</title>
<link rel="stylesheet" href="/static/leaflet.css">
<style>
  :root {
    color-scheme: light;
    --bg: #f7f4ee;
    --ink: #1c1915;
    --muted: #5c564c;
    --line: #e4dccb;
    --accent: #c9a227;
    --panel: #fffdf8;
    --map-bg: #e7e1d4;
    --chip: #fffdf8;
    --ok: #1f7a45;
    --soft: #8a6a10;
    --bad: #9a3030;
    --focus: #c9a227;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --bg: #12110e;
      --ink: #f3efe6;
      --muted: #c4bbaa;
      --line: #3a3428;
      --accent: #c9a227;
      --panel: #1c1a16;
      --map-bg: #0e0d0b;
      --chip: #1c1a16;
      --ok: #8fd0a8;
      --soft: #e4c56a;
      --bad: #f0a0a0;
      --focus: #c9a227;
    }
  }
  * { box-sizing: border-box; }
  html, body {
    height: 100%; margin: 0; color: var(--ink); background: var(--bg);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  body { display: grid; grid-template-rows: auto minmax(0, 1fr); min-height: 100%; }
  :focus { outline: none; }
  :focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 2px;
  }
  header {
    display: flex; flex-wrap: wrap; gap: 1rem 1.5rem; align-items: end;
    justify-content: space-between; padding: 1.1rem 1.25rem 1rem;
    border-bottom: 1px solid var(--line); background: var(--panel);
  }
  .brand { min-width: 0; flex: 1 1 16rem; }
  .brand .mark {
    font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--accent); margin: 0 0 0.3rem; font-weight: 650;
  }
  h1 { font-weight: 650; font-size: 1.55rem; margin: 0; letter-spacing: -0.01em; }
  .sub { margin: 0.4rem 0 0; color: var(--muted); font-size: 0.98rem; max-width: 40rem; line-height: 1.45; }
  .primary {
    display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: end;
    flex: 1 1 18rem; min-width: 0;
  }
  label { display: grid; gap: 0.35rem; font-size: 0.82rem; color: var(--muted); min-width: 0; }
  .primary label { flex: 1 1 12rem; }
  select, button {
    font: inherit; color: var(--ink); background: var(--panel);
    border: 1px solid var(--line); border-radius: 8px; padding: 0.6rem 0.8rem;
    max-width: 100%;
  }
  select { width: 100%; }
  button { cursor: pointer; }
  button.primary-btn {
    background: var(--accent); color: #1c1915; border-color: #a68516;
    font-weight: 650; padding: 0.65rem 1rem;
  }
  button.ghost { background: transparent; color: var(--ink); font-weight: 550; }
  .layer-toggles { display: grid; gap: 0.55rem; margin: 0.75rem 0; }
  .layer-toggles label {
    display: flex; flex-direction: row; align-items: center; gap: 0.5rem;
    font-size: 0.95rem; color: var(--ink);
  }
  main {
    display: grid;
    grid-template-columns: minmax(260px, 380px) minmax(0, 1fr);
    min-height: 0; min-width: 0;
  }
  #map { min-height: 420px; min-width: 0; background: var(--map-bg); grid-column: 2; grid-row: 1; }
  .side {
    overflow: auto; padding: 1.1rem 1.15rem 2rem; min-width: 0;
    grid-column: 1; grid-row: 1; border-right: 1px solid var(--line);
  }
  @media (max-width: 800px) {
    header { flex-direction: column; align-items: stretch; padding: 1rem; }
    .brand, .primary, .primary label { flex: none; width: 100%; }
    .primary { flex-direction: column; align-items: stretch; }
    button.primary-btn, button.ghost { width: 100%; }
    main { grid-template-columns: minmax(0, 1fr); }
    #map, .side { grid-column: 1; }
    #map { grid-row: 1; height: 46vh; min-height: 240px; }
    .side { grid-row: 2; border-right: 0; border-top: 1px solid var(--line); }
  }
  .person-head h2 { font-size: 1.25rem; margin: 0 0 0.35rem; }
  .person-head p, .status-line { margin: 0 0 0.9rem; color: var(--muted); font-size: 0.95rem; line-height: 1.45; }
  .legend { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 0 0 1rem; }
  .swatch {
    font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 999px;
    border: 1px solid var(--line); color: var(--muted); background: var(--chip);
  }
  .swatch i { display: inline-block; width: 0.55rem; height: 0.55rem;
    border-radius: 50%; margin-right: 0.3rem; vertical-align: middle; }
  .timeline { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.55rem; }
  .timeline li {
    display: grid; grid-template-columns: 4px minmax(0, 1fr); gap: 0.7rem;
    padding: 0.65rem 0.7rem; border-radius: 10px; cursor: pointer;
    background: var(--panel); border: 1px solid var(--line);
  }
  .timeline li:hover, .timeline li.active { border-color: var(--accent); }
  .timeline .rail { border-radius: 4px; background: var(--accent); }
  .timeline .when { font-variant-numeric: tabular-nums; font-size: 0.82rem; color: var(--muted); }
  .timeline .title { margin: 0.15rem 0; font-weight: 650; overflow-wrap: anywhere; }
  .timeline .meta { color: var(--muted); font-size: 0.85rem; overflow-wrap: anywhere; }
  .fold {
    margin: 1.15rem 0 0; border: 1px solid var(--line); border-radius: 10px;
    background: var(--panel); padding: 0.35rem 0.85rem 0.85rem;
  }
  .fold > summary { cursor: pointer; font-weight: 650; padding: 0.55rem 0; }
  .fold p, .note, .coverage-note { color: var(--muted); font-size: 0.92rem; line-height: 1.45; }
  .advanced .field { margin: 0.35rem 0 0.8rem; }
  .row-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .queries { margin: 0.8rem 0 0; }
  .queries h3, .leads h3 {
    font-size: 0.95rem; color: var(--ink); font-weight: 650; margin: 0.8rem 0 0.45rem;
  }
  .queries details {
    border: 1px solid var(--line); border-radius: 8px; padding: 0.45rem 0.65rem; margin: 0 0 0.45rem;
  }
  .queries summary { cursor: pointer; font-weight: 650; }
  .queries pre {
    white-space: pre-wrap; overflow-wrap: anywhere;
    font-family: ui-monospace, "SFMono-Regular", monospace;
    font-size: 0.78rem; color: var(--ink); margin: 0.45rem 0 0;
  }
  .lead-card {
    border: 1px solid var(--line); border-radius: 10px; padding: 0.7rem 0.75rem;
    margin: 0 0 0.55rem; background: var(--bg);
  }
  .lead-card .kicker { color: var(--muted); font-size: 0.78rem; letter-spacing: 0.04em; text-transform: uppercase; }
  .lead-card .title { font-weight: 650; margin: 0.2rem 0 0.35rem; overflow-wrap: anywhere; }
  .lead-card table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
  .lead-card th { text-align: left; color: var(--muted); font-weight: 550; padding: 0.15rem 0.35rem 0.15rem 0; }
  .lead-card td { padding: 0.15rem 0.35rem 0.15rem 0; overflow-wrap: anywhere; }
  .st-match { color: var(--ok); }
  .st-soft_match { color: var(--soft); }
  .st-mismatch { color: var(--bad); }
  .st-unknown { color: var(--muted); }
  .lead-card .warn-mini { color: var(--ink); font-size: 0.85rem; margin: 0.45rem 0 0; }
  .pin-popup h3 { margin: 0 0 0.35rem; font-size: 1rem; color: #1c1915; }
  .pin-popup dl { margin: 0; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 0.2rem 0.65rem; }
  .pin-popup dt { color: #5c564c; font-size: 0.75rem; }
  .pin-popup dd { margin: 0; font-size: 0.88rem; color: #1c1915; overflow-wrap: anywhere; }
  .leaflet-container { font: inherit; background: var(--map-bg); }
  .duration-halo {
    border-radius: 50%; background: rgba(201,162,39,0.18);
    border: 1px solid rgba(201,162,39,0.55);
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <p class="mark">M.I.A.Lock</p>
    <h1>Event map</h1>
    <p class="sub">See one person's documented events — date × time × event × duration.</p>
  </div>
  <div class="primary">
    <label>Person
      <select id="person"></select>
    </label>
    <button type="button" class="primary-btn" id="show">Show events</button>
  </div>
</header>
<main>
  <div id="map" role="application" aria-label="Subject event map"></div>
  <aside class="side">
    <div class="person-head">
      <h2 id="personName">Choose a person</h2>
      <p id="personSummary">Pick a name, then show their events.</p>
    </div>
    <p class="status-line" id="modeFlags"></p>
    <div class="legend" id="legend"></div>
    <ol class="timeline" id="timeline"></ol>
    <details class="fold">
      <summary>About</summary>
      <p>Each pin is a documented event: date × time × event × duration.</p>
      <p>Doe results are compatibility leads. Check the source record before you treat a notice as the person.</p>
      <p>Coverage color shows how thoroughly a source was searched.</p>
      <p>Author: Aziel Eliab</p>
    </details>
    <details class="fold advanced">
      <summary>Advanced</summary>
      <label class="field">Search mode
        <select id="mode">
          <option value="all">All events</option>
        </select>
      </label>
      <div class="layer-toggles">
        <label><input type="checkbox" id="ellipses" checked> Uncertainty ellipses</label>
        <label><input type="checkbox" id="heat" checked> Coverage heat</label>
      </div>
      <p class="coverage-note" id="coverageNote"></p>
      <div class="row-actions">
        <button type="button" class="ghost" id="fit">Fit pins</button>
        <button type="button" class="ghost" id="reload">Reload</button>
      </div>
      <div class="leads" id="doeLeads"></div>
      <div class="queries" id="queries"></div>
    </details>
  </aside>
</main>

<script src="/static/leaflet.js"></script>
<script>
const EVENT_COLORS = {
  missing_person_notice: "#c4a35a",
  missing_person_update: "#c4a35a",
  cold_case_missing: "#b8923f",
  booking: "#3d9b84",
  arrest: "#2f8f9a",
  custody: "#267a6c",
  release: "#5aa88a",
  hearing: "#6b8cce",
  court_filing: "#5b7ab8",
  charge: "#5b7ab8",
  disposition: "#4a6aa0",
  incarceration: "#3a6e62",
  crime_incident: "#b8744a",
  homicide_victim: "#b04a4a",
  homicide_suspect_mention: "#8a3d3d",
  obituary: "#8b7a9e",
  death_notice: "#8b7a9e",
  funeral_notice: "#8b7a9e",
  archive_obituary: "#7a6a8e",
  news_crime_report: "#a0895a",
  discovery_lead: "#7a8790",
  unidentified_remains: "#9a6b6b",
  jane_doe_notice: "#d08a9a",
  john_doe_notice: "#8a9ad0",
  cold_case_unidentified: "#a67c7c",
  newspaper_archive_hit: "#c4b07a",
  archive_missing_report: "#b8a56e",
  archive_crime_report: "#a89460",
  historical_publication: "#9a8b6a",
  periodical_clipping: "#8f8060",
  library_digital_collection: "#7e7358",
  news_identification: "#b09070"
};

const map = L.map("map", { zoomControl: true, attributionControl: true });
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap"
}).addTo(map);
map.setView([41.88, -87.63], 9);

let coverageLayer = L.layerGroup().addTo(map);
let ellipseLayer = L.layerGroup().addTo(map);
let pathLayer = L.layerGroup().addTo(map);
let layer = L.layerGroup().addTo(map);
let currentFeatures = [];
let coverageFeatures = [];

function colorFor(event) {
  return EVENT_COLORS[event] || "#c4a35a";
}

function durationRadius(seconds) {
  if (!seconds || seconds <= 0) return 18;
  const hours = seconds / 3600;
  return Math.min(90, 18 + Math.sqrt(hours) * 14);
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function renderLegend(events) {
  const root = document.getElementById("legend");
  root.innerHTML = "";
  [...new Set(events)].forEach(ev => {
    const el = document.createElement("span");
    el.className = "swatch";
    el.innerHTML = `<i style="background:${colorFor(ev)}"></i>${ev}`;
    root.appendChild(el);
  });
}

function popupHtml(p) {
  return `<div class="pin-popup">
    <h3>${p.label || p.event}</h3>
    <dl>
      <dt>Date</dt><dd>${p.date}</dd>
      <dt>Time</dt><dd>${p.time}</dd>
      <dt>Event</dt><dd>${p.event}</dd>
      <dt>Duration</dt><dd>${p.duration_label}</dd>
      <dt>Place</dt><dd>${p.place_name || "—"}</dd>
      <dt>Geo conf.</dt><dd>${Math.round((p.geo_confidence || 0) * 100)}%</dd>
      <dt>State</dt><dd>${p.verification_state}</dd>
    </dl>
  </div>`;
}

function focusPin(pinId) {
  const feat = currentFeatures.find(f => f.properties && f.properties.pin_id === pinId);
  if (!feat || !feat.geometry || feat.geometry.type !== "Point") return;
  const [lon, lat] = feat.geometry.coordinates;
  map.flyTo([lat, lon], Math.max(map.getZoom(), 12), { duration: 0.7 });
  document.querySelectorAll(".timeline li").forEach(li => {
    li.classList.toggle("active", li.dataset.pinId === pinId);
  });
}

function renderTimeline(features) {
  const root = document.getElementById("timeline");
  root.innerHTML = "";
  features
    .filter(f => f.geometry && f.geometry.type === "Point")
    .sort((a, b) => (a.properties.start_at || "").localeCompare(b.properties.start_at || ""))
    .forEach(f => {
      const p = f.properties;
      const li = document.createElement("li");
      li.dataset.pinId = p.pin_id;
      li.innerHTML = `
        <div class="rail" style="background:${colorFor(p.event)}"></div>
        <div>
          <div class="when">${p.date} · ${p.time}</div>
          <div class="title">${p.label || p.event}</div>
          <div class="meta">${p.event} · ${p.duration_label}${p.place_name ? " · " + p.place_name : ""}</div>
        </div>`;
      li.tabIndex = 0;
      const open = () => focusPin(p.pin_id);
      li.addEventListener("click", open);
      li.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          open();
        }
      });
      root.appendChild(li);
    });
}

function coverageColor(result, intensity) {
  const i = Math.max(0, Math.min(1, intensity || 0));
  if (result === "zero_compatible_hits") return `rgba(110, 140, 180, ${0.18 + i * 0.42})`;
  if (result === "low_coverage") return `rgba(196, 163, 90, ${0.12 + i * 0.28})`;
  if (result === "failed" || result === "access_denied") return `rgba(180, 90, 90, ${0.1 + i * 0.2})`;
  return `rgba(61, 155, 132, ${0.16 + i * 0.45})`;
}

function drawCoverage(geojson) {
  coverageLayer.clearLayers();
  coverageFeatures = (geojson && geojson.features) || [];
  const framing = (geojson && geojson.properties && geojson.properties.framing) ||
    "Heat = search coverage intensity / negative-evidence weight — not a probability of presence.";
  document.getElementById("coverageNote").textContent = framing;
  coverageFeatures.forEach(f => {
    if (!f.geometry || f.geometry.type !== "Point") return;
    const p = f.properties || {};
    const [lon, lat] = f.geometry.coordinates;
    const stroke = (p.result === "zero_compatible_hits") ? "#6e8cb4"
      : (p.result === "low_coverage") ? "#c4a35a"
      : (p.result === "failed" || p.result === "access_denied") ? "#b45a5a"
      : "#3d9b84";
    L.circle([lat, lon], {
      radius: p.radius_m || 8000,
      color: stroke,
      weight: 1,
      fillColor: stroke,
      fillOpacity: 0.16 + 0.38 * (p.intensity || 0),
      className: "coverage-heat"
    }).bindTooltip(
      `${p.source_id || "adapter"} · ${p.result || "searched"} · coverage ${Math.round((p.intensity || 0) * 100)}% — not presence`
    ).addTo(coverageLayer);
  });
  applyLayerToggles();
}

function drawPerson(geojson) {
  layer.clearLayers();
  pathLayer.clearLayers();
  ellipseLayer.clearLayers();
  currentFeatures = geojson.features || [];
  const props = geojson.properties || {};
  document.getElementById("personName").textContent = props.display_name || props.subject_id || "—";
  document.getElementById("personSummary").textContent = props.summary || "";

  const points = [];
  const events = [];

  currentFeatures.forEach(f => {
    const kind = (f.properties && f.properties.kind) || "";
    if (f.geometry && f.geometry.type === "Polygon" && kind === "uncertainty_ellipse") {
      const ring = (f.geometry.coordinates[0] || []).map(([lon, lat]) => [lat, lon]);
      const p = f.properties || {};
      L.polygon(ring, {
        color: "#c4a35a",
        weight: 1.2,
        dashArray: "4 6",
        fillColor: "#c4a35a",
        fillOpacity: 0.08,
        className: "uncertainty-ellipse"
      }).bindTooltip(
        `Uncertainty ellipse ${Math.round(p.semi_major_m || 0)}×${Math.round(p.semi_minor_m || 0)} m — not live location`
      ).addTo(ellipseLayer);
      return;
    }
    if (f.geometry && f.geometry.type === "LineString") {
      const latlngs = f.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
      L.polyline(latlngs, {
        color: "#3d9b84",
        weight: 2,
        opacity: 0.75,
        dashArray: "6 8"
      }).bindTooltip("Documented event order — not inferred travel")
        .addTo(pathLayer);
      return;
    }
    if (!f.geometry || f.geometry.type !== "Point") return;
    if (kind === "coverage_cell") return;
    const p = f.properties;
    events.push(p.event);
    const [lon, lat] = f.geometry.coordinates;
    points.push([lat, lon]);

    const halo = L.circleMarker([lat, lon], {
      radius: durationRadius(p.duration_seconds),
      className: "duration-halo",
      color: colorFor(p.event),
      weight: 1,
      fillColor: colorFor(p.event),
      fillOpacity: 0.12
    }).addTo(layer);

    const marker = L.circleMarker([lat, lon], {
      radius: 7,
      color: "#0c1714",
      weight: 2,
      fillColor: colorFor(p.event),
      fillOpacity: 1
    }).bindPopup(popupHtml(p)).addTo(layer);

    marker.on("click", () => focusPin(p.pin_id));
    halo.bindTooltip(`${p.date} ${p.time} · ${p.event} · ${p.duration_label}`);
  });

  renderLegend(events);
  renderTimeline(currentFeatures.filter(f => f.geometry && f.geometry.type === "Point" && (f.properties || {}).kind !== "coverage_cell"));
  applyLayerToggles();
  if (points.length) {
    map.fitBounds(points, { padding: [36, 36], maxZoom: 12 });
  }
  setTimeout(() => map.invalidateSize(), 0);
}

function applyLayerToggles() {
  const showEllipses = document.getElementById("ellipses").checked;
  const showHeat = document.getElementById("heat").checked;
  if (showEllipses) {
    if (!map.hasLayer(ellipseLayer)) map.addLayer(ellipseLayer);
  } else if (map.hasLayer(ellipseLayer)) {
    map.removeLayer(ellipseLayer);
  }
  if (showHeat) {
    if (!map.hasLayer(coverageLayer)) map.addLayer(coverageLayer);
  } else if (map.hasLayer(coverageLayer)) {
    map.removeLayer(coverageLayer);
  }
}

function renderDoeLeads(payload) {
  const root = document.getElementById("doeLeads");
  if (!payload || !payload.leads || !payload.leads.length) {
    root.innerHTML = payload && payload.doe_match === false ? "" :
      (payload && payload.mode_hidden ? "" : "");
    if (payload && payload.leads && payload.leads.length === 0) {
      root.innerHTML = `<h3>Doe compatibility leads</h3><p class="note">No leads to list for this search. Check the source record before you treat a notice as the person.</p>`;
    }
    return;
  }
  const cards = payload.leads.map(lead => {
    const rows = (lead.fields || []).map(f => `
      <tr>
        <th>${f.field}</th>
        <td class="st-${f.status}">${f.status}</td>
        <td>${f.subject || "—"} → ${f.notice || "—"}</td>
      </tr>`).join("");
    return `<article class="lead-card" data-notice="${lead.notice_id || ""}">
      <div class="kicker">Compatibility lead</div>
      <div class="title">${lead.label || lead.notice_id}</div>
      <div class="meta">${lead.event_class || ""} · ${lead.jurisdiction || ""}</div>
      <table>${rows}</table>
      <p class="note">${lead.next_verification || ""}</p>
      <p class="warn-mini">Check this lead against the source record before you treat it as the person.</p>
    </article>`;
  }).join("");
  root.innerHTML = `<h3>Doe compatibility leads</h3>
    <p class="note">Check each lead against the source record before you treat it as the person.</p>
    ${cards}`;
  root.querySelectorAll(".lead-card").forEach(card => {
    card.style.cursor = "pointer";
    card.addEventListener("click", () => {
      const id = card.dataset.notice;
      const feat = currentFeatures.find(f => f.properties && f.properties.pin_id === id);
      if (feat && feat.geometry && feat.geometry.type === "Point") {
        focusPin(id);
      }
    });
  });
}

async function loadModes() {
  const data = await fetchJSON("/api/search-options");
  const select = document.getElementById("mode");
  const keep = select.value || "all";
  select.innerHTML = '<option value="all">All pins</option>';
  (data.modes || []).forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.mode_id;
    const tags = [
      m.archive ? "archives" : null,
      m.doe_match ? "Doe" : null,
      m.cold_case ? "cold" : null
    ].filter(Boolean).join(", ");
    opt.textContent = tags ? `${m.title} (${tags})` : m.title;
    select.appendChild(opt);
  });
  select.value = [...select.options].some(o => o.value === keep) ? keep : "all";
}

function renderModeFlags(payload) {
  const root = document.getElementById("modeFlags");
  if (!payload || !payload.mode_id || payload.mode_id === "all") {
    root.textContent = "Showing every documented event for this person.";
    return;
  }
  const title = payload.title || payload.mode_id;
  root.textContent = payload.summary ? `${title}. ${payload.summary}` : title;
}

function renderQueries(payload) {
  const root = document.getElementById("queries");
  if (!payload || !payload.queries || !payload.queries.length) {
    root.innerHTML = "";
    return;
  }
  const items = payload.queries.map(q => `
    <details>
      <summary>${q.title}</summary>
      <pre>${q.rendered || q.template}</pre>
      ${q.notes ? `<p class="note">${q.notes}</p>` : ""}
    </details>`).join("");
  root.innerHTML = `<h3>${payload.title || "Search plans"}</h3>${items}
    <p class="note">These are search plans to run yourself.</p>`;
}

async function loadPeople() {
  await loadModes();
  const data = await fetchJSON("/api/people");
  const select = document.getElementById("person");
  select.innerHTML = "";
  data.people.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.subject_id;
    let kind = "";
    if (p.case_kind === "cold_missing") kind = " · cold case";
    else if (p.case_kind && p.case_kind !== "active") kind = " · " + String(p.case_kind).replaceAll("_", " ");
    opt.textContent = `${p.display_name} · ${p.pin_count} events${kind}`;
    select.appendChild(opt);
  });
  if (data.people.length) {
    select.value = data.people[0].subject_id;
    await loadSelected();
  }
}

async function loadSelected() {
  const id = document.getElementById("person").value;
  if (!id) {
    document.getElementById("personSummary").textContent = "Pick a name, then show their events.";
    return;
  }
  const mode = document.getElementById("mode").value || "all";
  try {
  const geojson = await fetchJSON(
    `/api/people/${encodeURIComponent(id)}/geojson?mode=${encodeURIComponent(mode)}`
  );
  drawPerson(geojson);
  try {
    const cov = await fetchJSON(`/api/people/${encodeURIComponent(id)}/coverage`);
    drawCoverage(cov.geojson || cov);
  } catch (err) {
    coverageLayer.clearLayers();
    document.getElementById("coverageNote").textContent =
      "Heat = search coverage intensity / negative-evidence weight — not a probability of presence.";
  }
  if (mode === "all") {
    renderModeFlags({ mode_id: "all" });
    renderQueries(null);
    document.getElementById("doeLeads").innerHTML = "";
  } else {
    const q = await fetchJSON(
      `/api/people/${encodeURIComponent(id)}/queries?mode=${encodeURIComponent(mode)}`
    );
    renderModeFlags(q);
    renderQueries(q);
    if (mode === "doe_cold" || mode === "cold_missing") {
      const leads = await fetchJSON(
        `/api/people/${encodeURIComponent(id)}/doe-match`
      );
      renderDoeLeads(leads);
    } else {
      document.getElementById("doeLeads").innerHTML = "";
    }
  }
  } catch (err) {
    document.getElementById("personSummary").textContent =
      "Could not show events for this person. Choose another name, or open Advanced and use Reload.";
  }
}

document.getElementById("person").addEventListener("change", loadSelected);
document.getElementById("show").addEventListener("click", loadSelected);
document.getElementById("mode").addEventListener("change", loadSelected);
document.getElementById("ellipses").addEventListener("change", applyLayerToggles);
document.getElementById("heat").addEventListener("change", applyLayerToggles);
document.getElementById("fit").addEventListener("click", () => {
  const pts = currentFeatures
    .filter(f => f.geometry && f.geometry.type === "Point")
    .map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0]]);
  if (pts.length) map.fitBounds(pts, { padding: [36, 36], maxZoom: 12 });
});
document.getElementById("reload").addEventListener("click", loadPeople);

loadPeople().catch(() => {
  document.getElementById("personSummary").textContent =
    "Could not load the casebook. Check the file, then use Reload under Advanced.";
});
</script>
</body>
</html>
"""


class MapState:
    def __init__(self, casebook_path: Path | None = None) -> None:
        self.casebook_path = casebook_path or (DATA_DIR / "sample_persons.json")
        self.cases: dict[str, PersonCase] = {}
        self.reload()

    def reload(self) -> None:
        loaded = load_casebook(self.casebook_path)
        self.cases = {c.subject_id: c for c in loaded}


def make_handler(state: MapState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, payload: Any) -> None:
            raw = json.dumps(payload, indent=2).encode("utf-8")
            self._send(code, raw, "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path

            if path in {"/", "/map"}:
                if _wants_json(self.headers.get("Accept", "")):
                    self._json(
                        200,
                        {
                            "product": "mialock",
                            "version": __version__,
                            "author": "Aziel Eliab",
                            "ui": path,
                        },
                    )
                    return
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return

            if path.startswith("/static/"):
                rel = path[len("/static/") :]
                target = (STATIC_DIR / rel).resolve()
                if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
                    self._send(404, b"not found", "text/plain")
                    return
                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                self._send(200, target.read_bytes(), ctype)
                return

            if path == "/api/people":
                self._json(200, casebook_index(state.cases.values()))
                return

            if path == "/api/search-options":
                self._json(
                    200,
                    {
                        "boundary": (
                            "Archive publication dates are not event dates. "
                            "Doe hits are compatibility leads — never confirmed identity."
                        ),
                        "modes": list_search_modes(),
                    },
                )
                return

            if path.startswith("/api/people/") and path.endswith("/geojson"):
                subject_id = path[len("/api/people/") : -len("/geojson")]
                case = state.cases.get(subject_id)
                if case is None:
                    self._json(404, {"error": "unknown subject"})
                    return
                mode = parse_qs(parsed.query).get("mode", ["all"])[0]
                self._json(200, case.to_geojson(mode))
                return

            if path.startswith("/api/people/") and path.endswith("/queries"):
                subject_id = path[len("/api/people/") : -len("/queries")]
                case = state.cases.get(subject_id)
                if case is None:
                    self._json(404, {"error": "unknown subject"})
                    return
                mode = parse_qs(parsed.query).get("mode", ["active"])[0]
                if mode == "all":
                    self._json(200, {"mode_id": "all", "queries": []})
                    return
                name = case.display_name.split("(")[0].strip()
                desc = case.descriptor or {}
                payload = render_queries(
                    mode,
                    name=name,
                    aliases=name,
                    jurisdiction=desc.get("jurisdiction")
                    or (case.pins[0].jurisdiction if case.pins else "US"),
                    age_band=str(desc.get("age_band") or "20-30"),
                    sex=str(desc.get("sex") or ""),
                    year_from=str(desc.get("time_window_from") or "1990")[:4],
                    year_to=str(desc.get("time_window_to") or "1999")[:4],
                    distinguishing_marks=str(desc.get("scars_marks") or ""),
                    height_band=str(desc.get("height_band") or desc.get("height_cm") or ""),
                )
                self._json(200, payload)
                return

            if path.startswith("/api/people/") and path.endswith("/doe-match"):
                subject_id = path[len("/api/people/") : -len("/doe-match")]
                case = state.cases.get(subject_id)
                if case is None:
                    self._json(404, {"error": "unknown subject"})
                    return
                self._json(200, match_subject(case))
                return

            if path.startswith("/api/people/") and path.endswith("/coverage"):
                subject_id = path[len("/api/people/") : -len("/coverage")]
                case = state.cases.get(subject_id)
                if case is None:
                    self._json(404, {"error": "unknown subject"})
                    return
                self._json(200, coverage_report(case))
                return

            if path.startswith("/api/people/") and path.endswith("/pins"):
                subject_id = path[len("/api/people/") : -len("/pins")]
                case = state.cases.get(subject_id)
                if case is None:
                    self._json(404, {"error": "unknown subject"})
                    return
                self._json(200, case.to_dict())
                return

            if path == "/api/reload":
                qs = parse_qs(parsed.query)
                if "path" in qs:
                    state.casebook_path = Path(qs["path"][0])
                state.reload()
                self._json(200, casebook_index(state.cases.values()))
                return

            self._send(404, b"not found", "text/plain")

    return Handler


def _wants_json(accept: str) -> bool:
    parts = [part.split(";")[0].strip().lower() for part in (accept or "").split(",") if part.strip()]
    if not parts:
        return False
    if parts[0] == "application/json":
        return True
    return "application/json" in parts and "text/html" not in parts


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, casebook: Path | None = None) -> None:
    state = MapState(casebook)
    handler = make_handler(state)
    httpd = ThreadingHTTPServer((host, port), handler)
    shown = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"Open http://{shown}:{port}/", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
