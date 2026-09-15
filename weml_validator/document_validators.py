"""Validation of WEML interchange documents."""

from uuid import UUID

import bs4

from weml_validator.attribute_validators import (
    AttributeRuleEnum, AttributeRuleInteger, AttributeRuleLanguage, AttributeRuleRequired,
)
from weml_validator.errors import ValidationResult
from weml_validator.repository import ValidatorBase
from weml_validator.validators import validator_instance


PUBLICATION_TYPES = (
    "bible", "bible-commentary", "book", "devotional", "dictionary", "manuscript-volume",
    "periodical/page-break", "periodical/no-page-break", "topical-index", "scripture-index",
)
METADATA_NAMES = {
    "pubid", "original-id", "code", "type", "author", "publication-year",
    "publication-start-year", "publication-end-year", "total-pages", "publisher",
    "isbn", "description", "purchase-link", "version-id", "hash",
}


def _children(node: bs4.Tag, allowed: set[str], result: ValidationResult) -> list[bs4.Tag]:
    children = []
    for child in node.children:
        if isinstance(child, bs4.Comment):
            continue
        if isinstance(child, bs4.Tag):
            if child.name not in allowed:
                result.add_node_error(f"Unexpected child `{child.name}`", child)
            children.append(child)
        elif str(child).strip():
            result.add_node_error("Unexpected text or declaration", node)
    return children


def _validate_head(head: bs4.Tag, *, allow_extra_attributes: bool = False) -> ValidationResult:
    result = ValidatorBase("head", {}).validate(head, allow_extra_attributes=allow_extra_attributes)
    children = _children(head, {"meta", "title"}, result)
    titles = [child for child in children if child.name == "title"]
    if len(titles) != 1:
        result.add_node_error("Head must contain exactly one title", head)
    for title in titles:
        result = result.combine_with(ValidatorBase("title", {}).validate(title, allow_extra_attributes=allow_extra_attributes))
        if title.find(True):
            result.add_node_error("Title must contain text only", title)

    charset_count = 0
    metadata = {}
    for meta in (child for child in children if child.name == "meta"):
        if "charset" in meta.attrs:
            charset_count += 1
            rules = {"charset": [AttributeRuleRequired()]}
            if str(meta.get("charset", "")).lower() != "utf-8":
                result.add_node_error("Document charset must be UTF-8", meta)
        else:
            rules = {"name": [AttributeRuleRequired()], "content": []}
            name = meta.get("name")
            if name not in METADATA_NAMES:
                result.add_node_error(f"Unsupported metadata name `{name}`", meta)
            if name in metadata:
                result.add_node_error(f"Duplicate metadata `{name}`", meta)
            metadata[name] = meta
            if "content" not in meta.attrs:
                result.add_node_error("Metadata content attribute is required", meta)
            if name in {"pubid", "code", "type"}:
                rules["content"].append(AttributeRuleRequired())
            if name == "pubid":
                rules["content"].append(AttributeRuleInteger(-2147483648, 2147483647))
            if name == "type":
                rules["content"].append(AttributeRuleEnum(*PUBLICATION_TYPES))
            if name == "version-id" and "content" in meta.attrs:
                try:
                    UUID(meta["content"])
                except ValueError:
                    result.add_node_error("Version ID must be a GUID", meta)
            # original-id and purchase-link may be unparseable: import treats them as null.
        result = result.combine_with(ValidatorBase("meta", rules).validate(meta, allow_extra_attributes=allow_extra_attributes))

    if charset_count != 1:
        result.add_node_error("Head must contain exactly one charset declaration", head)
    for name in ("pubid", "code", "type"):
        if name not in metadata:
            result.add_node_error(f"Required metadata `{name}` missing", head)
    return result


def _validate_body(body: bs4.Tag, *, allow_extra_attributes: bool = False) -> ValidationResult:
    result = ValidatorBase("body", {}).validate(body, allow_extra_attributes=allow_extra_attributes)
    children = _children(body, {"div"}, result)
    rows = [child for child in children if child.name == "div"]
    if not rows:
        result.add_node_error("Body must contain at least one paragraph div", body)
    seen_ids = set()
    for row in rows:
        result = result.combine_with(validator_instance.validate(row, allow_extra_attributes=allow_extra_attributes))
        row_id = row.get("id")
        if row_id is None:
            result.add_node_error("Paragraph div requires an id", row)
        elif AttributeRuleInteger(1, 2147483647).validate(row_id, row):
            number = int(row_id)
            if number in seen_ids:
                result.add_node_error(f"Duplicate paragraph id `{row_id}`", row)
            seen_ids.add(number)
    return result


def validate_document(document: str, *, allow_extra_attributes: bool = False) -> ValidationResult:
    content = bs4.BeautifulSoup(document, "html.parser")
    result = ValidationResult.success()
    doctypes = [node for node in content if isinstance(node, bs4.Doctype)]
    if len(doctypes) != 1 or str(doctypes[0]).lower() != "html":
        result.add_node_error("Document requires <!DOCTYPE html>", content)
    roots = []
    for node in content:
        if isinstance(node, (bs4.Comment, bs4.Doctype)):
            continue
        if isinstance(node, bs4.Tag):
            roots.append(node)
        elif str(node).strip():
            result.add_node_error("Unexpected text outside html", content)
    if len(roots) != 1 or roots[0].name != "html":
        result.add_node_error("Document must contain exactly one html root", content)
        return result

    html = roots[0]
    result = result.combine_with(ValidatorBase("html", {
        "lang": [AttributeRuleRequired(), AttributeRuleLanguage()],
        "dir": [AttributeRuleEnum(None, "ltr", "rtl")],
    }).validate(html, allow_extra_attributes=allow_extra_attributes))
    children = _children(html, {"head", "body"}, result)
    if [child.name for child in children] != ["head", "body"]:
        result.add_node_error("Html must contain one head followed by one body", html)
    for child in children:
        if child.name == "head":
            result = result.combine_with(_validate_head(child, allow_extra_attributes=allow_extra_attributes))
        elif child.name == "body":
            result = result.combine_with(_validate_body(child, allow_extra_attributes=allow_extra_attributes))
    return result
