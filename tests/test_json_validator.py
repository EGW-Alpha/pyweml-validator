import copy
import json
import unittest
from importlib.resources import files
from pathlib import Path

from json_validator import (
    ValidationError, ValidationResult,
    validate_json_document, validate_json_element, validate_json_paragraph,
)


def text_node():
    return {"kind": "text", "content": "A & B: Привет"}


def paragraph():
    return {"kind": "paragraph", "type": "paragraph", "children": [text_node()]}


def container():
    return {"kind": "paragraph-container", "child": paragraph()}


def document():
    return {
        "meta": {"id": 127, "type": "book", "language": "en", "code": "AA"},
        "body": [{"id": 1, **container()}],
    }


def node_examples():
    return [
        {"kind": "heading-container", "child": paragraph()},
        container(),
        {"kind": "paragraph-group-container", "children": [container()]},
        {"kind": "toc", "child": paragraph()},
        {"kind": "page-break", "number": "iv"},
        paragraph(), {"kind": "hr"},
        {"kind": "image", "src": "images/a.png", "header": paragraph()},
        {"kind": "list", "type": "ordered", "children": [{"kind": "list-item", "children": [paragraph()]}]},
        {"kind": "list-item", "children": [paragraph()]},
        {"kind": "table", "header": [{"kind": "tr", "children": [{"kind": "td", "header": True}]}],
         "children": [{"kind": "tr", "children": [{"kind": "td", "children": [paragraph()]}]}]},
        {"kind": "tr", "children": [{"kind": "td"}]},
        {"kind": "td", "children": [paragraph()]},
        {"kind": "note-para", "child": paragraph()},
        text_node(), {"kind": "br"},
        {"kind": "text-format", "type": "overline", "children": [text_node()]},
        {"kind": "sentence", "children": [text_node()]},
        {"kind": "link", "href": "egw://book/127.5#section", "children": [text_node()]},
        {"kind": "anchor", "id": "section"},
        {"kind": "lang", "lang": "he", "dir": "rtl", "children": [text_node()]},
        {"kind": "non-egw", "type": "preface", "children": [text_node()]},
        {"kind": "entity", "type": "date", "value": "any string", "children": [text_node()]},
        {"kind": "note", "type": "footnote", "ref": [text_node()],
         "children": [{"kind": "note-para", "child": paragraph()}]},
        {"kind": "color", "foreground": "#abc", "children": [text_node()]},
    ]


