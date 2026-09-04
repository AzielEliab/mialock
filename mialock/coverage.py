"""Adapter coverage reports and map heat cells.

Whitepaper §11.1 / source-catalog §7: a coverage map is the union of adapter
coverage actually exercised plus dead-end certificates for zero-hit runs.

Heat intensity is **search coverage / negative-evidence weight** — never a
probability that the missing person is present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from mialock.models import DATA_DIR, PersonCase

FRAMING = (
    "Heat = search coverage intensity / negative-evidence weight — "
    "not a probability of presence."
)

_RESULT_NOTE = {
    "searched": "Adapter ran and returned a searchable corpus in this footprint.",
    "zero_compatible_hits": (
        "Dead-end certificate: coverage was high enough that zero compatible "
        "hits is informative negative evidence — not proof of absence."
    ),
    "low_coverage": (
        "Low coverage: absence of hits is unknown, not informative."
    ),
    "failed": "Adapter failed or was skipped; treat as a coverage gap.",
    "access_denied": "Lawful access was refused; visible gap, not a silent miss.",
}


def load_coverage_index(path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    target = path or (DATA_DIR / "sample_coverage.json")
    if not target.is_file():
        return {}
    payload = json.loads(target.read_text(encoding="utf-8"))
    people = payload.get("people", payload)
    if isinstance(people, dict):
        return {k: list(v) for k, v in people.items()}
    if isinstance(people, list):
        out: dict[str, list[dict[str, Any]]] = {}
        for row in people:
            sid = str(row.get("subject_id") or "")
            if sid:
                out[sid] = list(row.get("cells") or [])
        return out
    return {}


def cells_for_case(
    case: PersonCase,
    *,
    coverage_path: Path | None = None,
) -> list[dict[str, Any]]:
    owned = list(getattr(case, "coverage", None) or [])
    if owned:
        return owned
    return list(load_coverage_index(coverage_path).get(case.subject_id, []))


def _intensity(cell: dict[str, Any]) -> float:
    if cell.get("intensity") is not None:
        return max(0.0, min(1.0, float(cell["intensity"])))
    est = cell.get("coverage_estimate")
    if est is None:
        return 0.35
    return max(0.0, min(1.0, float(est)))


def coverage_feature(cell: dict[str, Any], *, subject_id: str) -> dict[str, Any]:
    result = str(cell.get("result") or "searched")
    intensity = _intensity(cell)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(cell["lon"]), float(cell["lat"])],
        },
        "properties": {
            "kind": "coverage_cell",
            "cell_id": cell.get("cell_id") or cell.get("source_id") or "",
            "subject_id": subject_id,
            "source_id": cell.get("source_id") or "",
            "jurisdiction": cell.get("jurisdiction") or "",
            "event_classes": list(cell.get("event_classes") or []),
            "coverage_estimate": cell.get("coverage_estimate"),
            "result": result,
            "intensity": intensity,
            "radius_m": float(cell.get("radius_m") or 8_000),
            "note": cell.get("note") or _RESULT_NOTE.get(result, ""),
            "framing": FRAMING,
        },
    }


def coverage_geojson(case: PersonCase, *, coverage_path: Path | None = None) -> dict[str, Any]:
    cells = cells_for_case(case, coverage_path=coverage_path)
    features = [
        coverage_feature(c, subject_id=case.subject_id)
        for c in cells
        if c.get("lat") is not None and c.get("lon") is not None
    ]
    return {
        "type": "FeatureCollection",
        "properties": {
            "kind": "coverage_heat",
            "subject_id": case.subject_id,
            "display_name": case.display_name,
            "cell_count": len(features),
            "framing": FRAMING,
            "boundary": (
                "Adapter search footprints and dead-end certificates. "
                "Not live tracking. Not a presence probability surface."
            ),
        },
        "features": features,
    }


def coverage_report(case: PersonCase, *, coverage_path: Path | None = None) -> dict[str, Any]:
    cells = cells_for_case(case, coverage_path=coverage_path)
    dead_ends = []
    adapters_run = []
    low = []
    failed = []
    for c in cells:
        result = str(c.get("result") or "searched")
        adapters_run.append(
            {
                "source_id": c.get("source_id"),
                "jurisdiction": c.get("jurisdiction"),
                "event_classes": list(c.get("event_classes") or []),
                "coverage_estimate": c.get("coverage_estimate"),
                "result": result,
            }
        )
        if result == "zero_compatible_hits":
            dead_ends.append(
                {
                    "certificate_id": c.get("cell_id") or c.get("source_id"),
                    "case_id": case.subject_id,
                    "source_id": c.get("source_id"),
                    "jurisdiction": c.get("jurisdiction"),
                    "time_window": c.get("time_window"),
                    "event_classes": list(c.get("event_classes") or []),
                    "coverage_estimate": c.get("coverage_estimate"),
                    "result": "zero_compatible_hits",
                    "note": c.get("note") or _RESULT_NOTE["zero_compatible_hits"],
                }
            )
        elif result == "low_coverage":
            low.append(c.get("source_id"))
        elif result in {"failed", "access_denied"}:
            failed.append({"source_id": c.get("source_id"), "result": result})
    return {
        "case_id": case.subject_id,
        "subject_id": case.subject_id,
        "display_name": case.display_name,
        "framing": FRAMING,
        "adapters_run": adapters_run,
        "dead_ends": dead_ends,
        "low_coverage_sources": low,
        "failed_or_denied": failed,
        "cell_count": len(cells),
        "geojson": coverage_geojson(case, coverage_path=coverage_path),
        "boundary": (
            "Coverage honesty: sources attempted, sources failed, jurisdictions "
            "not covered, and dead-end certificates. Silent gaps are a failure."
        ),
    }


def coverage_reports(
    cases: Iterable[PersonCase], *, coverage_path: Path | None = None
) -> dict[str, Any]:
    items = [coverage_report(c, coverage_path=coverage_path) for c in cases]
    return {
        "framing": FRAMING,
        "reports": items,
    }
