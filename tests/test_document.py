import unittest

from weml_validator import validate_weml_document


HEADER = '''<meta charset="UTF-8">
<title>Publication</title>
<meta name="pubid" content="127">
<meta name="code" content="AA">
<meta name="type" content="book">'''
ROW = '<div id="1"><w-para><w-text-block>Text</w-text-block></w-para></div>'


def document(body=ROW, header=HEADER, attributes='lang="en"'):
    return f'<!DOCTYPE html>\n<html {attributes}><head>{header}</head><body>{body}</body></html>'


class DocumentTestCase(unittest.TestCase):
    def assert_valid(self, markup):
        result = validate_weml_document(markup)
        self.assertTrue(result, result.errors)

    def assert_invalid(self, markup):
        result = validate_weml_document(markup)
        self.assertFalse(result, markup)
        self.assertTrue(result.errors)

    def test_minimal_document(self):
        self.assert_valid(document())
        self.assert_valid(document(attributes='lang="zh-Hans-CN" dir="rtl"'))

    def test_document_structure(self):
        for markup in ("", ROW, document().replace("<!DOCTYPE html>", ""),
                       document().replace("<head>", "<header>").replace("</head>", "</header>"),
                       document() + "<html></html>", document() + "stray text",
                       document().replace("<body>", "<body><head></head>"),
                       document().replace("</html>", "<body></body></html>")):
            with self.subTest(markup=markup):
                self.assert_invalid(markup)
        self.assert_valid("<!-- Document -->\n" + document(body="<!-- Rows -->" + ROW))

    def test_document_language(self):
        for attrs in ("", 'lang=""', 'lang="en_US"', 'lang="en" dir="bad"'):
            self.assert_invalid(document(attributes=attrs))

    def test_required_header_fields(self):
        for field in HEADER.splitlines():
            with self.subTest(field=field):
                self.assert_invalid(document(header=HEADER.replace(field, "")))
                self.assert_invalid(document(header=HEADER + field))
        for value in ("bad", "2147483648", "-2147483649", "1.5"):
            self.assert_invalid(document(header=HEADER.replace('content="127"', f'content="{value}"')))
        self.assert_invalid(document(header=HEADER.replace('content="book"', 'content="invalid"')))
        self.assert_invalid(document(header=HEADER.replace('charset="UTF-8"', 'charset="bogus"')))
        self.assert_invalid(document(header=HEADER.replace('name="code" content="AA"', 'name="code"')))

    def test_optional_metadata(self):
        metadata = {
            "original-id": "unparseable-becomes-null", "author": "Author", "publisher": "Publisher",
            "publication-year": "1900", "publication-start-year": "1900", "publication-end-year": "1910",
            "total-pages": "iv + 198", "isbn": "1-57233-111-9", "description": "Description",
            "purchase-link": "https://example.com", "version-id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "hash": "opaque-hash",
        }
        header = HEADER + "".join(f'<meta name="{name}" content="{value}">' for name, value in metadata.items())
        self.assert_valid(document(header=header))
        self.assert_invalid(document(header=HEADER + '<meta name="version-id" content="bad">'))
        self.assert_valid(document(header=HEADER + '<meta name="purchase-link" content="relative">'))

    def test_row_ids(self):
        for row_id in ("0", "-1", "2147483648", "", "1.5", "invalid", "²", "9" * 5000):
            with self.subTest(row_id=row_id[:20]):
                self.assert_invalid(document(body=ROW.replace('id="1"', f'id="{row_id}"')))
        self.assert_invalid(document(body=ROW.replace(' id="1"', "")))
        self.assert_invalid(document(body=ROW + ROW))
        self.assert_invalid(document(body=ROW + ROW.replace('id="1"', 'id="01"')))
        self.assert_valid(document(body=ROW + ROW.replace('id="1"', 'id="2147483647"')))

    def test_row_attributes_and_containers(self):
        self.assert_valid(document(body='<div id="9" hash="opaque" refcode-short="AA 1.1" '
                              'refcode-long="The Acts 1.1" data-skip="1">'
                              '<w-toc><w-text-block>Contents</w-text-block></w-toc></div>'
                              '<div id="10"><w-page number="iv"/></div>'))
        self.assert_invalid(document(body=""))
        self.assert_invalid(document(body="<w-para><hr></w-para>"))
        self.assert_invalid(document(body='<div id="1"><w-para><hr></w-para><w-toc/></div>'))
        self.assert_invalid(document(body=ROW.replace("<w-text-block>", '<w-text-block align="invalid">')))

    def test_duplicate_error_identifies_node_and_location(self):
        result = validate_weml_document(document(body=ROW + "\n" + ROW))
        errors = [error for error in result.errors if "Duplicate paragraph id" in error.message]
        self.assertEqual(len(errors), 1)
        self.assertIn('id="1"', errors[0].message)
        self.assertGreater(errors[0].line, 0)
