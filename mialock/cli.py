"""CLI for M.I.A.Lock map, casebook, and cold-case / archive search options."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mialock import __version__
from mialock.coverage import coverage_report
from mialock.doe import Descriptor, match_descriptors, match_subject
from mialock.map_ui import DEFAULT_HOST, DEFAULT_PORT, serve
from mialock.models import casebook_index, load_casebook
from mialock.search_options import list_search_modes, render_queries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mialock",
        description=(
            "M.I.A.Lock — per-person historical event map "
            "(date × time × event × duration), Doe descriptor matching, "
            "uncertainty ellipses, and coverage-heat layers."
        ),
    )
    parser.add_argument("--version", action="version", version=f"mialock {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    map_p = sub.add_parser("map", help="Open localhost map UI for each person's pins")
    map_p.add_argument("--host", default=DEFAULT_HOST)
    map_p.add_argument("--port", type=int, default=DEFAULT_PORT)
    map_p.add_argument(
        "--casebook",
        type=Path,
        default=None,
        help="JSON casebook path (default: packaged sample_persons.json)",
    )

    list_p = sub.add_parser("people", help="List subjects in a casebook")
    list_p.add_argument("--casebook", type=Path, default=None)

    geo_p = sub.add_parser("geojson", help="Export one subject's GeoJSON")
    geo_p.add_argument("subject_id")
    geo_p.add_argument("--casebook", type=Path, default=None)
    geo_p.add_argument(
        "--mode",
        default="all",
        help="Search mode filter: all|active|archives|doe_cold|cold_missing",
    )
    geo_p.add_argument("-o", "--output", type=Path, default=None)
    geo_p.add_argument(
        "--ellipses",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include uncertainty ellipse polygons (default: yes)",
    )
    geo_p.add_argument(
        "--coverage",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include coverage-heat cells in the GeoJSON",
    )

    sub.add_parser(
        "search-options",
        help="List archive / Doe / cold-case search modes",
    )

    q_p = sub.add_parser("queries", help="Render query families for a search mode")
    q_p.add_argument(
        "mode",
        help="active | archives | doe_cold | cold_missing",
    )
    q_p.add_argument("--name", default="Christina Green")
    q_p.add_argument("--aliases", default='"Christy Green" OR "Tina Green"')
    q_p.add_argument("--jurisdiction", default="Illinois")
    q_p.add_argument("--year-from", default="1990")
    q_p.add_argument("--year-to", default="1999")
    q_p.add_argument("--age-band", default="20-30")
    q_p.add_argument("--sex", default="female")

    doe_p = sub.add_parser(
        "doe-match",
        help="Rank Doe / unidentified notices as compatibility leads (never an ID)",
    )
    doe_p.add_argument("--casebook", type=Path, default=None)
    doe_p.add_argument("--subject", default="", help="Subject id in the casebook")
    doe_p.add_argument("--notices", type=Path, default=None, help="Extra notices JSON")
    doe_p.add_argument(
        "--no-sample-notices",
        action="store_true",
        help="Do not merge packaged sample_doe_notices.json",
    )
    doe_p.add_argument("--age-band", default="")
    doe_p.add_argument("--sex", default="")
    doe_p.add_argument("--height-cm", default="")
    doe_p.add_argument("--height-band", default="")
    doe_p.add_argument("--build", default="")
    doe_p.add_argument("--scars-marks", default="")
    doe_p.add_argument("--clothing", default="")
    doe_p.add_argument("--jurisdiction", default="")
    doe_p.add_argument("--time-from", default="")
    doe_p.add_argument("--time-to", default="")

    cov_p = sub.add_parser(
        "coverage",
        help="Adapter coverage report (search intensity / dead-ends — not presence)",
    )
    cov_p.add_argument("--casebook", type=Path, default=None)
    cov_p.add_argument("--subject", default="", help="Subject id (default: all)")

    args = parser.parse_args(argv)

    if args.cmd == "map":
        serve(host=args.host, port=args.port, casebook=args.casebook)
        return 0

    if args.cmd == "search-options":
        print(json.dumps({"modes": list_search_modes()}, indent=2))
        return 0

    if args.cmd == "queries":
        payload = render_queries(
            args.mode,
            name=args.name,
            aliases=args.aliases,
            jurisdiction=args.jurisdiction,
            year_from=args.year_from,
            year_to=args.year_to,
            age_band=args.age_band,
            sex=args.sex,
            decade=f"{args.year_from[:3]}0s" if args.year_from[:4].isdigit() else "{decade}",
        )
        print(json.dumps(payload, indent=2))
        return 0

    if args.cmd == "doe-match":
        overrides = {
            "age_band": args.age_band,
            "sex": args.sex,
            "height_cm": args.height_cm,
            "height_band": args.height_band,
            "build": args.build,
            "scars_marks": args.scars_marks,
            "clothing": args.clothing,
            "jurisdiction": args.jurisdiction,
            "time_window_from": args.time_from,
            "time_window_to": args.time_to,
        }
        if args.subject:
            cases = load_casebook(args.casebook)
            match = next((c for c in cases if c.subject_id == args.subject), None)
            if match is None:
                print(f"unknown subject: {args.subject}", file=sys.stderr)
                return 1
            if any(overrides.values()):
                merged = dict(match.descriptor or {})
                merged.update({k: v for k, v in overrides.items() if v})
                match.descriptor = merged
            payload = match_subject(
                match,
                include_sample_notices=not args.no_sample_notices,
                notices_path=args.notices,
            )
        else:
            from mialock.doe import load_sample_notices

            subject = Descriptor.from_mapping(overrides)
            notices = load_sample_notices(args.notices)
            if not notices:
                print("no Doe notices to match (pass --subject or --notices)", file=sys.stderr)
                return 1
            payload = match_descriptors(subject, notices)
        print(json.dumps(payload, indent=2))
        return 0

    if args.cmd == "coverage":
        cases = load_casebook(args.casebook)
        if args.subject:
            match = next((c for c in cases if c.subject_id == args.subject), None)
            if match is None:
                print(f"unknown subject: {args.subject}", file=sys.stderr)
                return 1
            print(json.dumps(coverage_report(match), indent=2))
            return 0
        print(
            json.dumps(
                {
                    "framing": (
                        "Heat = search coverage intensity / negative-evidence weight — "
                        "not a probability of presence."
                    ),
                    "reports": [coverage_report(c) for c in cases],
                },
                indent=2,
            )
        )
        return 0

    cases = load_casebook(args.casebook)
    if args.cmd == "people":
        print(json.dumps(casebook_index(cases), indent=2))
        return 0

    if args.cmd == "geojson":
        match = next((c for c in cases if c.subject_id == args.subject_id), None)
        if match is None:
            print(f"unknown subject: {args.subject_id}", file=sys.stderr)
            return 1
        payload = json.dumps(
            match.to_geojson(
                args.mode,
                include_ellipses=args.ellipses,
                include_coverage=args.coverage,
            ),
            indent=2,
        )
        if args.output:
            args.output.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
