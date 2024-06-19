import abc
from abc import ABC


class AttributeRule(ABC):
    @abc.abstractmethod
    def validate(self, value: str | None):
        """ do nothing"""


class AttributeRuleRequired(AttributeRule):
    def validate(self, value: str | None):
        return value is not None and value != ""


class AttributeRuleOptional(AttributeRule):
    def validate(self, value: str | None):
        return True


class AttributeRuleEnum(AttributeRule):
    def __init__(self, *allowed_values: str | None):
        self._allowed_values = allowed_values

    def validate(self, value: str | None):
        return value in self._allowed_values


class AttributeRuleMaxLength(AttributeRule):

    def __init__(self, max_length: int):
        super().__init__()
        self._max_length = max_length

    def validate(self, value: str | None):
        return value is None or len(value) <= self._max_length


__all__ = ["AttributeRule", "AttributeRuleRequired", "AttributeRuleOptional", "AttributeRuleEnum",
           "AttributeRuleMaxLength"]
