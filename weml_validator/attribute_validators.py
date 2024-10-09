import abc
import re
from abc import ABC

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


class AttributeRuleListMarker(AttributeRule):

    def validate(self, value: str | None, tag: bs4.Tag):
        t = tag.attrs.get("type", None)
        marker = tag.attrs.get("marker", None)
        if t is not None and t == "ordered":
            if marker is not None and re.match("^[1aAiI]$", marker) is None:
                return False
        return True


class AttributeRuleListStart(AttributeRule):

    def validate(self, value: str | None, tag: bs4.Tag):
        t = tag.attrs.get("type", None)
        start = tag.attrs.get("start", None)
        if t is not None and t == "ordered":
            if start is not None and not start.isdigit():
                return False
        return True


__all__ = ["AttributeRule", "AttributeRuleRequired", "AttributeRuleOptional", "AttributeRuleEnum",
           "AttributeRuleMaxLength", "AttributeRuleListMarker", "AttributeRuleListStart"]
