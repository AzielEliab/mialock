"""Coverage report + heat GeoJSON. Heat is search intensity, not presence."""

from __future__ import annotations

import json

from mialock.coverage import FRAMING, coverage_geojson, coverage_report
from mialock.models import load_casebook


def test_sample_people_have_coverage_cells():
    cases = {c.subject_id: c for c in load_casebook()}
    for sid in ("subj-christina-demo", "subj-jordan-demo", "subj-elena-cold-demo"):
        report = coverage_report(cases[sid])
        assert report["cell_count"] >= 3
        assert report["framing"] == FRAMING
        assert "not a probability of presence" in report["framing"]
        results = {row["result"] for row in report["adapters_run"]}
        assert "searched" in results


def test_coverage_geojson_cells_are_heat_points():
    elena = next(c for c in load_casebook() if c.subject_id == "subj-elena-cold-demo")
    geo = coverage_geojson(elena)
    assert geo["properties"]["kind"] == "coverage_heat"
    assert geo["properties"]["framing"] == FRAMING
    points = [f for f in geo["features"] if f["geometry"]["type"] == "Point"]
    assert points
    for feat in points:
        props = feat["properties"]
        assert props["kind"] == "coverage_cell"
        assert 0 <= props["intensity"] <= 1
        assert props["result"] in {
            "searched",
            "zero_compatible_hits",
            "low_coverage",
            "failed",
            "access_denied",
        }


def test_dead_end_certificate_shape():
    elena = next(c for c in load_casebook() if c.subject_id == "subj-elena-cold-demo")
    report = coverage_report(elena)
    assert report["dead_ends"]
    cert = report["dead_ends"][0]
    assert cert["result"] == "zero_compatible_hits"
    assert "coverage_estimate" in cert
    assert cert["case_id"] == "subj-elena-cold-demo"


def test_cli_and_map_coverage(tmp_path=None):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    import threading

    from mialock.cli import main
    from mialock.map_ui import MapState, make_handler

    from io import StringIO
    import sys

    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = main(["coverage", "--subject", "subj-elena-cold-demo", "--json"])
    finally:
        sys.stdout = old
    assert rc == 0
    cli = json.loads(buf.getvalue())
    assert cli["dead_ends"]

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(MapState()))
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/people/subj-elena-cold-demo/coverage")
        res = conn.getresponse()
        body = json.loads(res.read().decode())
        assert res.status == 200
        assert body["geojson"]["features"]
        conn.close()
    finally:
        httpd.shutdown()
