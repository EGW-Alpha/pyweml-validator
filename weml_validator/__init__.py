import bs4

from weml_validator.errors import ValidationResult, ValidationError
from weml_validator.validators import validator_instance
from weml_validator.document_validators import validate_document


def validate_weml_document(document: str, *, allow_extra_attributes: bool = False) -> ValidationResult:
    return validate_document(document, allow_extra_attributes=allow_extra_attributes)


def validate_weml_paragraph(node_html: str, *, allow_extra_attributes: bool = False) -> ValidationResult:
    content = bs4.BeautifulSoup(node_html, "html.parser")
    wrapper = content.new_tag("div", sourceline=1, sourcepos=0)
    for node in list(content.contents):
        wrapper.append(node.extract())
    return validator_instance.validate(wrapper, allow_extra_attributes=allow_extra_attributes)


def validate_weml_element(node_html: str, *, allow_extra_attributes: bool = False) -> ValidationResult:
    content = bs4.BeautifulSoup(node_html, "html.parser")
    result = ValidationResult.success()
    element_count = 0
    for node in content:
        if isinstance(node, bs4.Comment):
            continue
        if isinstance(node, bs4.Tag):
            element_count += 1
            result = result.combine_with(validator_instance.validate(node, allow_extra_attributes=allow_extra_attributes))
        elif isinstance(node, bs4.Doctype) or str(node).strip():
            result.add_node_error("Expected a WEML element, found text or declaration", content)
    if not element_count:
        result.add_node_error("At least one WEML element is required", content)
    return result


__all__ = ["validate_weml_document", "validate_weml_paragraph", "validate_weml_element",
           "ValidationResult", "ValidationError"]
