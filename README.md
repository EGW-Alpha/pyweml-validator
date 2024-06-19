## Python library for validation of WEML markup language

This library is a Python implementation of the WEML markup language. It is used to validate WEML files without accessing EGW Writings API.

### Installation

```bash
pip install weml-validator
```

### Usage

```python
from weml_validator import validate_weml_paragraph, validate_weml_element, ValidationResult

sample_weml_element = '<w-text-block>text<w-lang lang="en">note</w-lang></w-text-block>'
sample_weml_paragraph = '<w-para><w-text-block>text</w-text-block></w-para>'


def print_result(result: ValidationResult):
    if result:
        print("IS VALID")
        return
    print("IS NOT VALID")
    for error in result.errors:
        print(f"{error.line}:{error.column} {error.message}")


print_result(validate_weml_element(sample_weml_element))
print_result(validate_weml_paragraph(sample_weml_paragraph))
```