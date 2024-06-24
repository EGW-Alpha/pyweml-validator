import bs4

from weml_validator.errors import ValidationResult, ValidationError
from weml_validator.validators import validator_instance


def validate_weml_document(document: str) -> ValidationResult:  # pragma: no cover
    # Not implemented yet
    return ValidationResult(False, [])


def validate_weml_paragraph(node_html: str) -> ValidationResult:
    div_content = f"<div>\n{node_html}\n</div>"
    validation_result = validate_weml_element(div_content)
    for error in validation_result.errors:
        error.line -= 1
    return validation_result


def validate_weml_element(node_html: str) -> ValidationResult:
    content = bs4.BeautifulSoup(node_html, "html.parser")
    for node in content:
        result = validator_instance.validate(node)
        if not result:
            return result
    return ValidationResult(True, [])


__all__ = ["validate_weml_document", "validate_weml_paragraph", "validate_weml_element",
           "ValidationResult", "ValidationError"]
