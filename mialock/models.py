"""Per-person historical location pins: date × time × event × duration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DATA_DIR = Path(__file__).resolve().parent / "data"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _duration_seconds(start: datetime, end: datetime | None, explicit: int | None) -> int:
    if explicit is not None:
        return max(0, int(explicit))
    if end is None:
        return 0
    return max(0, int((end - start).total_seconds()))


def _opt_float(raw: dict[str, Any], key: str) -> float | None:
    value = raw.get(key)
    if value in (None, ""):
        return None
    return float(value)


@dataclass(frozen=True)
class EventPin:
    """One documented historical presence point for a subject."""

    pin_id: str
    subject_id: str
    lat: float
    lon: float
    start_at: datetime
    event_class: str
    end_at: datetime | None = None
    duration_seconds: int = 0
    label: str = ""
    jurisdiction: str = ""
    geo_confidence: float = 0.5
    verification_state: str = "unverified"
    place_name: str = ""
    notes: str = ""
    source_tier: str = "discovery"
    location_uncertainty_m: float | None = None
    uncertainty_semi_major_m: float | None = None
    uncertainty_semi_minor_m: float | None = None
    uncertainty_bearing_deg: float = 0.0
    jurisdiction_footprint_m: float | None = None
    time_window_geo_soft_m: float | None = None
    doe_descriptor: dict[str, Any] = field(default_factory=dict)

    @property
    def date_str(self) -> str:
        return self.start_at.date().isoformat()

    @property
    def time_str(self) -> str:
        return self.start_at.strftime("%H:%M:%S %Z").strip()

    @property
    def duration_label(self) -> str:
        secs = self.duration_seconds
        if secs <= 0:
            return "instant / unknown duration"
        if secs < 60:
            return f"{secs}s"
        if secs < 3600:
            return f"{secs // 60}m {secs % 60}s"
        if secs < 86400:
            h, rem = divmod(secs, 3600)
            return f"{h}h {rem // 60}m"
        d, rem = divmod(secs, 86400)
        return f"{d}d {rem // 3600}h"

    def to_map_feature(self) -> dict[str, Any]:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [self.lon, self.lat]},
            "properties": {
                "pin_id": self.pin_id,
                "subject_id": self.subject_id,
                "date": self.date_str,
                "time": self.time_str,
                "start_at": self.start_at.isoformat(),
                "end_at": self.end_at.isoformat() if self.end_at else None,
                "event": self.event_class,
                "duration_seconds": self.duration_seconds,
                "duration_label": self.duration_label,
                "label": self.label or self.event_class,
                "place_name": self.place_name,
                "jurisdiction": self.jurisdiction,
                "geo_confidence": self.geo_confidence,
                "verification_state": self.verification_state,
                "source_tier": self.source_tier,
                "notes": self.notes,
                "kind": "event_pin",
                "location_uncertainty_m": self.location_uncertainty_m,
                "uncertainty_semi_major_m": self.uncertainty_semi_major_m,
                "uncertainty_semi_minor_m": self.uncertainty_semi_minor_m,
                "uncertainty_bearing_deg": self.uncertainty_bearing_deg,
                "jurisdiction_footprint_m": self.jurisdiction_footprint_m,
                "time_window_geo_soft_m": self.time_window_geo_soft_m,
                "doe_descriptor": dict(self.doe_descriptor or {}),
            },
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, subject_id: str | None = None) -> EventPin:
        start = _parse_dt(raw["start_at"])
        if start is None:
            raise ValueError("start_at is required")
        end = _parse_dt(raw.get("end_at"))
        sid = subject_id or raw["subject_id"]
        duration = _duration_seconds(start, end, raw.get("duration_seconds"))
        return cls(
            pin_id=str(raw["pin_id"]),
            subject_id=str(sid),
            lat=float(raw["lat"]),
            lon=float(raw["lon"]),
            start_at=start,
            end_at=end,
            duration_seconds=duration,
            event_class=str(raw["event_class"]),
            label=str(raw.get("label") or ""),
            jurisdiction=str(raw.get("jurisdiction") or ""),
            geo_confidence=float(raw.get("geo_confidence", 0.5)),
            verification_state=str(raw.get("verification_state") or "unverified"),
            place_name=str(raw.get("place_name") or ""),
            notes=str(raw.get("notes") or ""),
            source_tier=str(raw.get("source_tier") or "discovery"),
            location_uncertainty_m=_opt_float(raw, "location_uncertainty_m"),
            uncertainty_semi_major_m=_opt_float(raw, "uncertainty_semi_major_m"),
            uncertainty_semi_minor_m=_opt_float(raw, "uncertainty_semi_minor_m"),
            uncertainty_bearing_deg=float(raw.get("uncertainty_bearing_deg") or 0.0),
            jurisdiction_footprint_m=_opt_float(raw, "jurisdiction_footprint_m"),
            time_window_geo_soft_m=_opt_float(raw, "time_window_geo_soft_m"),
            doe_descriptor=dict(raw.get("doe_descriptor") or {}),
        )


@dataclass
class PersonCase:
    subject_id: str
    display_name: str
    summary: str = ""
    case_kind: str = "active"
    pins: list[EventPin] = field(default_factory=list)
    descriptor: dict[str, Any] = field(default_factory=dict)
    coverage: list[dict[str, Any]] = field(default_factory=list)

    def sorted_pins(self) -> list[EventPin]:
        return sorted(self.pins, key=lambda p: p.start_at)

    def pins_for_mode(self, mode_id: str = "all") -> list[EventPin]:
        from mialock.search_options import filter_pins_by_mode

        return filter_pins_by_mode(self.sorted_pins(), mode_id)

    def to_geojson(
        self,
        mode_id: str = "all",
        *,
        include_ellipses: bool = True,
        include_coverage: bool = False,
    ) -> dict[str, Any]:
        from mialock.uncertainty import ellipse_feature, pin_has_uncertainty

        pins = self.pins_for_mode(mode_id)
        features = [p.to_map_feature() for p in pins]
        ellipse_count = 0
        if include_ellipses:
            for p in pins:
                if pin_has_uncertainty(p):
                    features.append(ellipse_feature(p))
                    ellipse_count += 1
        if include_coverage:
            from mialock.coverage import coverage_feature, cells_for_case

            for cell in cells_for_case(self):
                if cell.get("lat") is not None and cell.get("lon") is not None:
                    features.append(coverage_feature(cell, subject_id=self.subject_id))
        line_coords = [[p.lon, p.lat] for p in pins if p.verification_state != "rejected"]
        if len(line_coords) >= 2:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": line_coords},
                    "properties": {
                        "kind": "chronology_path",
                        "subject_id": self.subject_id,
                        "note": "Documented event order only — not inferred travel",
                    },
                }
            )
        return {
            "type": "FeatureCollection",
            "properties": {
                "subject_id": self.subject_id,
                "display_name": self.display_name,
                "summary": self.summary,
                "case_kind": self.case_kind,
                "search_mode": mode_id,
                "pin_count": len(pins),
                "ellipse_count": ellipse_count,
                "descriptor": dict(self.descriptor or {}),
                "boundary": (
                    "Historical documented events with uncertainty ellipses. "
                    "Not live tracking. Coverage heat is search intensity, not presence."
                ),
            },
            "features": features,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "display_name": self.display_name,
            "summary": self.summary,
            "case_kind": self.case_kind,
            "descriptor": dict(self.descriptor or {}),
            "coverage": list(self.coverage or []),
            "pins": [asdict(p) | {
                "start_at": p.start_at.isoformat(),
                "end_at": p.end_at.isoformat() if p.end_at else None,
                "date": p.date_str,
                "time": p.time_str,
                "duration_label": p.duration_label,
            } for p in self.sorted_pins()],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PersonCase:
        subject_id = str(raw["subject_id"])
        pins = [
            EventPin.from_dict(p, subject_id=subject_id) for p in raw.get("pins", [])
        ]
        return cls(
            subject_id=subject_id,
            display_name=str(raw.get("display_name") or subject_id),
            summary=str(raw.get("summary") or ""),
            case_kind=str(raw.get("case_kind") or "active"),
            pins=pins,
            descriptor=dict(raw.get("descriptor") or {}),
            coverage=list(raw.get("coverage") or []),
        )


def load_casebook(path: Path | None = None) -> list[PersonCase]:
    target = path or (DATA_DIR / "sample_persons.json")
    payload = json.loads(target.read_text(encoding="utf-8"))
    people = payload.get("people", payload)
    if not isinstance(people, list):
        raise ValueError("casebook must contain a people list")
    return [PersonCase.from_dict(p) for p in people]


def casebook_index(cases: Iterable[PersonCase]) -> dict[str, Any]:
    items = list(cases)
    return {
        "boundary": "Historical documented events with date × time × event × duration. Not live tracking.",
        "people": [
            {
                "subject_id": c.subject_id,
                "display_name": c.display_name,
                "summary": c.summary,
                "case_kind": c.case_kind,
                "pin_count": len(c.pins),
                "span": {
                    "start": c.sorted_pins()[0].start_at.isoformat() if c.pins else None,
                    "end": (
                        (c.sorted_pins()[-1].end_at or c.sorted_pins()[-1].start_at).isoformat()
                        if c.pins
                        else None
                    ),
                },
            }
            for c in items
        ],
    }
