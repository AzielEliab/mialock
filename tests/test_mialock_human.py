"""Human CLI defaults. --json keeps the machine payload."""

from __future__ import annotations

import json
from io import StringIO

from mialock.cli import main


def _run(argv: list[str]) -> tuple[int, str, str]:
    import sys

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def test_bare_command_welcomes_a_person():
    code, out, err = _run([])
    assert code == 0
    assert err == ""
    assert "mialock ui" in out
    assert "Aziel Eliab" in out
    assert not out.lstrip().startswith("{")
    assert "what this is not" not in out.lower()


def test_help_is_short_and_lists_examples():
    code, out, err = _run(["--help"])
    assert code == 0
    assert err == ""
    assert "Start here" in out
    assert "Advanced" in out
    assert "Examples" in out
    assert "mialock ui" in out
    assert "--json" in out
    assert "the following arguments are required" not in out
    assert "changelog" not in out.lower()


def test_unknown_command_has_a_next_step():
    code, out, err = _run(["bogus"])
    assert code == 2
    assert out == ""
    assert 'Unknown command "bogus".' in err
    assert "mialock ui" in err
    assert "mialock --help" in err
    assert "Traceback" not in err


def test_unknown_person_has_a_next_step():
    code, out, err = _run(["people", "--casebook", "missing-casebook.json"])
    assert code == 1
    assert "Try: mialock people" in err
    assert "Traceback" not in err

    code, out, err = _run(["coverage", "--subject", "nobody"])
    assert code == 1
    assert 'Unknown person "nobody".' in err
    assert "Try: mialock people" in err


def test_unknown_search_mode_has_a_next_step():
    code, out, err = _run(["queries", "not-a-mode"])
    assert code == 1
    assert 'Unknown search mode "not-a-mode".' in err
    assert "Try: mialock search-options" in err
    assert "Traceback" not in err


def test_people_human_and_json():
    code, out, err = _run(["people"])
    assert code == 0
    assert err == ""
    assert "Christina Green" in out
    assert "Next: mialock ui" in out
    assert not out.lstrip().startswith("{")

    code, raw, err = _run(["people", "--json"])
    assert code == 0
    assert err == ""
    payload = json.loads(raw)
    assert payload["people"]
    assert payload["people"][0]["subject_id"]


def test_doe_match_json_shape_unchanged():
    code, raw, err = _run(["doe-match", "--subject", "subj-elena-cold-demo", "--json"])
    assert code == 0
    assert err == ""
    payload = json.loads(raw)
    assert payload["leads"]
    assert "rank_score" in payload["leads"][0]
    assert "warning" in payload

    code, out, err = _run(["doe-match", "--subject", "subj-elena-cold-demo"])
    assert code == 0
    assert "compatibility lead" in out.lower()
    assert "rank_score" not in out
    assert not out.lstrip().startswith("{")
