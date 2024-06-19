import unittest

from assertpy import fail

from weml_validator import validate_weml_document


def assert_correct_document(document_html: str):
    validation_result = validate_weml_document(document_html)
    if not validation_result:
        for error in validation_result.errors:
            print(f"Node is invalid: {error.message} at {error.line}:{error.column}")
        fail(f"Document must be valid")


def assert_incorrect_document(document_html: str):
    validation_result = validate_weml_document(document_html)
    if validation_result:
        fail(f"Document must not be correct")


# noinspection PyMethodMayBeStatic
class DocumentTestCase(unittest.TestCase):
    def test_paragraph(self):
        pass
