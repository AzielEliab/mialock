"""Tests for M.I.A.Lock per-person event map pins."""

from __future__ import annotations

import json
from datetime import timedelta

from mialock.models import EventPin, load_casebook


def test_sample_casebook_loads_two_people():
    cases = load_casebook()
    assert len(cases) >= 2
    assert all(c.pins for c in cases)


def test_pin_exposes_date_time_event_duration():
    cases = load_casebook()
    pin = cases[0].sorted_pins()[0]
    assert pin.date_str
    assert pin.time_str
    assert pin.event_class
    assert isinstance(pin.duration_seconds, int)
    assert pin.duration_label


def test_duration_from_end_at():
    pin = EventPin.from_dict(
        {
            "pin_id": "t1",
            "subject_id": "s1",
            "lat": 41.0,
            "lon": -87.0,
            "start_at": "2026-01-01T10:00:00+00:00",
            "end_at": "2026-01-01T12:30:00+00:00",
            "event_class": "custody",
        }
    )
    assert pin.duration_seconds == int(timedelta(hours=2, minutes=30).total_seconds())
    assert "2h" in pin.duration_label


def test_geojson_is_per_person_and_includes_path():
    cases = load_casebook()
    geo = cases[0].to_geojson()
    assert geo["type"] == "FeatureCollection"
    assert geo["properties"]["subject_id"] == cases[0].subject_id
    points = [f for f in geo["features"] if f["geometry"]["type"] == "Point"]
    assert len(points) == len(cases[0].pins)
    for feat in points:
        props = feat["properties"]
        assert {"date", "time", "event", "duration_seconds", "duration_label"} <= set(props)
    if len(points) >= 2:
        lines = [f for f in geo["features"] if f["geometry"]["type"] == "LineString"]
        assert lines
    ellipses = [
        f
        for f in geo["features"]
        if f["geometry"]["type"] == "Polygon"
        and (f["properties"] or {}).get("kind") == "uncertainty_ellipse"
    ]
    assert ellipses, "sample pins must emit uncertainty ellipses"
    for feat in ellipses:
        props = feat["properties"]
        assert props["semi_major_m"] >= props["semi_minor_m"]
        assert props["semi_major_m"] > 0
        assert "location" in " ".join(props.get("sources") or []) or props.get("sources")
        ring = feat["geometry"]["coordinates"][0]
        assert len(ring) >= 8
        assert ring[0] == ring[-1]


def test_sample_pins_include_explicit_uncertainty_fields():
    cases = load_casebook()
    measured = [
        p
        for c in cases
        for p in c.pins
        if p.location_uncertainty_m or p.uncertainty_semi_major_m
    ]
    assert len(measured) >= 6
    elena = next(c for c in cases if c.subject_id == "subj-elena-cold-demo")
    jane = next(p for p in elena.pins if p.pin_id == "ev-3")
    assert jane.uncertainty_semi_major_m == 3200
    assert jane.uncertainty_semi_minor_m == 1900
    assert jane.doe_descriptor.get("sex") == "female"


def test_map_handler_people_and_geojson(tmp_path):
    from mialock.map_ui import MapState, make_handler
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    import threading

    state = MapState()
    handler = make_handler(state)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/people")
        res = conn.getresponse()
        body = json.loads(res.read().decode())
        assert res.status == 200
        assert body["people"]
        sid = body["people"][0]["subject_id"]
        conn.request("GET", f"/api/people/{sid}/geojson")
        res2 = conn.getresponse()
        geo = json.loads(res2.read().decode())
        assert res2.status == 200
        assert geo["properties"]["subject_id"] == sid
        conn.request("GET", "/")
        res3 = conn.getresponse()
        html = res3.read().decode()
        assert res3.status == 200
        assert "date × time × event × duration" in html
        assert "Uncertainty ellipses" in html
        assert "Coverage heat" in html
        assert "Show events" in html
        assert "Advanced" in html
        assert "prefers-color-scheme" in html
        assert ":focus-visible" in html
        conn.request("GET", "/", headers={"Accept": "application/json"})
        res_json = conn.getresponse()
        machine = json.loads(res_json.read().decode())
        assert res_json.status == 200
        assert machine["product"] == "mialock"
        assert machine["author"] == "Aziel Eliab"
        conn.request("GET", f"/api/people/{sid}/geojson?mode=all")
        res4 = conn.getresponse()
        geo2 = json.loads(res4.read().decode())
        assert res4.status == 200
        assert geo2["properties"]["ellipse_count"] >= 1
        conn.close()
    finally:
        httpd.shutdown()
