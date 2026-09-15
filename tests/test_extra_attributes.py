import copy
import json
import unittest

from json_validator import validate_json_document, validate_json_element, validate_json_paragraph
from weml_validator import validate_weml_document, validate_weml_element, validate_weml_paragraph
from tests.test_document import document as weml_document, ROW
from tests.test_json_validator import document as json_document, container


class ExtraAttributesTestCase(unittest.TestCase):
    def assert_modes(self, validator, value):
        self.assertFalse(validator(value), "Strict mode must remain the default")
        result = validator(value, allow_extra_attributes=True)
        self.assertTrue(result, result.errors)
        self.assertFalse(validator(value, allow_extra_attributes=False))
        self.assertFalse(validator(value), "An earlier call must not change the default")

    def test_weml_element_and_paragraph_extensions(self):
        markup = '<w-para data-custom="x"><w-text-block custom="y">'
        markup += '<w-format type="bold" custom="z">Text</w-format><br custom="1"></w-text-block></w-para>'
        for validator in (validate_weml_element, validate_weml_paragraph):
            self.assert_modes(validator, markup)
        self.assert_modes(validate_weml_element, '<a href="https://example.com" custom="x">Link</a>')
        self.assert_modes(validate_weml_element, '<a id="anchor" custom="x"/>')

    def test_weml_document_extensions_at_every_level(self):
        markup = weml_document(body=ROW.replace('<div ', '<div custom="row" '))
        markup = markup.replace('<html ', '<html custom="root" ')
        markup = markup.replace('<head>', '<head custom="head">').replace('<body>', '<body custom="body">')
        markup = markup.replace('<meta ', '<meta custom="meta" ').replace('<title>', '<title custom="title">')
        markup = markup.replace('<w-para>', '<w-para custom="paragraph">')
        self.assert_modes(validate_weml_document, markup)

    def test_weml_known_rules_still_apply(self):
        for markup in (
            '<w-format type="wrong" custom="x">Text</w-format>',
            '<w-format custom="x">Text</w-format>',
            '<w-color foreground="red" custom="x">Text</w-color>',
            '<w-color custom="x">Text</w-color>',
            '<w-para indent="-5" custom="x"><hr></w-para>',
            '<w-para custom="x"><unknown/></w-para>',
            '<w-para custom="x"><hr><hr></w-para>',
            '<w-page custom="x" number="1">Text</w-page>',
            '<a href="invalid" id="anchor" custom="x"/>',
            '<a href="https://example.com" id="anchor" custom="x"/>',
            '<a href="https://example.com" custom="x"><a href="https://example.com"/></a>',
        ):
            with self.subTest(markup=markup):
                self.assertFalse(validate_weml_element(markup, allow_extra_attributes=True))
        duplicate = weml_document(body=ROW + ROW).replace('<div ', '<div custom="x" ')
        self.assertFalse(validate_weml_document(duplicate, allow_extra_attributes=True))
        bad_meta = weml_document().replace('content="book"', 'content="wrong" custom="x"')
        self.assertFalse(validate_weml_document(bad_meta, allow_extra_attributes=True))
        # Unknown names are values of the known meta name attribute, not extra attributes.
        unknown_meta = weml_document().replace('</head>', '<meta name="custom" content="x"></head>')
        self.assertFalse(validate_weml_document(unknown_meta, allow_extra_attributes=True))

    def test_json_element_and_container_extensions(self):
        value = container()
        value["custom"] = {"kind": "not-weml", "arbitrary": [1, None, "text"]}
        value["child"]["custom"] = "block"
        value["child"]["children"][0]["custom"] = "inline"
        before = copy.deepcopy(value)
        for validator in (validate_json_element, validate_json_paragraph):
            self.assert_modes(validator, value)
            self.assert_modes(validator, json.dumps(value))
        self.assertEqual(value, before)

    def test_json_document_extensions_at_every_level(self):
        value = json_document()
        value["custom"] = [1, 2]
        value["meta"]["custom"] = None
        value["body"][0]["custom"] = True
        value["body"][0]["child"]["custom"] = "block"
        value["body"][0]["child"]["children"][0]["custom"] = 123
        before = copy.deepcopy(value)
        self.assert_modes(validate_json_document, value)
        self.assert_modes(validate_json_document, json.dumps(value))
        self.assertEqual(value, before)

    def test_json_known_rules_still_apply(self):
        for node in (
            {"kind": "paragraph", "type": "wrong"},
            {"kind": "paragraph"},
            {"kind": "paragraph", "type": "paragraph", "align": 1},
            {"kind": "color", "foreground": "red"},
            {"kind": "color"},
            {"kind": "td", "indent": True},
            {"kind": "td", "rowspan": 2147483648},
            {"kind": "paragraph", "type": "paragraph", "children": [{"kind": "unknown"}]},
            {"kind": "paragraph", "type": "paragraph", "children": [{"kind": "hr"}]},
            {"kind": "toc"},
            {"kind": "link", "href": "invalid"},
        ):
            with self.subTest(node=node):
                self.assertFalse(validate_json_element({**node, "custom": "x"}, allow_extra_attributes=True))
        value = json_document()
        value["meta"]["type"] = "invalid"
        value["custom"] = "x"
        self.assertFalse(validate_json_document(value, allow_extra_attributes=True))
        value = json_document()
        value["body"].append(copy.deepcopy(value["body"][0]))
        value["body"][1]["custom"] = "x"
        result = validate_json_document(value, allow_extra_attributes=True)
        self.assertFalse(result)
        self.assertIn("/body/1/id", [error.path for error in result.errors])

    def test_json_error_paths_survive_extensions(self):
        value = json_document()
        value["custom"] = "ignored"
        value["body"][0]["child"]["children"][0]["content"] = None
        result = validate_json_document(value, allow_extra_attributes=True)
        self.assertFalse(result)
        self.assertEqual([error.path for error in result.errors], ["/body/0/child/children/0/content"])
