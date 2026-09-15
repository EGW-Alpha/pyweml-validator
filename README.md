# WEML Validator

Validate WEML markup and JSON publications without accessing the EGW Writings API.

## Installation

Requires Python 3.13 or newer (Python 3).

```bash
pip install weml-validator
```

## WEML validation

```python
from pathlib import Path
from weml_validator import validate_weml_document

weml = Path("publication.weml").read_text(encoding="utf-8")
result = validate_weml_document(weml)

for error in result.errors:
    print(f"{error.line}:{error.column}: {error.message}")
```

For fragments, use `validate_weml_paragraph(weml)` for one container or
`validate_weml_element(weml)` for individual elements.

## JSON validation

```python
from pathlib import Path
from json_validator import validate_json_document

text = Path("publication.json").read_text(encoding="utf-8")
result = validate_json_document(text)

for error in result.errors:
    print(f"{error.path or '/'}: {error.message}")
```

Accepts a JSON string or Python dictionary. Checks the complete document
(`meta` and `body`), nested nodes, field values, and unique row IDs.
For fragments, use `validate_json_paragraph(value)` for one container without
row metadata or `validate_json_element(value)` for one node.

Example of validating a text block:

```python
from json_validator import validate_json_element

result = validate_json_element({
    "kind": "paragraph",
    "type": "paragraph",
    "children": [{"kind": "text", "content": "Hello"}],
})
print(result.is_valid)
```

## Validation options

Results expose `is_valid` and `errors`; `bool(result)` indicates validity.
Input data is not modified.

All functions reject unknown attributes or fields by default. To allow custom
attributes, pass `allow_extra_attributes=True`:

```python
from weml_validator import validate_weml_paragraph

result = validate_weml_paragraph(
    '<w-para custom-attr="123"><w-text-block>Text</w-text-block></w-para>',
    allow_extra_attributes=True,
)
```

Known fields are still validated. Unknown tags and invalid nesting remain errors.

## Development

```bash
poetry install --with test
poetry run python -m unittest
poetry build
```
