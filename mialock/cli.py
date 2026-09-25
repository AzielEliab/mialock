"""CLI for M.I.A.Lock map, casebook, and cold-case / archive search options."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from mialock import __version__
from mialock.coverage import coverage_report
from mialock.doe import Descriptor, match_descriptors, match_subject
from mialock.human import (
    format_coverage,
    format_doe,
    format_geojson,
    format_modes,
    format_people,
    format_queries,
)
from mialock.map_ui import DEFAULT_HOST, DEFAULT_PORT, serve
from mialock.models import casebook_index, load_casebook
from mialock.search_options import list_search_modes, render_queries

HELP = f"""\
mialock — map one person's documented events

usage:
  mialock [--json] <command> [<args>]

See when and where a person's documented events happened, and how long
each one lasted.

Author: Aziel Eliab

Start here
  ui               Open the local map
  map              Same as ui
  people           List people in the casebook

Advanced
  search-options   List search modes
  queries          Write search text for a mode
  doe-match        Rank Doe notices as leads to check
  coverage         Show which sources were searched
  geojson          Export one person's map data

Options
  -h, --help       Show this help
  --version        Show the version ({__version__})
  --json           Print machine-readable JSON

Examples
  mialock
  mialock ui
  mialock people
  mialock doe-match --subject subj-elena-cold-demo
  mialock people --json
"""

WELCOME = """\
M.I.A.Lock maps one person's documented events — the date, the time, the place, and how long each event lasted.

Open the map:
  mialock ui

