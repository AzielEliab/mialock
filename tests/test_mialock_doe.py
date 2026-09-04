"""Doe descriptor matching — positive and negative cases. Leads ≠ ID."""

from __future__ import annotations

import json

from mialock.doe import (
    Descriptor,
    match_descriptors,
    match_subject,
    notices_from_pins,
)
from mialock.models import load_casebook


def _elena():
    return next(c for c in load_casebook() if c.subject_id == "subj-elena-cold-demo")


def test_positive_jane_doe_is_ranked_lead():
    case = _elena()
    payload = match_subject(case, include_sample_notices=False)
    assert payload["warning"].startswith("DO NOT INTERPRET")
    assert "never" in payload["boundary"].lower() or "≠" in payload["boundary"]
    ids = {lead["notice_id"] for lead in payload["leads"]}
    assert "ev-3" in ids
    jane = next(lead for lead in payload["leads"] if lead["notice_id"] == "ev-3")
    assert jane["rank_score"] >= 50
    assert jane["calibration_status"] == "uncalibrated"
    fields = {f["field"]: f for f in jane["fields"]}
    assert fields["sex"]["status"] == "match"
    assert fields["age_band"]["status"] in {"match", "soft_match"}
    assert fields["scars_marks"]["status"] == "match"
    assert "NOT" in jane["warning"] or "≠" in jane["warning"]


def test_negative_sex_mismatch_is_not_a_lead():
    case = _elena()
    payload = match_subject(case, include_sample_notices=False)
    lead_ids = {lead["notice_id"] for lead in payload["leads"]}
    assert "ev-6" not in lead_ids
    excluded = next(x for x in payload["excluded"] if x["notice_id"] == "ev-6")
    assert excluded["reason"] == "sex_mismatch"
    sex = next(f for f in excluded["fields"] if f["field"] == "sex")
    assert sex["status"] == "mismatch"


def test_negative_age_mismatch_drops_below_lead_floor():
    subject = Descriptor.from_mapping(
        {
            "age_band": "20-30",
            "sex": "female",
            "jurisdiction": "US-IL-COOK",
            "time_window_from": "1994-09-02",
            "time_window_to": "1995-12-31",
        }
    )
    notice = Descriptor.from_mapping(
        {
            "notice_id": "age-miss",
            "event_class": "jane_doe_notice",
            "age_band": "45-55",
            "sex": "female",
            "jurisdiction": "US-IL-CHAMPAIGN",
            "scars_marks": "scar right knee",
            "build": "heavy",
            "time_window_from": "1996-01-01",
            "time_window_to": "1996-03-01",
        }
    )
    payload = match_descriptors(subject, [notice])
    assert payload["leads"] == []
    assert payload["excluded"][0]["reason"] in {"below_lead_threshold", "sex_mismatch"}


def test_cli_descriptor_args_match_sample_notices():
    from mialock.cli import main
    from io import StringIO
    import sys

    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = main(
            [
                "doe-match",
                "--age-band",
                "20-30",
                "--sex",
                "female",
                "--height-cm",
                "165",
                "--build",
                "slim",
                "--scars-marks",
                "tattoo left wrist",
                "--clothing",
                "red jacket",
                "--jurisdiction",
                "US-IL-COOK",
                "--time-from",
                "1994-09-02",
                "--time-to",
                "1995-12-31",
            ]
        )
    finally:
        sys.stdout = old
    assert rc == 0
    payload = json.loads(buf.getvalue())
    ids = {lead["notice_id"] for lead in payload["leads"]}
    assert "doe-cook-jane-marks" in ids
    assert "doe-cook-john-sex-mismatch" not in ids
    john = next(x for x in payload["excluded"] if x["notice_id"] == "doe-cook-john-sex-mismatch")
    assert john["reason"] == "sex_mismatch"


def test_notices_from_pins_reads_doe_descriptor():
    case = _elena()
    notices = notices_from_pins(case.pins)
    classes = {n.event_class for n in notices}
    assert "jane_doe_notice" in classes
    assert "john_doe_notice" in classes
    jane = next(n for n in notices if n.notice_id == "ev-3")
    assert jane.scars_marks == "tattoo left wrist"
    assert jane.sex == "female"


def test_map_api_doe_match():
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    import threading

    from mialock.map_ui import MapState, make_handler

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(MapState()))
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/people/subj-elena-cold-demo/doe-match")
        res = conn.getresponse()
        body = json.loads(res.read().decode())
        assert res.status == 200
        assert body["leads"]
        assert all(lead["rank_score"] <= 84 for lead in body["leads"])
        conn.close()
    finally:
        httpd.shutdown()
