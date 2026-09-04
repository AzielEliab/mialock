"""M.I.A.Lock — missing-person event map and evidence models."""

from __future__ import annotations

__version__ = "0.1.1"
__all__ = [
    "__version__",
    "load_casebook",
    "PersonCase",
    "EventPin",
    "match_descriptors",
    "match_subject",
    "coverage_report",
]

from mialock.coverage import coverage_report
from mialock.doe import match_descriptors, match_subject
from mialock.models import EventPin, PersonCase, load_casebook
