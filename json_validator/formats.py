"""JSON-specific semantic formats; WEML attribute rules have different constraints."""

import re
from urllib.parse import urlsplit

from jsonschema import FormatChecker


format_checker = FormatChecker()


@format_checker.checks("weml-link", raises=ValueError)
def is_weml_link(value: object) -> bool:
    if not isinstance(value, str):
        return True  # The schema's type keyword reports non-string input.
    if not value or re.search(r"[\s<>\\\x00-\x1f\x7f]", value) or re.search(r"%(?![0-9a-fA-F]{2})", value):
        return False
    uri = urlsplit(value)
    if uri.scheme in {"http", "https"}:
        return bool(uri.hostname) and (uri.port is None or 0 < uri.port <= 65535)
    if uri.scheme == "mailto":
        return not uri.netloc and re.fullmatch(r"[^@/]+@[^@/]+", uri.path) is not None
    if uri.scheme != "egw" or uri.query:
        return False
    if uri.netloc.lower() == "missing":
        return len(uri.path) > 1
    if uri.netloc.lower() not in {"book", "bible"}:
        return False
    match = re.fullmatch(r"/([+-]?[0-9]+)\.([+-]?[0-9]+)", uri.path)
    return match is not None and all(-2147483648 <= int(part) <= 2147483647 for part in match.groups())
