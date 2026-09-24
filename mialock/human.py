"""Plain-language views of M.I.A.Lock results.

Machine JSON stays on the ``--json`` path. This module only formats text
a person reads. It does not add fields the payloads do not already have.
"""

from __future__ import annotations

from typing import Any


def _kind(kind: str) -> str:
    labels = {
        "active": "Active case",
        "cold_missing": "Cold case",
    }
    if kind in labels:
        return labels[kind]
    return kind.replace("_", " ")


def _join(lines: list[str]) -> str:
    text = "\n".join(lines).rstrip()
    return text + "\n"


def format_people(payload: dict[str, Any]) -> str:
    people = list(payload.get("people") or [])
    noun = "person" if len(people) == 1 else "people"
    lines = [f"{len(people)} {noun} in this casebook", ""]
    if not people:
        lines.append("This casebook has no people yet.")
        lines.append("")
        lines.append("Next: mialock ui --casebook path/to/casebook.json")
        return _join(lines)
    for person in people:
        name = person.get("display_name") or person.get("subject_id") or "Person"
        lines.append(str(name))
        lines.append(
            f"  {_kind(str(person.get('case_kind') or 'active'))} · "
            f"{person.get('pin_count', 0)} events"
        )
        summary = str(person.get("summary") or "").strip()
        if summary:
            lines.append(f"  {summary}")
        lines.append(f"  id {person.get('subject_id')}")
        lines.append("")
    lines.append("Next: mialock ui")
    return _join(lines)


def format_modes(payload: dict[str, Any]) -> str:
    modes = list(payload.get("modes") or [])
    lines = ["Search modes", ""]
    if not modes:
        lines.append("No search modes are packaged.")
        lines.append("")
        lines.append("Next: mialock --help")
        return _join(lines)
    for mode in modes:
        lines.append(str(mode.get("mode_id") or ""))
        title = str(mode.get("title") or "").strip()
        if title:
            lines.append(f"  {title}")
        summary = str(mode.get("summary") or "").strip()
        if summary:
            lines.append(f"  {summary}")
        lines.append("")
    lines.append("Next: mialock queries <mode>")
    return _join(lines)


def format_queries(payload: dict[str, Any]) -> str:
    title = str(payload.get("title") or payload.get("mode_id") or "Search plans")
    lines = [title, ""]
    summary = str(payload.get("summary") or "").strip()
    if summary:
        lines.append(summary)
        lines.append("")
    queries = list(payload.get("queries") or [])
    if not queries:
        lines.append("This mode has no query text to show.")
    for query in queries:
        lines.append(str(query.get("title") or query.get("family_id") or "Query"))
        rendered = str(query.get("rendered") or query.get("template") or "").strip()
        if rendered:
            lines.append(f"  {rendered}")
        notes = str(query.get("notes") or "").strip()
        if notes:
            lines.append(f"  {notes}")
        lines.append("")
    lines.append(
        "These are search plans to run yourself. "
        "A Doe line is a compatibility lead to verify with the source record."
    )
    lines.append("Next: mialock ui")
    return _join(lines)


def _field_line(field: dict[str, Any]) -> str:
    name = field.get("field") or "field"
    status = field.get("status") or "unknown"
    subject = field.get("subject") or "—"
    notice = field.get("notice") or "—"
    return f"   {name}: {status} ({subject} → {notice})"


def format_doe(payload: dict[str, Any]) -> str:
    name = str(payload.get("display_name") or "Descriptor")
    leads = list(payload.get("leads") or [])
    lines = [name, ""]
    count = len(leads)
    if count == 0:
        lines.append("No compatibility leads to list.")
    elif count == 1:
        lines.append(
            "1 compatibility lead. Check it against the source record "
            "before you treat it as the person."
        )
    else:
        lines.append(
            f"{count} compatibility leads. Check each one against the source "
            "record before you treat it as the person."
        )
    lines.append("")
    for index, lead in enumerate(leads, start=1):
        label = lead.get("label") or lead.get("notice_id") or "Notice"
        lines.append(f"{index}. {label}")
        bits = [bit for bit in (lead.get("event_class"), lead.get("jurisdiction")) if bit]
        if bits:
            lines.append("   " + " · ".join(str(bit) for bit in bits))
        for field in lead.get("fields") or []:
            if isinstance(field, dict):
                lines.append(_field_line(field))
        nxt = str(lead.get("next_verification") or "").strip()
        if nxt:
            lines.append(f"   Next check: {nxt}")
        lines.append("")
    excluded = list(payload.get("excluded") or [])
    if excluded:
        reasons: list[str] = []
        if any(row.get("reason") == "sex_mismatch" for row in excluded):
            reasons.append("sex did not match")
        if any(row.get("reason") == "below_lead_threshold" for row in excluded):
            reasons.append("not enough agreement to list as a lead")
        known = {"sex_mismatch", "below_lead_threshold"}
        extra = sorted(
            {
                str(row.get("reason"))
                for row in excluded
                if row.get("reason") and str(row.get("reason")) not in known
            }
        )
        reasons.extend(extra)
        why = "; ".join(reasons) if reasons else "they did not qualify as leads"
        lines.append(f"{len(excluded)} notices were set aside ({why}).")
        lines.append("")
    lines.append("Next: mialock ui")
    return _join(lines)