Then open the address it prints (http://127.0.0.1:8765/ by default).

Also:
  mialock people     who is in the sample casebook
  mialock --help     every command

Author: Aziel Eliab
"""

COMMAND_HELP = {
    "ui": """\
mialock ui — open the local map

usage:
  mialock ui [--host HOST] [--port PORT] [--casebook PATH]

Serves the map and prints the address to open.
The default host is 127.0.0.1 and the default port is 8765.

Examples
  mialock ui
  mialock ui --port 8765
""",
    "map": """\
mialock map — open the local map

usage:
  mialock map [--host HOST] [--port PORT] [--casebook PATH]

Same as mialock ui.

Examples
  mialock map
""",
    "people": """\
mialock people — list people in the casebook

usage:
  mialock people [--casebook PATH] [--json]

Examples
  mialock people
  mialock people --json
""",
    "search-options": """\
mialock search-options — list search modes

usage:
  mialock search-options [--json]

Examples
  mialock search-options
  mialock search-options --json
""",
    "queries": """\
mialock queries — write search text for a mode

usage:
  mialock queries <mode> [--name NAME] [--jurisdiction TEXT] [--json]

Modes include active, archives, doe_cold, and cold_missing.

Examples
  mialock queries archives
  mialock queries doe_cold --name "Elena Vargas" --json
""",
    "doe-match": """\
mialock doe-match — rank Doe notices as leads to check

usage:
  mialock doe-match [--subject ID] [--casebook PATH] [--json]

A lead is something to verify with the source record.

Examples
  mialock doe-match --subject subj-elena-cold-demo
  mialock doe-match --subject subj-elena-cold-demo --json
""",
    "coverage": """\
mialock coverage — show which sources were searched

usage:
  mialock coverage [--subject ID] [--casebook PATH] [--json]

Examples
  mialock coverage
  mialock coverage --subject subj-elena-cold-demo --json
""",
    "geojson": """\
mialock geojson — export one person's map data

usage:
  mialock geojson <person-id> [--mode MODE] [-o FILE] [--json]

Without --json, the terminal shows a short summary.
--json prints GeoJSON. -o writes GeoJSON to a file.

Examples
  mialock geojson subj-elena-cold-demo
  mialock geojson subj-elena-cold-demo --json
  mialock geojson subj-elena-cold-demo -o events.geojson
""",
}


class MiaArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return HELP if HELP.endswith("\n") else HELP + "\n"

    def error(self, message: str) -> None:
        self.exit(2, human_arg_error(message) + "\n")


def human_arg_error(message: str) -> str:
    choice = re.search(r"invalid choice: '([^']+)'", message)
    if choice and "argument cmd" in message:
        bad = choice.group(1)
        return f'Unknown command "{bad}". Try: mialock ui   or   mialock --help'
    required = re.search(r"the following arguments are required: (.+)", message)
    if required:
        missing = required.group(1).strip()
        if "subject_id" in missing:
            return "Name the person for geojson. Try: mialock people"
        if missing == "mode":
            return "Name a search mode. Try: mialock search-options"
        return f"Missing {missing}. Try: mialock --help"
    if message.startswith("unrecognized arguments:"):
        extra = message.split(":", 1)[1].strip()
        return f'Unknown option {extra}. Try: mialock --help'
    if "invalid int value" in message and "--port" in message:
        return "That port is not a whole number. Try: mialock ui --port 8765"
    return f"{message}. Try: mialock --help"


def _say(reason: str, hint: str, code: int = 1) -> None:
    if hint.startswith("Try:"):
        print(f"{reason} {hint}", file=sys.stderr)
    else:
        print(f"{reason} Try: {hint}", file=sys.stderr)
    raise SystemExit(code)


def _emit(text: str, payload: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    print(text, end="" if text.endswith("\n") else "\n")


def _load_cases(path: Path | None) -> list:
    try:
        return load_casebook(path)
    except FileNotFoundError:
        shown = path if path is not None else "the packaged casebook"
        _say(f"No casebook at {shown}.", "mialock people")
    except json.JSONDecodeError:
        _say("That casebook file is not valid JSON.", "mialock people")
    except ValueError as exc:
        _say(str(exc), "mialock people")
    except OSError as exc:
        detail = exc.strerror or str(exc)
        _say(f"Could not read the casebook ({detail}).", "mialock people")
    raise AssertionError("unreachable")


def _require_person(cases: list, subject_id: str):
    match = next((case for case in cases if case.subject_id == subject_id), None)
    if match is None:
        _say(f'Unknown person "{subject_id}".', "mialock people")
    return match


def _build_parser() -> MiaArgumentParser:
    parser = MiaArgumentParser(prog="mialock", add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="cmd")

    def serve_parser(name: str) -> None:
        command = sub.add_parser(name, add_help=False)
        command.add_argument("--host", default=DEFAULT_HOST)
        command.add_argument("--port", type=int, default=DEFAULT_PORT)
        command.add_argument("--casebook", type=Path, default=None)

    serve_parser("ui")
    serve_parser("map")

    people = sub.add_parser("people", add_help=False)
    people.add_argument("--casebook", type=Path, default=None)

    geo = sub.add_parser("geojson", add_help=False)
    geo.add_argument("subject_id")
    geo.add_argument("--casebook", type=Path, default=None)
    geo.add_argument(
        "--mode",
        default="all",
        help="Search mode filter: all|active|archives|doe_cold|cold_missing",
    )
    geo.add_argument("-o", "--output", type=Path, default=None)
    geo.add_argument(
        "--ellipses",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include uncertainty ellipse polygons (default: yes)",
    )
    geo.add_argument(
        "--coverage",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include coverage-heat cells in the GeoJSON",
    )

    sub.add_parser("search-options", add_help=False)

    queries = sub.add_parser("queries", add_help=False)
    queries.add_argument("mode")
    queries.add_argument("--name", default="Christina Green")
    queries.add_argument("--aliases", default='"Christy Green" OR "Tina Green"')
    queries.add_argument("--jurisdiction", default="Illinois")
    queries.add_argument("--year-from", default="1990")
    queries.add_argument("--year-to", default="1999")
    queries.add_argument("--age-band", default="20-30")
    queries.add_argument("--sex", default="female")

    doe = sub.add_parser("doe-match", add_help=False)
    doe.add_argument("--casebook", type=Path, default=None)
    doe.add_argument("--subject", default="", help="Subject id in the casebook")
    doe.add_argument("--notices", type=Path, default=None, help="Extra notices JSON")
    doe.add_argument(
        "--no-sample-notices",
        action="store_true",
        help="Do not merge packaged sample_doe_notices.json",
    )
    doe.add_argument("--age-band", default="")
    doe.add_argument("--sex", default="")
    doe.add_argument("--height-cm", default="")
    doe.add_argument("--height-band", default="")
    doe.add_argument("--build", default="")
    doe.add_argument("--scars-marks", default="")
    doe.add_argument("--clothing", default="")
    doe.add_argument("--jurisdiction", default="")
    doe.add_argument("--time-from", default="")
    doe.add_argument("--time-to", default="")

    coverage = sub.add_parser("coverage", add_help=False)
    coverage.add_argument("--casebook", type=Path, default=None)
    coverage.add_argument("--subject", default="", help="Subject id (default: all)")
    return parser


def _strip_global(argv: list[str]) -> tuple[list[str], bool]:
    kept: list[str] = []
    as_json = False
    for arg in argv:
        if arg == "--json":
            as_json = True
        else:
            kept.append(arg)
    return kept, as_json


def _dispatch(args: argparse.Namespace, as_json: bool) -> int:
    if args.cmd in {"ui", "map"}:
        serve(host=args.host, port=args.port, casebook=args.casebook)
        return 0

    if args.cmd == "search-options":
        payload = {"modes": list_search_modes()}
        _emit(format_modes(payload), payload, as_json)
        return 0

    if args.cmd == "queries":
        try:
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
        except KeyError:
            _say(f'Unknown search mode "{args.mode}".', "mialock search-options")
        _emit(format_queries(payload), payload, as_json)
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
            cases = _load_cases(args.casebook)
            match = _require_person(cases, args.subject)
            if any(overrides.values()):
                merged = dict(match.descriptor or {})
                merged.update({key: value for key, value in overrides.items() if value})
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
                _say(
                    "No Doe notices to compare.",
                    "mialock doe-match --subject subj-elena-cold-demo",
                )
            payload = match_descriptors(subject, notices)
        _emit(format_doe(payload), payload, as_json)
        return 0

    if args.cmd == "coverage":
        cases = _load_cases(args.casebook)
        if args.subject:
            match = _require_person(cases, args.subject)
            payload = coverage_report(match)
        else:
            payload = {
                "framing": (
                    "Heat = search coverage intensity / negative-evidence weight — "
                    "not a probability of presence."
                ),
                "reports": [coverage_report(case) for case in cases],
            }
        _emit(format_coverage(payload), payload, as_json)
        return 0

    cases = _load_cases(getattr(args, "casebook", None))
    if args.cmd == "people":
        payload = casebook_index(cases)
        _emit(format_people(payload), payload, as_json)
        return 0

    if args.cmd == "geojson":
        match = _require_person(cases, args.subject_id)
        try:
            payload = match.to_geojson(
                args.mode,
                include_ellipses=args.ellipses,
                include_coverage=args.coverage,
            )
        except KeyError:
            _say(f'Unknown search mode "{args.mode}".', "mialock search-options")
        if args.output:
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            if not as_json:
                points = sum(
                    1
                    for feature in payload.get("features") or []
                    if (feature.get("geometry") or {}).get("type") == "Point"
                    and (feature.get("properties") or {}).get("kind") != "coverage_cell"
                )
                print(f"Wrote {args.output} ({points} event pins).")
            return 0
        _emit(format_geojson(payload), payload, as_json)
        return 0

    print(WELCOME, end="" if WELCOME.endswith("\n") else "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        print(WELCOME, end="" if WELCOME.endswith("\n") else "\n")
        return 0
    if raw[0] in {"-h", "--help"}:
        print(HELP, end="" if HELP.endswith("\n") else "\n")
        return 0
    if raw[0] in {"--version", "-V"} or raw == ["--version"]:
        print(f"mialock {__version__}")
        return 0

    cleaned, as_json = _strip_global(raw)
    if not cleaned:
        if as_json:
            print(
                json.dumps(
                    {
                        "product": "mialock",
                        "version": __version__,
                        "author": "Aziel Eliab",
                        "next": ["mialock ui", "mialock people", "mialock --help"],
                    },
                    indent=2,
                )
            )
            return 0
        print(WELCOME, end="" if WELCOME.endswith("\n") else "\n")
        return 0
    if "--version" in cleaned or "-V" in cleaned:
        print(f"mialock {__version__}")
        return 0
    if cleaned[0] in COMMAND_HELP and any(flag in cleaned[1:] for flag in ("-h", "--help")):
        text = COMMAND_HELP[cleaned[0]]
        print(text, end="" if text.endswith("\n") else "\n")
        return 0
    if "-h" in cleaned or "--help" in cleaned:
        print(HELP, end="" if HELP.endswith("\n") else "\n")
        return 0

    parser = _build_parser()
    try:
        args = parser.parse_args(cleaned)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    if getattr(args, "version", False):
        print(f"mialock {__version__}")
        return 0
    if getattr(args, "help", False):
        print(HELP, end="" if HELP.endswith("\n") else "\n")
        return 0
    as_json = as_json or bool(getattr(args, "json", False))
    try:
        return _dispatch(args, as_json)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
