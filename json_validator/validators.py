"""Validate JSON documents and fragments without coercing or normalizing input.

Public functions accept allow_extra_attributes to ignore undeclared fields
recursively for that call; strict validation remains the default.
"""

import json
from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator, validators

from json_validator.errors import ValidationError, ValidationResult
from json_validator.formats import format_checker


# WEML integer fields require integer tokens, not booleans or floats such as 1.0.
_type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
    "integer", lambda checker, instance: isinstance(instance, int) and not isinstance(instance, bool)
)
_Validator = validators.extend(Draft202012Validator, type_checker=_type_checker)


@lru_cache(maxsize=6)
def _validator(entry: str, allow_extra_attributes: bool):
    schema = json.loads(files("json_validator").joinpath("weml.schema.json").read_text(encoding="utf-8"))
    if allow_extra_attributes:
        # Each mode owns its schema. Never mutate the input or the strict schema.
        pending = [schema]
        while pending:
            part = pending.pop()
            if isinstance(part, dict):
                if part.get("additionalProperties") is False:
                    part["additionalProperties"] = True
                pending.extend(part.values())
            elif isinstance(part, list):
                pending.extend(part)
    if entry != "document":
        schema = {"$defs": schema["$defs"], "$ref": f"#/$defs/{entry}"}
    # Schema/configuration failures are programming errors, not invalid user documents.
    _Validator.check_schema(schema)
    return _Validator(schema, format_checker=format_checker)


def _reject_constant(value: str):
    raise ValueError(f"Non-standard JSON constant `{value}` is not allowed")


def _unique_properties(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON property `{key}`")
        result[key] = value
    return result


def _pointer(parts) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _validate(value: str | dict, entry: str, allow_extra_attributes: bool) -> ValidationResult:
    if isinstance(value, str):
        try:
            value = json.loads(value, parse_constant=_reject_constant, object_pairs_hook=_unique_properties)
        except json.JSONDecodeError as error:
            return ValidationResult([ValidationError(error.msg, line=error.lineno, column=error.colno)])
        except ValueError as error:
            return ValidationResult([ValidationError(str(error))])

    errors = []
    for error in _validator(entry, allow_extra_attributes).iter_errors(value):
        # anyOf is used for nullable scalar types and color presence; its parent
        # error retains the relevant value path without unrelated union branches.
        errors.append(ValidationError(error.message, _pointer(error.absolute_path)))

    if entry == "document" and isinstance(value, dict) and isinstance(value.get("body"), list):
        seen_ids = set()
        for index, row in enumerate(value["body"]):
            row_id = row.get("id") if isinstance(row, dict) else None
            if type(row_id) is not int or not 1 <= row_id <= 2147483647:
                continue
            if row_id in seen_ids:
                errors.append(ValidationError(f"Duplicate paragraph id `{row_id}`", f"/body/{index}/id"))
            seen_ids.add(row_id)
    return ValidationResult(errors)


def validate_json_document(document: str | dict, *, allow_extra_attributes: bool = False) -> ValidationResult:
    """Validate a complete publication, including uniqueness of body row IDs."""
    return _validate(document, "document", allow_extra_attributes)


def validate_json_paragraph(node: str | dict, *, allow_extra_attributes: bool = False) -> ValidationResult:
    """Validate one container without document row metadata."""
    return _validate(node, "container", allow_extra_attributes)


def validate_json_element(node: str | dict, *, allow_extra_attributes: bool = False) -> ValidationResult:
    """Validate one standalone node of any recognized WEML JSON kind."""
    return _validate(node, "node", allow_extra_attributes)