class JsonValidatorTestCase(unittest.TestCase):
    def assert_valid(self, value, validator=validate_json_element):
        result = validator(value)
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result, result.errors)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def assert_invalid(self, value, validator=validate_json_element, path=None):
        result = validator(value)
        self.assertFalse(result, value)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.errors)
        self.assertTrue(all(isinstance(error, ValidationError) and error.message for error in result.errors))
        if path is not None:
            self.assertIn(path, [error.path for error in result.errors], result.errors)
        return result

    def test_document_object_and_json_string(self):
        self.assert_valid(document(), validate_json_document)
        self.assert_valid(json.dumps(document(), ensure_ascii=False), validate_json_document)

    def test_all_node_kinds(self):
        for node in node_examples():
            with self.subTest(kind=node["kind"]):
                self.assert_valid(node)
                self.assert_valid(json.dumps(node))
                upper = copy.deepcopy(node)
                upper["kind"] = node["kind"].upper()
                self.assert_valid(upper)

    def test_all_document_container_kinds(self):
        for node in node_examples()[:5]:
            with self.subTest(kind=node["kind"]):
                self.assert_valid(node, validate_json_paragraph)
                self.assert_valid(json.dumps(node), validate_json_paragraph)
                value = document()
                value["body"] = [{"id": 1, **node}]
                self.assert_valid(value, validate_json_document)
        self.assert_invalid(paragraph(), validate_json_paragraph)
        self.assert_invalid({"id": 1, **container()}, validate_json_paragraph)

    def test_document_structure_and_metadata_requirements(self):
        for value in ({}, [], None, 1, True, {"meta": {}, "body": []}):
            self.assert_invalid(value, validate_json_document)
        for key in ("meta", "body"):
            value = document()
            del value[key]
            self.assert_invalid(value, validate_json_document)
        for key in ("id", "type", "language", "code"):
            value = document()
            del value["meta"][key]
            self.assert_invalid(value, validate_json_document)
            value["meta"][key] = None
            self.assert_invalid(value, validate_json_document)
        value = document()
        value["body"] = []
        self.assert_invalid(value, validate_json_document, "/body")

    def test_metadata_optional_types_and_compatibility(self):
        strings = ("title", "author", "publisher", "publication-year", "publication-start-year",
                   "publication-end-year", "total-pages", "isbn", "description", "purchase-link", "hash")
        for key in strings:
            for field in (None, "", "arbitrary string"):
                value = document()
                value["meta"][key] = field
                self.assert_valid(value, validate_json_document)
            value["meta"][key] = 123
            self.assert_invalid(value, validate_json_document, f"/meta/{key}")
        for field in (None, -2147483648, 0, 2147483647):
            value = document()
            value["meta"]["original-id"] = field
            self.assert_valid(value, validate_json_document)
        for field in ("127", 1.5, True, 2147483648):
            value["meta"]["original-id"] = field
            self.assert_invalid(value, validate_json_document)
        for field in (None, "3fa85f64-5717-4562-b3fc-2c963f66afa6", "{3FA85F64-5717-4562-B3FC-2C963F66AFA6}"):
            value = document()
            value["meta"]["version-id"] = field
            self.assert_valid(value, validate_json_document)
        for field in ("bad", "", 1):
            value["meta"]["version-id"] = field
            self.assert_invalid(value, validate_json_document, "/meta/version-id")
        for field in (-2147483648, 0, 2147483647):
            value = document()
            value["meta"]["id"] = field
            self.assert_valid(value, validate_json_document)

    def test_row_ids_and_metadata_scope(self):
        for field in (None, 0, -1, 2147483648, "1", 1.0, 1.5, True, [], {}):
            value = document()
            value["body"][0]["id"] = field
            self.assert_invalid(value, validate_json_document, "/body/0/id")
        value = document()
        del value["body"][0]["id"]
        self.assert_invalid(value, validate_json_document)
        value = document()
        value["body"].append({"id": 1, "kind": "page-break", "number": "2"})
        result = self.assert_invalid(value, validate_json_document, "/body/1/id")
        self.assertTrue(any("duplicate" in error.message.lower() for error in result.errors))
        value["body"][1]["id"] = 2147483647
        for field in ("hash", "refcode-short", "refcode-long"):
            value["body"][0][field] = None
        self.assert_valid(value, validate_json_document)
        value["body"][0]["child"]["children"] = [{"kind": "anchor", "id": "1"}] * 2
        self.assert_valid(value, validate_json_document)
        value["body"][0]["child"]["id"] = 1
        self.assert_invalid(value, validate_json_document)

    def test_single_children(self):
        for kind in ("heading-container", "paragraph-container", "toc", "note-para"):
            for child in (None, [], [paragraph()], "text", text_node()):
                with self.subTest(kind=kind, child=child):
                    self.assert_invalid({"kind": kind, "child": child})
            self.assert_invalid({"kind": kind})
        for kind in ("heading-container", "toc"):
            self.assert_invalid({"kind": kind, "child": {"kind": "hr"}})
        for kind in ("paragraph-container", "note-para"):
            self.assert_valid({"kind": kind, "child": {"kind": "hr"}})

    def test_nesting_and_collection_types(self):
        cases = [
            (paragraph(), "children", {"kind": "hr"}),
            ({"kind": "td"}, "children", text_node()),
            ({"kind": "tr"}, "children", paragraph()),
            ({"kind": "table"}, "children", {"kind": "td"}),
            ({"kind": "table"}, "header", {"kind": "td"}),
            ({"kind": "list", "type": "ordered"}, "children", paragraph()),
            ({"kind": "list-item"}, "children", text_node()),
            ({"kind": "paragraph-group-container"}, "children", paragraph()),
            ({"kind": "note", "type": "footnote"}, "ref", paragraph()),
        ]
        for node, field, wrong_child in cases:
            for children in ([wrong_child], [None], [1], ["text"], {}, None, "text"):
                with self.subTest(kind=node["kind"], field=field, children=children):
                    self.assert_invalid({**node, field: children})
            self.assert_valid({**node, field: []})
        value = document()
        value["body"] = [{"id": 1, **paragraph()}]
        self.assert_invalid(value, validate_json_document)

    def test_missing_collections_default_to_empty(self):
        for node in node_examples():
            if node["kind"] in {"text", "br", "hr", "anchor", "page-break"}:
                continue
            minimal = {key: value for key, value in node.items() if key not in {"children", "ref", "header"}}
            self.assert_valid(minimal)

    def test_notes_accept_legacy_blocks_but_no_inline_body(self):
        note = {"kind": "note", "type": "footnote", "ref": [], "children": [paragraph(), {"kind": "hr"}]}
        self.assert_valid(note)
        note["children"].append({"kind": "note-para", "child": paragraph()})
        self.assert_valid(note)
        note["children"].append(text_node())
        self.assert_invalid(note)

    def test_required_subtypes(self):
        enums = {
            "paragraph": ("paragraph", "blockquote", "poem"),
            "list": ("ordered", "unordered"),
            "text-format": ("bold", "italic", "underline", "superscript", "subscript", "small-caps", "all-caps", "overline"),
            "non-egw": ("appendix", "comment", "foreword", "intro", "note", "preface", "text"),
            "entity": ("addressee", "date", "place", "topic", "topic-word"),
            "note": ("footnote", "chapter-endnote", "book-endnote"),
        }
        for kind, choices in enums.items():
            for choice in choices:
                self.assert_valid({"kind": kind, "type": choice.upper()})
            self.assert_invalid({"kind": kind})
            for choice in (None, "", "unknown", 1, True):
                self.assert_invalid({"kind": kind, "type": choice})
        for publication_type in ("book", "devotional", "bible-commentary", "bible", "periodical/page-break",
                                 "periodical/no-page-break", "manuscript-volume", "dictionary", "topical-index", "scripture-index"):
            value = document()
            value["meta"]["type"] = publication_type.upper()
            self.assert_valid(value, validate_json_document)

    def test_optional_enum_fallbacks(self):
        for node, field in ((container(), "type"), (container(), "align"),
                            ({"kind": "paragraph-group-container"}, "type"),
                            (paragraph(), "align"), ({"kind": "note-para", "child": paragraph()}, "align"),
                            ({"kind": "td"}, "align"), ({"kind": "td"}, "valign"),
                            ({"kind": "image", "src": "a"}, "align"), ({"kind": "lang"}, "dir")):
            for value in (None, "", "UNKNOWN", "rtl", "CENTER"):
                self.assert_valid({**node, field: value})
            for value in (1, True, [], {}):
                self.assert_invalid({**node, field: value})

    def test_signed_int32_fields_without_weml_bounds(self):
        fields = [({"kind": "heading-container", "child": paragraph()}, "level"),
                  ({"kind": "heading-container", "child": paragraph()}, "override-chapter-number"),
                  (container(), "indent"), ({"kind": "note-para", "child": paragraph()}, "indent"),
                  ({"kind": "td"}, "indent"), ({"kind": "td"}, "rowspan"), ({"kind": "td"}, "colspan"),
                  ({"kind": "image", "src": "a"}, "wrap"), ({"kind": "image", "src": "a"}, "width"),
                  ({"kind": "image", "src": "a"}, "height")]
        for node, field in fields:
            for number in (None, -2147483648, -5, 0, 2147483647):
                self.assert_valid({**node, field: number})
            for number in (-2147483649, 2147483648, "1", 1.0, 1.2, True):
                self.assert_invalid({**node, field: number})
        self.assert_invalid('{"kind":"td","rowspan":1.0}')

    def test_boolean_fields(self):
        for node, field in ((container(), "skip"), ({"kind": "heading-container", "child": paragraph()}, "skip"),
                            ({"kind": "paragraph-group-container"}, "skip"), ({"kind": "td"}, "header")):
            for value in (None, True, False):
                self.assert_valid({**node, field: value})
            for value in (0, 1, "true", ""):
                self.assert_invalid({**node, field: value})

    def test_string_fields_and_overloaded_header(self):
        self.assert_valid({"kind": "text", "content": ""})
        self.assert_invalid({"kind": "text"})
        self.assert_invalid({"kind": "text", "content": None})
        self.assert_valid({"kind": "image", "src": "data:image/png;base64,abc", "header": None})
        self.assert_invalid({"kind": "image"})
        self.assert_invalid({"kind": "image", "src": "a", "header": []})
        self.assert_invalid({"kind": "table", "header": paragraph()})
        self.assert_invalid({"kind": "td", "header": paragraph()})
        for value in (None, "", "arbitrary", "iv"):
            self.assert_valid({"kind": "page-break", "number": value})
            self.assert_valid({"kind": "lang", "lang": value})
            self.assert_valid({"kind": "list", "type": "ordered", "start": value, "marker": value})
        self.assert_invalid({"kind": "list", "type": "ordered", "start": 1})
        self.assert_invalid({"kind": "anchor", "id": ""})
        self.assert_invalid({"kind": "anchor", "id": 1})

    def test_colors(self):
        for node in ({"kind": "color"}, container(), {"kind": "heading-container", "child": paragraph()}):
            for key in ("foreground", "background"):
                for color in ("#abc", "#AbCd", "#A1B2C3", "#80a1b2c3"):
                    self.assert_valid({**node, key: color})
                for color in (None, "", "red", "rgb(1,2,3)", "#12", "#12345", "#1234567", "#123456789", "#ggg", "#abc\n", 1):
                    self.assert_invalid({**node, key: color})
        self.assert_invalid({"kind": "color"})
        self.assert_invalid({"kind": "color", "foreground": "#fff", "background": None})
        self.assert_invalid({**paragraph(), "foreground": "#fff"})

    def test_link_forms(self):
        valid = ("http://example.org", "HTTPS://example.org/path#anchor", "mailto:a@b.com",
                 "egw://book/127.5#section", "egw://bible/1.2#", "egw://missing/AA+1.1",
                 "egw://book/-2147483648.2147483647", "egw://book/0.0")
        invalid = ("", "relative", "#anchor", "ftp://example.org", "javascript:alert(1)",
                   "https://", "https://[broken", "https://example.org:bad", "https://example.org/a b",
                   "mailto:bad", "egw://other/1.2", "egw://book/2147483648.1", "egw://bible/1.-2147483649",
                   "egw://book/not-a-reference", "egw://book/1.2.3", "https://example.org/%gg")
        for href in valid:
            with self.subTest(href=href):
                self.assert_valid({"kind": "link", "href": href})
        for href in invalid:
            with self.subTest(href=href):
                self.assert_invalid({"kind": "link", "href": href}, path="/href")

    def test_unknown_properties_and_kinds(self):
        for node in ({"kind": "unknown"}, {"kind": 1}, {"Kind": "hr"},
                     {"kind": "hr", "children": []}, {"kind": "text", "content": "a", "src": "x"}):
            self.assert_invalid(node)
        value = document()
        value["kind"] = "document"
        self.assert_invalid(value, validate_json_document)

    def test_errors_include_nested_paths_and_collect_multiple_failures(self):
        value = document()
        value["meta"]["code"] = 1
        value["body"][0]["child"]["children"][0]["content"] = None
        result = self.assert_invalid(value, validate_json_document, "/meta/code")
        paths = [error.path for error in result.errors]
        self.assertIn("/body/0/child/children/0/content", paths)
        self.assertTrue(all(error.line is None and error.column is None for error in result.errors))

    def test_invalid_json_and_input_types(self):
        result = self.assert_invalid('{\n "meta":,\n}', validate_json_document)
        self.assertEqual(result.errors[0].line, 2)
        self.assertGreater(result.errors[0].column, 0)
        for source in ("", "{", "null", "[]", "1", "true", '"text"', '{"kind":"hr"} garbage',
                       '{"kind":"td","indent":NaN}', '{"kind":"td","indent":Infinity}',
                       '{"kind":"hr","kind":"br"}'):
            self.assert_invalid(source)
        for value in ([], 1, True, None, float("nan")):
            self.assert_invalid(value)

    def test_validation_does_not_normalize_or_mutate(self):
        value = document()
        value["meta"]["type"] = "BOOK"
        value["meta"]["purchase-link"] = "relative"
        value["body"][0]["kind"] = "PARAGRAPH-CONTAINER"
        value["body"][0]["foreground"] = "#AbCd"
        value["body"][0]["align"] = "UNKNOWN"
        before = copy.deepcopy(value)
        self.assert_valid(value, validate_json_document)
        self.assertEqual(value, before)

    def test_schema_is_packaged_and_works_with_standard_jsonschema(self):
        from jsonschema import Draft202012Validator

        schema = json.loads(files("json_validator").joinpath("weml.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        self.assertTrue(validator.is_valid(document()))
        value = document()
        value["body"][0]["child"]["children"] = [{"kind": "color", "foreground": "bad"}]
        self.assertFalse(validator.is_valid(value))

    def test_json_example_fixtures(self):
        reference = Path(__file__).resolve().parent / "fixtures" / "weml_examples.json"
        examples = json.loads(reference.read_text(encoding="utf-8"))
        self.assertGreater(len(examples), 20)
        for index, value in enumerate(examples):
            with self.subTest(example=index):
                self.assert_valid(value, validate_json_document if "meta" in value else validate_json_element)