def _coverage_rows(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    adapters = list(report.get("adapters_run") or [])
    if not adapters:
        lines.append("No coverage rows for this person.")
        return lines
    for row in adapters:
        estimate = row.get("coverage_estimate")
        estimate_text = "—" if estimate is None else str(estimate)
        lines.append(
            f"  {row.get('source_id') or 'source'} · "
            f"{row.get('jurisdiction') or '—'} · "
            f"{row.get('result') or 'searched'} · "
            f"coverage {estimate_text}"
        )
    dead = list(report.get("dead_ends") or [])
    if dead:
        lines.append("")
        lines.append("Dead-end certificates (zero compatible hits):")
        for row in dead:
            lines.append(
                f"  {row.get('source_id') or 'source'} · {row.get('jurisdiction') or '—'}"
            )
    low = list(report.get("low_coverage_sources") or [])
    if low:
        lines.append("")
        lines.append("Low coverage: " + ", ".join(str(item) for item in low))
    failed = list(report.get("failed_or_denied") or [])
    if failed:
        lines.append("")
        lines.append("Failed or access denied:")
        for row in failed:
            if isinstance(row, dict):
                lines.append(f"  {row.get('source_id') or 'source'} · {row.get('result') or 'failed'}")
            else:
                lines.append(f"  {row}")
    return lines


def format_coverage(payload: dict[str, Any]) -> str:
    if "reports" in payload and "adapters_run" not in payload:
        lines = [
            "Search coverage",
            "",
            "Each row is how thoroughly a source was searched.",
            "",
        ]
        reports = list(payload.get("reports") or [])
        if not reports:
            lines.append("No coverage reports in this casebook.")
        for report in reports:
            name = report.get("display_name") or report.get("subject_id") or "Person"
            lines.append(
                f"{name} · {report.get('cell_count', 0)} rows · "
                f"{len(report.get('dead_ends') or [])} dead-end certificates"
            )
        lines.append("")
        lines.append("Next: mialock coverage --subject <id>")
        return _join(lines)
    name = str(payload.get("display_name") or payload.get("subject_id") or "Coverage")
    lines = [
        name,
        "",
        "This lists sources that were searched. "
        "The coverage amount describes the search, not whether the person was there.",
        "",
    ]
    lines.extend(_coverage_rows(payload))
    lines.append("")
    lines.append("Next: mialock ui")
    return _join(lines)


def format_geojson(payload: dict[str, Any]) -> str:
    props = payload.get("properties") or {}
    features = list(payload.get("features") or [])
    points = 0
    ellipses = 0
    heat = 0
    for feature in features:
        kind = str((feature.get("properties") or {}).get("kind") or "")
        geometry = (feature.get("geometry") or {}).get("type")
        if kind == "uncertainty_ellipse":
            ellipses += 1
        elif kind == "coverage_cell":
            heat += 1
        elif geometry == "Point":
            points += 1
    name = str(props.get("display_name") or props.get("subject_id") or "Person")
    subject_id = str(props.get("subject_id") or "")
    mode = str(props.get("search_mode") or "all")
    lines = [
        name,
        f"{points} event pins · {ellipses} uncertainty ellipses · mode {mode}",
    ]
    if heat:
        lines.append(f"{heat} coverage cells included")
    lines.append("")
    if subject_id:
        lines.append(f"Next: mialock geojson {subject_id} --json")
    else:
        lines.append("Next: mialock geojson <id> --json")
    lines.append("or:  mialock ui")
    return _join(lines)
