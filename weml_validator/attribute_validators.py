import abc
import re
from abc import ABC
from urllib.parse import urlsplit

import bs4


class AttributeRule(ABC):
    @abc.abstractmethod
    def validate(self, value: str | None, tag: bs4.Tag):
        """ do nothing"""


class AttributeRuleRequired(AttributeRule):
    def validate(self, value: str | None, tag: bs4.Tag):
        return value is not None and value != ""


class AttributeRuleOptional(AttributeRule):
    def validate(self, value: str | None, tag: bs4.Tag):
        return True


class AttributeRuleEnum(AttributeRule):
    def __init__(self, *allowed_values: str | None):
        self._allowed_values = allowed_values

    def validate(self, value: str | None, tag: bs4.Tag):
        return value in self._allowed_values


class AttributeRuleMaxLength(AttributeRule):

    def __init__(self, max_length: int):
        super().__init__()
        self._max_length = max_length

    def validate(self, value: str | None, tag: bs4.Tag):
        return value is None or len(value) <= self._max_length


class AttributeRuleInteger(AttributeRule):
    def __init__(self, minimum: int | None = None, maximum: int | None = None):
        self._minimum = minimum
        self._maximum = maximum

    def validate(self, value: str | None, tag: bs4.Tag):
        if value is None:
            return True
        if re.fullmatch(r"[+-]?[0-9]+", value) is None:
            return False
        try:
            number = int(value)
        except ValueError:
            return False
        return ((self._minimum is None or number >= self._minimum)
                and (self._maximum is None or number <= self._maximum))


class AttributeRuleColor(AttributeRule):
    def validate(self, value: str | None, tag: bs4.Tag):
        return value is None or re.fullmatch(
            r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value
        ) is not None


class AttributeRuleLanguage(AttributeRule):
    """Check BCP 47 syntax without looking up EGW or IANA language registries."""

    _pattern = re.compile(
        r"(?:[a-z]{2,3}(?:-[a-z]{3}){0,3}|[a-z]{4,8})"
        r"(?:-[a-z]{4})?(?:-[a-z]{2}|-[0-9]{3})?"
        r"(?P<variants>(?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*)"
        r"(?P<extensions>(?:-[0-9a-wy-z](?:-[a-z0-9]{2,8})+)*)"
        r"(?:-x(?:-[a-z0-9]{1,8})+)?", re.IGNORECASE | re.ASCII
    )
    _grandfathered = {
        "en-gb-oed", "i-ami", "i-bnn", "i-default", "i-enochian", "i-hak",
        "i-klingon", "i-lux", "i-mingo", "i-navajo", "i-pwn", "i-tao", "i-tay",
        "i-tsu", "sgn-be-fr", "sgn-be-nl", "sgn-ch-de", "art-lojban", "cel-gaulish",
        "no-bok", "no-nyn", "zh-guoyu", "zh-hakka", "zh-min", "zh-min-nan", "zh-xiang",
    }

    def validate(self, value: str | None, tag: bs4.Tag):
        if value is None:
            return True
        value = value.lower()
        if value in self._grandfathered or re.fullmatch(r"x(?:-[a-z0-9]{1,8})+", value):
            return True
        match = self._pattern.fullmatch(value)
        if match is None:
            return False
        variants = match["variants"].split("-")[1:]
        extensions = [part for part in match["extensions"].split("-") if len(part) == 1]
        return len(variants) == len(set(variants)) and len(extensions) == len(set(extensions))


class AttributeRuleLink(AttributeRule):
    """Validate supported absolute HTTP, email, and EGW links."""

    def validate(self, value: str | None, tag: bs4.Tag):
        if value is None:
            return True
        if not value or re.search(r"[\s<>\\]", value) or re.search(r"%(?![0-9a-fA-F]{2})", value):
            return False
        try:
            uri = urlsplit(value)
            if uri.scheme in {"http", "https"}:
                return bool(uri.hostname) and (uri.port is None or 0 < uri.port <= 65535)
            if uri.scheme == "mailto":
                return re.fullmatch(r"[^@/]+@[^@/]+", uri.path) is not None
            if uri.scheme == "egw":
                if uri.netloc in {"book", "bible"}:
                    return re.fullmatch(r"/[0-9]+\.[0-9]+", uri.path) is not None
                return uri.netloc == "missing" and len(uri.path) > 1
        except ValueError:
            return False
        return False


class AttributeRuleListMarker(AttributeRule):

    def validate(self, value: str | None, tag: bs4.Tag):
        t = tag.attrs.get("type", None)
        marker = tag.attrs.get("marker", None)
        if t is not None and t == "ordered":
            if marker is not None and re.fullmatch("[1aAiI]", marker) is None:
                return False
        return True


class AttributeRuleListStart(AttributeRule):

    def validate(self, value: str | None, tag: bs4.Tag):
        t = tag.attrs.get("type", None)
        start = tag.attrs.get("start", None)
        if t is not None and t == "ordered":
            if start is not None and re.fullmatch(r"[0-9]+", start) is None:
                return False
        return True


__all__ = ["AttributeRule", "AttributeRuleRequired", "AttributeRuleOptional", "AttributeRuleEnum",
           "AttributeRuleMaxLength", "AttributeRuleListMarker", "AttributeRuleListStart",
           "AttributeRuleInteger", "AttributeRuleColor", "AttributeRuleLanguage", "AttributeRuleLink"]
