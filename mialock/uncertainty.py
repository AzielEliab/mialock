"""Spatial / temporal uncertainty ellipses for event pins.

Whitepaper §11: each event node carries a time interval (soft uncertainty
band), jurisdiction, and geographic confidence. Semi-axes combine:

* location uncertainty (explicit meters or inverted geo_confidence)
* jurisdiction footprint (county / state grain as a *soft* contribution)
* time-window geo soft-band (unknown or wide duration expands the ellipse)

Rendered as GeoJSON polygons (Leaflet has no native ellipse). Historical
uncertainty only — not live tracking.
"""

from __future__ import annotations

import math
from typing import Any

# ~meters per degree of latitude.
_LAT_M = 111_320.0
_ELLIPSE_POINTS = 48

# County-scale footprint is a soft contribution, not a full-county disk.
_JURIS_COUNTY_M = 22_000.0
_JURIS_STATE_M = 40_000.0
_JURIS_DEFAULT_M = 15_000.0


def _meters_per_degree_lon(lat: float) -> float:
    return max(1.0, _LAT_M * math.cos(math.radians(lat)))


def invert_geo_confidence(geo_confidence: float) -> float:
    """Map geo_confidence in [0, 1] to a location-uncertainty radius in meters."""
    conf = min(1.0, max(0.0, float(geo_confidence)))
    return 400.0 + ((1.0 - conf) ** 1.35) * 28_000.0


def default_jurisdiction_footprint_m(jurisdiction: str) -> float:
    code = (jurisdiction or "").strip().upper()
    parts = [p for p in code.split("-") if p]
    if len(parts) >= 3:
        return _JURIS_COUNTY_M
    if len(parts) == 2:
        return _JURIS_STATE_M
    return _JURIS_DEFAULT_M


def default_time_window_soft_m(*, duration_seconds: int, geo_confidence: float) -> float:
    """Wider clock/date uncertainty → larger geo soft-band."""
    conf = min(1.0, max(0.0, float(geo_confidence)))
    if duration_seconds <= 0:
        return 1_500.0 + (1.0 - conf) * 4_000.0
    if duration_seconds >= 86_400:
        return 400.0
    return 200.0


def pin_ellipse_axes(pin: Any) -> tuple[float, float, float, list[str]]:
    """Return (semi_major_m, semi_minor_m, bearing_deg, sources)."""
    sources: list[str] = []
    geo_conf = float(getattr(pin, "geo_confidence", 0.5) or 0.5)
    duration = int(getattr(pin, "duration_seconds", 0) or 0)
    jurisdiction = str(getattr(pin, "jurisdiction", "") or "")

    explicit_major = getattr(pin, "uncertainty_semi_major_m", None)
    explicit_minor = getattr(pin, "uncertainty_semi_minor_m", None)
    bearing = float(getattr(pin, "uncertainty_bearing_deg", 0.0) or 0.0)

    loc = getattr(pin, "location_uncertainty_m", None)
    if loc is None:
        loc = invert_geo_confidence(geo_conf)
        sources.append("geo_confidence")
    else:
        loc = float(loc)
        sources.append("location_uncertainty")

    juris = getattr(pin, "jurisdiction_footprint_m", None)
    if juris is None:
        juris = default_jurisdiction_footprint_m(jurisdiction)
        sources.append("jurisdiction_footprint")
    else:
        juris = float(juris)
        sources.append("jurisdiction_footprint")

    time_soft = getattr(pin, "time_window_geo_soft_m", None)
    if time_soft is None:
        time_soft = default_time_window_soft_m(
            duration_seconds=duration, geo_confidence=geo_conf
        )
        sources.append("time_window_soft_band")
    else:
        time_soft = float(time_soft)
        sources.append("time_window_soft_band")

    if explicit_major is not None and explicit_minor is not None:
        return (
            max(50.0, float(explicit_major)),
            max(50.0, float(explicit_minor)),
            bearing,
            sources + ["explicit_semi_axes"],
        )

    # Jurisdiction grain is a soft band, not a full-county disk around the pin.
    major = loc + 0.18 * juris + time_soft
    minor = loc * 0.62 + 0.08 * juris + 0.45 * time_soft
    if explicit_major is not None:
        major = max(50.0, float(explicit_major))
        sources.append("explicit_semi_major")
    if explicit_minor is not None:
        minor = max(50.0, float(explicit_minor))
        sources.append("explicit_semi_minor")
    if minor > major:
        major, minor = minor, major
    if abs(bearing) < 1e-9:
        bearing = 22.0
    return max(50.0, major), max(50.0, minor), bearing, sources


def ellipse_ring(
    lat: float,
    lon: float,
    semi_major_m: float,
    semi_minor_m: float,
    bearing_deg: float,
    n: int = _ELLIPSE_POINTS,
) -> list[list[float]]:
    """Closed ring of [lon, lat] positions approximating an oriented ellipse."""
    theta = math.radians(bearing_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    m_per_lon = _meters_per_degree_lon(lat)
    ring: list[list[float]] = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        # Local ENU meters, then rotate by bearing (clockwise from north → rotate from east).
        east = semi_major_m * math.cos(a)
        north = semi_minor_m * math.sin(a)
        rot_east = east * cos_t - north * sin_t
        rot_north = east * sin_t + north * cos_t
        ring.append([lon + rot_east / m_per_lon, lat + rot_north / _LAT_M])
    ring.append(ring[0])
    return ring


def ellipse_feature(pin: Any) -> dict[str, Any]:
    major, minor, bearing, sources = pin_ellipse_axes(pin)
    ring = ellipse_ring(pin.lat, pin.lon, major, minor, bearing)
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "kind": "uncertainty_ellipse",
            "pin_id": pin.pin_id,
            "subject_id": pin.subject_id,
            "event": pin.event_class,
            "semi_major_m": round(major, 1),
            "semi_minor_m": round(minor, 1),
            "bearing_deg": round(bearing, 1),
            "sources": sources,
            "geo_confidence": getattr(pin, "geo_confidence", None),
            "jurisdiction": getattr(pin, "jurisdiction", ""),
            "note": (
                "Spatial/temporal uncertainty ellipse "
                "(location × jurisdiction footprint × time-window soft-band). "
                "Not a live location."
            ),
        },
    }


def pin_has_uncertainty(pin: Any) -> bool:
    """True when the pin should render an ellipse (any spatial/temporal uncertainty)."""
    if getattr(pin, "uncertainty_semi_major_m", None) or getattr(
        pin, "location_uncertainty_m", None
    ):
        return True
    if getattr(pin, "time_window_geo_soft_m", None):
        return True
    conf = float(getattr(pin, "geo_confidence", 0.5) or 0.5)
    return conf < 0.99 or int(getattr(pin, "duration_seconds", 0) or 0) == 0
