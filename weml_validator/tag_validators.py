from typing import Callable

import bs4

from weml_validator import ValidationResult
from weml_validator.attribute_validators import AttributeRule
from weml_validator.repository import ValidatorRepository, ValidatorBase


class EmptyTagValidator(ValidatorBase):
    """Validator for tags that must be empty"""

    def __init__(self, tag, attribute_rules: dict[str, list[AttributeRule]] = None):
        """Create a new EmptyTagValidator
        :param tag: The tag name
        :param attribute_rules: A dictionary of attribute rules. The key is the attribute name, the value is a list of
            AttributeRule objects
        """
        super().__init__(tag, attribute_rules or {})

    def validate(self, tag: bs4.Tag) -> ValidationResult:
        result = super().validate(tag)
        if tag.contents:
            result.add_node_error("Tag must be empty", tag)
        return result


class CombinedValidator(ValidatorBase):
    """Validator that combines multiple validators. One of the validators must pass for the tag to be valid"""

    def __init__(self, tag: str, *validators: ValidatorBase):
        super().__init__(tag, {})
        self._validators = validators

    def validate(self, tag: bs4.Tag) -> ValidationResult:
        output_result = ValidationResult.success()
        for validator in self._validators:
            result = validator.validate(tag)
            if result.is_valid:
                return ValidationResult.success()
            output_result = output_result.combine_with(result)
        return output_result


class ChildrenSubsetValidator(ValidatorBase):

    def __init__(self, tag,
                 allowed_children: list[str],
                 attribute_rules: dict[str, list[AttributeRule]] | None = None,
                 required_children: dict[str, int | None | Callable[[int], bool]] | None = None,
                 unique=False,
                 expected_child_count: int | None = None):
        """ Create a new ChildrenSubsetValidator
        :param tag: The tag name
        :param attribute_rules: A dictionary of attribute rules. The key is the attribute name, the value is a list of
            AttributeRule objects
        :param allowed_children: A list of allowed children tag names. Empty string represents text nodes
        :param required_children: A dictionary of required children. The key is the child tag name, the value is the
            number of required children. If the value is None, at least one child is required
        :param unique: If true, this tag cannot have any parent with the same tag name
        """
        super().__init__(tag, attribute_rules or {})
        self._allowed_children = allowed_children
        self._required_children = required_children or {}
        self._is_unique = unique
        self._expected_child_count = expected_child_count

    def validate(self, tag: bs4.Tag) -> ValidationResult:
        result = super().validate(tag)
        children = tag.children

        if self._is_unique:
            parents = tag.find_parents()
            if any(parent.name == tag.name for parent in parents):
                result.add_node_error(f"Tag must be unique", tag)
        children_count = {}
        for child in children:
            if isinstance(child, bs4.NavigableString):
                child_name = ""
                if child.strip() != "":
                    if "" not in self._allowed_children:
                        result.add_node_error(f"Text inside the tag is not allowed", tag)
            elif isinstance(child, bs4.Tag):
                child_name = child.name
                if child_name not in self._allowed_children:
                    result.add_node_error(f"Invalid child `{child_name}` (allowed {self._allowed_children})", tag)
                result = result.combine_with(ValidatorRepository.get_instance().validate(child))
            else:  # pragma: no cover
                # todo: How to test this?
                continue
            children_count[child_name] = children_count.get(child_name, 0) + 1
        for child_name, expected_count in self._required_children.items():
            if expected_count is None:
                if child_name not in children_count:
                    result.add_node_error(f"Required child `{child_name}` missing", tag)

            elif isinstance(expected_count, int):
                if children_count.get(child_name, 0) != expected_count:
                    result.add_node_error(f"Required child `{child_name}` missing", tag)
            elif callable(expected_count):
                if not expected_count(children_count.get(child_name, 0)):
                    result.add_node_error(f"Required child `{child_name}` missing", tag)
        if self._expected_child_count is not None:
            total_children = 0
            for count in (val for c, val in children_count.items() if c):
                total_children += count
            if total_children != self._expected_child_count:
                result.add_node_error(
                    f"Invalid number of children. Got {total_children}, expected {self._expected_child_count}: "
                    f"{children_count}",
                    tag
                )

        return result
