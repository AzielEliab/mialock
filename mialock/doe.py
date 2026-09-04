"""Doe descriptor matching — compatibility leads only, never identification.

Matches a named-subject descriptor (age band, sex, height/build, scars/marks,
clothing, time window, jurisdiction) against John/Jane Doe and unidentified
notices. Emits ranked leads with an explicit score and field-level
match / mismatch / unknown. Hard sex conflicts are excluded from the lead list.

Whitepaper §§9, 11, 13 and docs/cold-case-archives.md: Doe hit ≠ ID.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from mialock.models import DATA_DIR, EventPin, PersonCase

DOE_EVENT_CLASSES = frozenset(
    {
        "jane_doe_notice",
        "john_doe_notice",
        "unidentified_remains",
        "cold_case_unidentified",
        "medical_examiner_case",
    }
)

# Ranking only — never calibrated identity probability. 100 is reserved
# for authoritative confirmation. Doe descriptor compatibility cannot
# enter probable / near-certain bands (whitepaper §13 + Doe ≠ ID).
MIN_LEAD_SCORE = 30
MAX_RANK_SCORE = 84

_FEMALE = frozenset({"female", "f", "woman", "girl", "jane", "w"})
_MALE = frozenset({"male", "m", "man", "boy", "john"})

_WEIGHTS = {
    "sex": 22.0,
    "age_band": 20.0,
    "jurisdiction": 16.0,
    "time_window": 14.0,
    "height": 10.0,
    "build": 6.0,
    "scars_marks": 8.0,
    "clothing": 4.0,
}

_BOUNDARY = (
    "Compatibility leads only — never an identification. "
    "Doe hit ≠ ID. Rank scores are uncalibrated operational labels, "
    "not the probability that the notice is the missing person."
)


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def normalize_sex(value: Any, *, event_class: str = "") -> str:
    text = _norm(value)
    if text in _FEMALE:
        return "female"
    if text in _MALE:
        return "male"
    ev = _norm(event_class)
    if ev.startswith("jane_doe"):
        return "female"
    if ev.startswith("john_doe"):
        return "male"
    return ""


def parse_age_band(value: Any) -> tuple[float, float] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        n = float(value)
        return (n, n)
    text = _norm(value).replace("–", "-").replace("to", "-")
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (min(lo, hi), max(lo, hi))
    mid = re.search(r"mid-?(\d{2})", text)
    if mid:
        decade = int(mid.group(1))
        return (decade + 2.0, decade + 7.0)
    early = re.search(r"early-?(\d{2})", text)
    if early:
        decade = int(early.group(1))
        return (float(decade), decade + 4.0)
    late = re.search(r"late-?(\d{2})", text)
    if late:
        decade = int(late.group(1))
        return (decade + 6.0, decade + 9.0)
    single = re.search(r"(\d+(?:\.\d+)?)", text)
    if single:
        n = float(single.group(1))
        return (n, n)
    return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            return None


def parse_height_cm(value: Any, band: Any = None) -> tuple[float, float] | None:
    if value not in (None, ""):
        try:
            h = float(value)
            return (h - 3.0, h + 3.0)
        except (TypeError, ValueError):
            text = _norm(value)
            feet = re.search(r"(\d)\s*['ft]\s*(\d{1,2})?", text)
            if feet:
                ft = int(feet.group(1))
                inch = int(feet.group(2) or 0)
                cm = (ft * 12 + inch) * 2.54
                return (cm - 4.0, cm + 4.0)
    return parse_age_band(band)  # reuse "lo-hi" parser for height_band


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _norm(text)) if len(t) > 1}


def _jurisdiction_tokens(code: str) -> set[str]:
    raw = _norm(code).replace("_", "-")
    parts = {p for p in re.split(r"[^a-z0-9]+", raw) if p}
    aliases = {
        "illinois": "il",
        "wisconsin": "wi",
        "cook": "cook",
        "milwaukee": "milwaukee",
        "champaign": "champaign",
        "winnebago": "winnebago",
        "kane": "kane",
    }
    extra = set()
    for p in list(parts):
        if p in aliases:
            extra.add(aliases[p])
        for k, v in aliases.items():
            if p == v:
                extra.add(k)
    return parts | extra


@dataclass(frozen=True)
class Descriptor:
    """Named-subject or Doe-notice demographic / circumstance descriptor."""

    age_band: str = ""
    sex: str = ""
    height_cm: float | None = None
    height_band: str = ""
    build: str = ""
    scars_marks: str = ""
    clothing: str = ""
    time_window_from: str = ""
    time_window_to: str = ""
    jurisdiction: str = ""
    event_class: str = ""
    notice_id: str = ""
    label: str = ""
    lat: float | None = None
    lon: float | None = None
    source_tier: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None, **overrides: Any) -> Descriptor:
        data = dict(raw or {})
        data.update({k: v for k, v in overrides.items() if v not in (None, "")})
        height = data.get("height_cm")
        try:
            height_f = float(height) if height not in (None, "") else None
        except (TypeError, ValueError):
            height_f = None
        return cls(
            age_band=str(data.get("age_band") or ""),
            sex=str(data.get("sex") or ""),
            height_cm=height_f,
            height_band=str(data.get("height_band") or ""),
            build=str(data.get("build") or ""),
            scars_marks=str(data.get("scars_marks") or data.get("distinguishing_marks") or ""),
            clothing=str(data.get("clothing") or ""),
            time_window_from=str(
                data.get("time_window_from") or data.get("year_from") or ""
            ),
            time_window_to=str(data.get("time_window_to") or data.get("year_to") or ""),
            jurisdiction=str(data.get("jurisdiction") or ""),
            event_class=str(data.get("event_class") or ""),
            notice_id=str(data.get("notice_id") or data.get("pin_id") or ""),
            label=str(data.get("label") or ""),
            lat=float(data["lat"]) if data.get("lat") not in (None, "") else None,
            lon=float(data["lon"]) if data.get("lon") not in (None, "") else None,
            source_tier=str(data.get("source_tier") or ""),
            notes=str(data.get("notes") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FieldVerdict:
    field: str
    subject: str
    notice: str
    status: str  # match | soft_match | mismatch | unknown
    detail: str = ""
    contribution: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _score_sex(subject: Descriptor, notice: Descriptor) -> tuple[FieldVerdict, bool]:
    s = normalize_sex(subject.sex, event_class=subject.event_class)
    n = normalize_sex(notice.sex, event_class=notice.event_class)
    if not s or not n:
        return FieldVerdict("sex", s or "", n or "", "unknown", "one or both unknown"), False
    if s == n:
        return FieldVerdict("sex", s, n, "match", "exact", _WEIGHTS["sex"]), False
    return FieldVerdict("sex", s, n, "mismatch", "hard demographic conflict"), True


def _score_range(
    field_name: str,
    subject_range: tuple[float, float] | None,
    notice_range: tuple[float, float] | None,
    subject_label: str,
    notice_label: str,
    *,
    weight: float,
) -> FieldVerdict:
    if subject_range is None or notice_range is None:
        return FieldVerdict(field_name, subject_label, notice_label, "unknown", "missing bound")
    lo = max(subject_range[0], notice_range[0])
    hi = min(subject_range[1], notice_range[1])
    overlap = max(0.0, hi - lo)
    span = min(subject_range[1] - subject_range[0], notice_range[1] - notice_range[0])
    if span <= 0:
        # Point estimates: match if within 2 units, soft within 5.
        dist = abs(subject_range[0] - notice_range[0])
        if dist <= 2:
            return FieldVerdict(field_name, subject_label, notice_label, "match", f"delta={dist:.1f}", weight)
        if dist <= 5:
            return FieldVerdict(
                field_name, subject_label, notice_label, "soft_match", f"delta={dist:.1f}", weight * 0.55
            )
        return FieldVerdict(field_name, subject_label, notice_label, "mismatch", f"delta={dist:.1f}", 0.0)
    ratio = overlap / span if span else 0.0
    if ratio >= 0.5:
        status = "match" if ratio >= 0.85 else "soft_match"
        return FieldVerdict(
            field_name, subject_label, notice_label, status, f"overlap={ratio:.2f}", weight * min(1.0, ratio)
        )
    if ratio > 0:
        return FieldVerdict(
            field_name, subject_label, notice_label, "soft_match", f"overlap={ratio:.2f}", weight * ratio * 0.5
        )
    return FieldVerdict(field_name, subject_label, notice_label, "mismatch", "no overlap", 0.0)


def _score_jurisdiction(subject: Descriptor, notice: Descriptor) -> FieldVerdict:
    s, n = subject.jurisdiction, notice.jurisdiction
    if not _norm(s) or not _norm(n):
        return FieldVerdict("jurisdiction", s, n, "unknown", "missing jurisdiction")
    st, nt = _jurisdiction_tokens(s), _jurisdiction_tokens(n)
    su, nu = _norm(s).upper().replace(" ", "-"), _norm(n).upper().replace(" ", "-")
    if su == nu or su in nu or nu in su:
        return FieldVerdict("jurisdiction", s, n, "match", "exact or nested", _WEIGHTS["jurisdiction"])
    shared = st & nt
    # Shared country-only (us) is not enough.
    meaningful = {t for t in shared if t not in {"us", "usa", "united", "states"}}
    if meaningful:
        return FieldVerdict(
            "jurisdiction", s, n, "soft_match", f"shared={sorted(meaningful)}", _WEIGHTS["jurisdiction"] * 0.5
        )
    return FieldVerdict("jurisdiction", s, n, "mismatch", "no shared grain", 0.0)


def _score_time(subject: Descriptor, notice: Descriptor) -> FieldVerdict:
    s0 = _parse_date(subject.time_window_from)
    s1 = _parse_date(subject.time_window_to) or s0
    n0 = _parse_date(notice.time_window_from)
    n1 = _parse_date(notice.time_window_to) or n0
    sl = f"{subject.time_window_from}..{subject.time_window_to}".strip(".")
    nl = f"{notice.time_window_from}..{notice.time_window_to}".strip(".")
    if not s0 or not n0:
        return FieldVerdict("time_window", sl, nl, "unknown", "missing window")
    assert s1 is not None and n1 is not None
    lo = max(s0, n0)
    hi = min(s1, n1)
    if lo <= hi:
        return FieldVerdict("time_window", sl, nl, "match", "windows overlap", _WEIGHTS["time_window"])
    gap = (lo - hi).days
    if gap <= 180:
        return FieldVerdict(
            "time_window", sl, nl, "soft_match", f"gap_days={gap}", _WEIGHTS["time_window"] * 0.45
        )
    return FieldVerdict("time_window", sl, nl, "mismatch", f"gap_days={gap}", 0.0)


def _score_tokens(field_name: str, subject_val: str, notice_val: str, weight: float) -> FieldVerdict:
    if not _norm(subject_val) or not _norm(notice_val):
        return FieldVerdict(field_name, subject_val, notice_val, "unknown", "one or both unknown")
    st, nt = _tokens(subject_val), _tokens(notice_val)
    if not st or not nt:
        return FieldVerdict(field_name, subject_val, notice_val, "unknown", "no tokens")
    if st == nt or subject_val.strip().lower() == notice_val.strip().lower():
        return FieldVerdict(field_name, subject_val, notice_val, "match", "exact", weight)
    shared = st & nt
    if shared:
        ratio = len(shared) / max(len(st), len(nt))
        return FieldVerdict(
            field_name, subject_val, notice_val, "soft_match", f"shared={sorted(shared)}", weight * min(1.0, ratio + 0.25)
        )
    return FieldVerdict(field_name, subject_val, notice_val, "mismatch", "no shared tokens", 0.0)


def _band_label(score: float) -> str:
    if score >= 95:
        return "Near-certain correlation"
    if score >= 85:
        return "Probable candidate"
    if score >= 70:
        return "Strong candidate"
    if score >= 50:
        return "Investigate"
    if score >= 30:
        return "Weak candidate"
    return "Noise"


def _next_verification(fields: list[FieldVerdict], notice: Descriptor) -> str:
    unknown = [f.field for f in fields if f.status == "unknown"]
    mismatches = [f.field for f in fields if f.status == "mismatch"]
    if "scars_marks" in unknown or "scars_marks" in {f.field for f in fields}:
        marks = "Compare scars/marks / dental / fingerprints through an authorized ME or clearinghouse channel"
    else:
        marks = "Seek an authorized identification process (fingerprints, dental, DNA) — do not treat this score as ID"
    extras = []
    if mismatches:
        extras.append("resolve " + ", ".join(mismatches))
    if unknown:
        extras.append("fill unknown fields: " + ", ".join(unknown[:4]))
    suffix = f" Next cheapest checks: {'; '.join(extras)}." if extras else ""
    return f"{marks}. Notice remains a compatibility lead only ({notice.event_class or 'unidentified'}).{suffix}"


def score_descriptor_pair(subject: Descriptor, notice: Descriptor) -> dict[str, Any]:
    fields: list[FieldVerdict] = []
    sex_v, hard_sex = _score_sex(subject, notice)
    fields.append(sex_v)
    fields.append(
        _score_range(
            "age_band",
            parse_age_band(subject.age_band),
            parse_age_band(notice.age_band),
            subject.age_band,
            notice.age_band,
            weight=_WEIGHTS["age_band"],
        )
    )
    fields.append(_score_jurisdiction(subject, notice))
    fields.append(_score_time(subject, notice))
    fields.append(
        _score_range(
            "height",
            parse_height_cm(subject.height_cm, subject.height_band),
            parse_height_cm(notice.height_cm, notice.height_band),
            subject.height_band or (str(subject.height_cm) if subject.height_cm else ""),
            notice.height_band or (str(notice.height_cm) if notice.height_cm else ""),
            weight=_WEIGHTS["height"],
        )
    )
    fields.append(_score_tokens("build", subject.build, notice.build, _WEIGHTS["build"]))
    fields.append(_score_tokens("scars_marks", subject.scars_marks, notice.scars_marks, _WEIGHTS["scars_marks"]))
    fields.append(_score_tokens("clothing", subject.clothing, notice.clothing, _WEIGHTS["clothing"]))

    raw = sum(f.contribution for f in fields)
    denom = sum(_WEIGHTS.values())
    # Age complete miss is a major contradiction (whitepaper §10).
    age = next(f for f in fields if f.field == "age_band")
    penalty = 0.0
    if age.status == "mismatch":
        penalty += 18.0
    if hard_sex:
        penalty += 40.0
    uncapped = 100.0 * (raw - penalty) / denom
    score = max(0.0, min(float(MAX_RANK_SCORE), uncapped))
    score = round(score, 1)
    return {
        "notice_id": notice.notice_id,
        "label": notice.label or notice.notice_id,
        "event_class": notice.event_class,
        "rank_score": score,
        "label_band": _band_label(score),
        "calibration_status": "uncalibrated",
        "hard_sex_mismatch": hard_sex,
        "is_lead": (not hard_sex) and score >= MIN_LEAD_SCORE,
        "fields": [f.to_dict() for f in fields],
        "next_verification": _next_verification(fields, notice),
        "lat": notice.lat,
        "lon": notice.lon,
        "jurisdiction": notice.jurisdiction,
        "source_tier": notice.source_tier,
        "notes": notice.notes,
        "warning": "DO NOT INTERPRET AS CONFIRMED IDENTITY UNTIL VERIFIED. Doe hit ≠ ID.",
    }


def match_descriptors(
    subject: Descriptor,
    notices: Iterable[Descriptor],
) -> dict[str, Any]:
    scored = [score_descriptor_pair(subject, n) for n in notices]
    leads = sorted(
        (r for r in scored if r["is_lead"]),
        key=lambda r: (-r["rank_score"], r["notice_id"]),
    )
    excluded = [r for r in scored if not r["is_lead"]]
    return {
        "boundary": _BOUNDARY,
        "calibration_status": "uncalibrated",
        "subject": subject.to_dict(),
        "lead_count": len(leads),
        "leads": leads,
        "excluded": [
            {
                "notice_id": r["notice_id"],
                "label": r["label"],
                "event_class": r["event_class"],
                "rank_score": r["rank_score"],
                "reason": "sex_mismatch" if r["hard_sex_mismatch"] else "below_lead_threshold",
                "fields": r["fields"],
                "warning": r["warning"],
            }
            for r in excluded
        ],
        "warning": "DO NOT INTERPRET AS CONFIRMED IDENTITY UNTIL VERIFIED. Doe hit ≠ ID.",
    }


def descriptor_from_case(case: PersonCase) -> Descriptor:
    raw = dict(getattr(case, "descriptor", None) or {})
    if not raw.get("jurisdiction") and case.pins:
        raw.setdefault("jurisdiction", case.pins[0].jurisdiction)
    return Descriptor.from_mapping(raw, label=case.display_name, notice_id=case.subject_id)


def notices_from_pins(pins: Iterable[EventPin]) -> list[Descriptor]:
    out: list[Descriptor] = []
    for pin in pins:
        if pin.event_class not in DOE_EVENT_CLASSES:
            continue
        raw = dict(getattr(pin, "doe_descriptor", None) or {})
        raw.setdefault("event_class", pin.event_class)
        raw.setdefault("notice_id", pin.pin_id)
        raw.setdefault("pin_id", pin.pin_id)
        raw.setdefault("label", pin.label or pin.event_class)
        raw.setdefault("lat", pin.lat)
        raw.setdefault("lon", pin.lon)
        raw.setdefault("jurisdiction", raw.get("jurisdiction") or pin.jurisdiction)
        raw.setdefault("source_tier", pin.source_tier)
        raw.setdefault("notes", pin.notes)
        if pin.start_at and not raw.get("time_window_from"):
            raw["time_window_from"] = pin.start_at.date().isoformat()
        if pin.end_at and not raw.get("time_window_to"):
            raw["time_window_to"] = pin.end_at.date().isoformat()
        elif pin.start_at and not raw.get("time_window_to"):
            raw["time_window_to"] = pin.start_at.date().isoformat()
        out.append(Descriptor.from_mapping(raw))
    return out


def load_sample_notices(path: Path | None = None) -> list[Descriptor]:
    target = path or (DATA_DIR / "sample_doe_notices.json")
    if not target.is_file():
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    items = payload.get("notices", payload)
    if not isinstance(items, list):
        return []
    return [Descriptor.from_mapping(n) for n in items]


def match_subject(
    case: PersonCase,
    *,
    include_sample_notices: bool = True,
    notices_path: Path | None = None,
    extra_notices: Iterable[Descriptor] | None = None,
) -> dict[str, Any]:
    subject = descriptor_from_case(case)
    notices = notices_from_pins(case.pins)
    seen = {n.notice_id for n in notices if n.notice_id}
    if include_sample_notices:
        for n in load_sample_notices(notices_path):
            if n.notice_id and n.notice_id in seen:
                continue
            notices.append(n)
            if n.notice_id:
                seen.add(n.notice_id)
    if extra_notices:
        notices.extend(list(extra_notices))
    payload = match_descriptors(subject, notices)
    payload["subject_id"] = case.subject_id
    payload["display_name"] = case.display_name
    return payload


def descriptor_from_cli_args(**kwargs: Any) -> Descriptor:
    return Descriptor.from_mapping(kwargs)
