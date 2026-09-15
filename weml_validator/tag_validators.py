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

    def validate(self, tag: bs4.Tag, *, allow_extra_attributes: bool = False) -> ValidationResult:
        result = super().validate(tag, allow_extra_attributes=allow_extra_attributes)
        if tag.contents:
            result.add_node_error("Tag must be empty", tag)
        return result


class CombinedValidator(ValidatorBase):
    """Validator that combines multiple validators. One of the validators must pass for the tag to be valid"""

    def __init__(self, tag: str, *validators: ValidatorBase):
        super().__init__(tag, {})
        self._validators = validators

    @property
    def attribute_names(self) -> set[str]:
        return set().union(*(validator.attribute_names for validator in self._validators))

    def validate(self, tag: bs4.Tag, *, allow_extra_attributes: bool = False) -> ValidationResult:
        output_result = ValidationResult.success()
        for validator in self._validators:
            # A known attribute belonging to another alternative is not an
            # extension: e.g. an invalid href cannot hide behind the anchor branch.
            incompatible = set(tag.attrs) & (self.attribute_names - validator.attribute_names)
            if allow_extra_attributes and incompatible:
                output_result.add_node_error(f"Attributes incompatible with this tag form: {incompatible}", tag)
                continue
            result = validator.validate(tag, allow_extra_attributes=allow_extra_attributes)
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
                 expected_child_count: int | None = None,
                 minimum_child_count: int = 0,
                 required_any_attributes: tuple[str, ...] = ()):
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
        self._minimum_child_count = minimum_child_count
        self._required_any_attributes = required_any_attributes

    def validate(self, tag: bs4.Tag, *, allow_extra_attributes: bool = False) -> ValidationResult:
        result = super().validate(tag, allow_extra_attributes=allow_extra_attributes)
        children = tag.children

        if self._required_any_attributes and not any(name in tag.attrs for name in self._required_any_attributes):
            result.add_node_error(f"At least one attribute is required: {self._required_any_attributes}", tag)

        if self._is_unique:
            parents = tag.find_parents()
            if any(parent.name == tag.name for parent in parents):
                result.add_node_error(f"Tag must be unique", tag)
        children_count = {}
        for child in children:
            if isinstance(child, bs4.Comment):
                continue
            if isinstance(child, (bs4.Doctype, bs4.ProcessingInstruction, bs4.Declaration)):
                result.add_node_error("Declarations are not allowed inside WEML elements", tag)
                continue
            if isinstance(child, bs4.NavigableString):
                child_name = ""
                if child.strip() != "":
                    if "" not in self._allowed_children:
                        result.add_node_error(f"Text inside the tag is not allowed", tag)
            elif isinstance(child, bs4.Tag):
                child_name = child.name
                if child_name not in self._allowed_children:
                    result.add_node_error(f"Invalid child `{child_name}` (allowed {self._allowed_children})", tag)
                result = result.combine_with(ValidatorRepository.get_instance().validate(
                    child, allow_extra_attributes=allow_extra_attributes
                ))
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
        total_children = sum(count for name, count in children_count.items() if name)
        if total_children < self._minimum_child_count:
            result.add_node_error(f"Expected at least {self._minimum_child_count} child elements", tag)
        if self._expected_child_count is not None:
            if total_children != self._expected_child_count:
                result.add_node_error(
                    f"Invalid number of children. Got {total_children}, expected {self._expected_child_count}: "
                    f"{children_count}",
                    tag
                )

        return result
