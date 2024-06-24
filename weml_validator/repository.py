import bs4

from weml_validator import ValidationResult, ValidationError
from weml_validator.attribute_validators import AttributeRule


class ValidatorBase:
    def __init__(self, tag, attribute_rules: dict[str, list[AttributeRule]]):
        self._tag = tag
        self._attribute_rules = attribute_rules

    @property
    def tag(self):
        return self._tag

    def validate(self, tag: bs4.Tag) -> ValidationResult:
        result = ValidationResult.success()
        if tag.name != self.tag:  # pragma: no cover
            result.add_node_error("Invalid tag", tag)
        existing_attrs = set(tag.attrs.keys())
        for attr, rule_set in self._attribute_rules.items():
            existing_attrs.discard(attr)
            attr_value = tag.attrs.get(attr, None)
            for rule in rule_set:
                if not rule.validate(attr_value):
                    result.add_node_error(f"Attribute {attr} failed validation with rule: {rule}", tag)
        if len(existing_attrs) > 0:
            result.add_node_error(f"Unexpected attributes: {existing_attrs}", tag)
        return result


class ValidatorRepository:
    def __init__(self):
        self._validators = {}

    def add_validator(self, validator: ValidatorBase):
        self._validators[validator.tag] = validator

    def get_validator(self, tag: str) -> ValidatorBase:
        return self._validators[tag]

    def validate(self, element: bs4.Tag) -> ValidationResult:
        tag = element.name
        if tag not in self._validators:
            return ValidationResult(False, [ValidationError(tag, 0, 0)])
        validator = self.get_validator(tag)
        return validator.validate(element)

    @classmethod
    def get_instance(cls):
        return _instance


_instance = ValidatorRepository()

__all__ = ["ValidatorRepository", "ValidatorBase"]
