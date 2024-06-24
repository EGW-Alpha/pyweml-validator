import unittest

from assertpy import fail

from weml_validator import validate_weml_paragraph


def assert_correct_paragraph(node_html: str):
    validation_result = validate_weml_paragraph(node_html)
    if not validation_result:
        for error in validation_result.errors:
            print(f"Node is invalid: {error.message} at {error.line}:{error.column}")
        fail(f"Paragraph {node_html} must be valid")


def assert_incorrect_paragraph(node_html: str):
    validation_result = validate_weml_paragraph(node_html)
    if validation_result:
        fail(f"Paragraph `{node_html}` must not be valid")


# noinspection PyMethodMayBeStatic
class ParagraphTestCase(unittest.TestCase):
    def test_paragraph(self):
        assert_correct_paragraph('<w-para><w-text-block>text</w-text-block></w-para>')
        assert_correct_paragraph(
            '<w-para-group><w-para><w-text-block>text</w-text-block></w-para><w-para><w-text-block>text</w-text-block></w-para></w-para-group>')
        assert_correct_paragraph('<w-heading level="1"><w-text-block>text</w-text-block></w-heading>')

    def test_incorrect_paragraph(self):
        assert_incorrect_paragraph('<w-text-block>text</w-text-block>')
        assert_incorrect_paragraph('<w-para><w-text-block>text</w-text-block></w-para><w-para><w-text-block>text</w-text-block></w-para>')
