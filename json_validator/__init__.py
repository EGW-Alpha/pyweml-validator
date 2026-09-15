"""JSON validation shipped alongside weml_validator in the weml-validator distribution."""

from json_validator.errors import ValidationError, ValidationResult
from json_validator.validators import validate_json_document, validate_json_element, validate_json_paragraph

__all__ = [
    "validate_json_document", "validate_json_paragraph", "validate_json_element",
    "ValidationResult", "ValidationError",
]
