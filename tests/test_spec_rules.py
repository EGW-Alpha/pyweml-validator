import unittest

from weml_validator import validate_weml_element, validate_weml_paragraph


class SpecificationRulesTestCase(unittest.TestCase):
    def assert_valid(self, markup):
        result = validate_weml_element(markup)
        self.assertTrue(result, result.errors)

    def assert_invalid(self, markup):
        result = validate_weml_element(markup)
        self.assertFalse(result, markup)
        self.assertTrue(result.errors)

    def test_color_syntax_on_all_supported_elements(self):
        for tag, attrs, child in (
            ("w-heading", ' level="1"', "<w-text-block>Heading</w-text-block>"),
            ("w-para", "", "<w-text-block>Paragraph</w-text-block>"),
            ("w-color", "", '<w-format type="overline">Text</w-format>'),
        ):
            for attribute in ("background", "foreground"):
                for color in ("#abc", "#AbCd", "#A1B2C3", "#80a1b2c3"):
                    with self.subTest(tag=tag, attribute=attribute, color=color):
                        self.assert_valid(f'<{tag}{attrs} {attribute}="{color}">{child}</{tag}>')
                for color in ("", "red", "abc", "#12", "#12345", "#1234567", "#123456789", "#ggg", "#abc\n"):
                    with self.subTest(tag=tag, attribute=attribute, color=color):
                        self.assert_invalid(f'<{tag}{attrs} {attribute}="{color}">{child}</{tag}>')

    def test_color_requires_one_color_and_validates_both(self):
        self.assert_invalid("<w-color>Text</w-color>")
        self.assert_valid('<w-color background="#fff" foreground="#0008">Text</w-color>')
        self.assert_invalid('<w-color background="#fff" foreground="bad">Text</w-color>')
        self.assert_invalid('<w-color background="bad" foreground="#fff">Text</w-color>')
        self.assert_invalid('<w-color foreground="#fff"><w-text-block>Text</w-text-block></w-color>')
        for wrapper, attrs in (("w-text-block", ""), ("w-format", ' type="bold"'),
                               ("w-lang", ""), ("w-sent", ""), ("w-note-header", "")):
            with self.subTest(wrapper=wrapper):
                self.assert_valid(f'<{wrapper}{attrs}><w-color foreground="#fff">Text</w-color></{wrapper}>')

    def test_indentation_bounds(self):
        for tag in ("w-para", "td", "th", "w-note-para"):
            minimum = 0 if tag == "w-note-para" else -4
            for indent in (str(minimum), "0", "11", "100"):
                with self.subTest(tag=tag, indent=indent):
                    self.assert_valid(f'<{tag} indent="{indent}"><w-text-block>Text</w-text-block></{tag}>')
            for indent in (str(minimum - 1), "", "1.5", "bad", "²", "1\n"):
                with self.subTest(tag=tag, indent=indent):
                    self.assert_invalid(f'<{tag} indent="{indent}"><w-text-block>Text</w-text-block></{tag}>')

    def test_alignment_enums(self):
        for tag, child in (("w-para", "<hr>"), ("w-text-block", "Text"),
                           ("td", ""), ("th", ""), ("w-note-para", "<w-text-block/>")):
            for align in ("left", "center", "right"):
                with self.subTest(tag=tag, align=align):
                    self.assert_valid(f'<{tag} align="{align}">{child}</{tag}>')
            self.assert_invalid(f'<{tag} align="justify">{child}</{tag}>')
        self.assert_valid('<figure align="justify"><img src="image.png"></figure>')

    def test_heading_attributes_and_skip_strings(self):
        self.assert_valid('<w-heading level="3" override-chapter-number="12" alt-text="A &amp; B">'
                          '<w-text-block>Chapter</w-text-block></w-heading>')
        for skip in ("", "1", "0", "true", "preface"):
            for tag, attrs, child in (
                ("w-heading", ' level="1"', "<w-text-block/>"),
                ("w-para", "", "<hr>"),
                ("w-para-group", "", "<w-para><hr></w-para>"),
            ):
                with self.subTest(tag=tag, skip=skip):
                    self.assert_valid(f'<{tag}{attrs} skip="{skip}">{child}</{tag}>')

    def test_integer_heading_and_image_attributes(self):
        for value in ("-1", "0", "123", "2147483647"):
            self.assert_valid(f'<w-heading level="1" override-chapter-number="{value}"><w-text-block/></w-heading>')
            self.assert_valid(f'<img src="image.png" width="{value}" height="{value}">')
        for value in ("bad", "1.5", "2147483648", ""):
            self.assert_invalid(f'<w-heading level="1" override-chapter-number="{value}"><w-text-block/></w-heading>')
            self.assert_invalid(f'<img src="image.png" width="{value}">')
            self.assert_invalid(f'<img src="image.png" height="{value}">')

    def test_toc_requires_one_text_block(self):
        self.assert_valid("<w-toc><w-text-block>Contents</w-text-block></w-toc>")
        for children in ("", "Text", "<hr>", "<w-text-block/><w-text-block/>"):
            self.assert_invalid(f"<w-toc>{children}</w-toc>")
        result = validate_weml_paragraph("<w-toc><w-text-block>Contents</w-text-block></w-toc>")
        self.assertTrue(result, result.errors)

    def test_list_cardinality(self):
        self.assert_valid("<w-list/>")
        self.assert_valid("<w-list><w-li><w-text-block>First</w-text-block><hr>"
                          "<w-list><w-li><hr></w-li></w-list></w-li></w-list>")
        self.assert_invalid("<w-list><w-li/></w-list>")
        self.assert_invalid("<w-list><hr></w-list>")
        self.assert_valid('<w-list marker="•" start="ignored"/>')
        self.assert_invalid('<w-list type="ordered" marker="A\n"/>')
        self.assert_invalid('<w-list type="ordered" start="²"/>')

    def test_table_sections_and_spans(self):
        for section in ("thead", "tbody"):
            self.assert_invalid(f"<table><{section}/></table>")
            self.assert_valid(f"<table><{section}><tr/></{section}></table>")
            self.assert_invalid(f"<table><{section}><tr/></{section}><{section}><tr/></{section}></table>")
        for tag in ("td", "th"):
            for attribute in ("rowspan", "colspan"):
                for value in ("1", "11", "1000"):
                    self.assert_valid(f'<{tag} {attribute}="{value}"/>')
                for value in ("0", "-1", "1.5", "", "²"):
                    self.assert_invalid(f'<{tag} {attribute}="{value}"/>')

    def test_note_header_inlines_and_empty_body(self):
        for note_type in ("footnote", "chapter-endnote", "book-endnote"):
            self.assert_valid(f'<w-note type="{note_type}"><w-note-header>'
                              '<w-format type="overline">1</w-format><br>'
                              '</w-note-header><w-note-body/></w-note>')
        self.assert_invalid('<w-note type="endnote"><w-note-header/><w-note-body/></w-note>')
        self.assert_invalid('<w-note><w-note-header/><w-note-body><w-text-block/></w-note-body></w-note>')
        self.assert_invalid('<w-note><w-note-header/><w-note-body><w-note-para/></w-note-body></w-note>')
        self.assert_valid('<w-note-para><w-list><w-li><hr></w-li></w-list></w-note-para>')
        self.assert_invalid('<w-note-para><w-text-block/><hr></w-note-para>')

    def test_bcp47_language_syntax(self):
        for language in ("en", "zh-Hans-CN", "de-DE-u-co-phonebk", "sl-rozaj-biske-1994",
                         "x-private", "i-klingon", "en-GB-oed", "en-x-a-a", "en-a-foo-b-bar"):
            with self.subTest(language=language):
                self.assert_valid(f'<w-lang lang="{language}">Text</w-lang>')
        for language in ("", "en_US", "e", "en-", "en--US", "en-u", "en-a-foo-a-bar",
                         "sl-rozaj-rozaj", "en-abcdefghij", "en US"):
            with self.subTest(language=language):
                self.assert_invalid(f'<w-lang lang="{language}">Text</w-lang>')

    def test_absolute_links(self):
        for href in ("https://example.com/a#b", "http://example.com", "mailto:user@host.com",
                     "egw://book/11155.2794#sectionAnm01", "egw://bible/1965.5",
                     "egw://missing/5SDABC#page.140"):
            with self.subTest(href=href):
                self.assert_valid(f'<a href="{href}">Link</a>')
        for href in ("#anchor", "relative/page", "ftp://example.com", "javascript:alert(1)",
                     "https://", "https://[broken", "https://example.com:bad", "https://example.com/a b",
                     "mailto:user", "egw://other/1.2", "egw://book/bad", "https://example.com/%zz"):
            with self.subTest(href=href):
                self.assert_invalid(f'<a href="{href}">Link</a>')

    def test_fragment_whitespace_comments_and_diagnostics(self):
        self.assert_valid("\n<!-- comment -->\n<w-para><!-- comment --><hr></w-para>\n")
        for markup in ("", " \n", "plain text", "<!-- comment -->", "<!DOCTYPE html><hr>"):
            self.assert_invalid(markup)
        result = validate_weml_element("<w-text-block>Valid</w-text-block>\n<unknown/>\n<another/>")
        self.assertEqual([error.line for error in result.errors], [2, 3])
        paragraph = validate_weml_paragraph("<w-para>\n<unknown/>\n</w-para>")
        self.assertFalse(paragraph)
        self.assertTrue(any(error.line == 2 and "Unknown tag" in error.message for error in paragraph.errors))
        self.assertFalse(validate_weml_paragraph('<w-para><hr></w-para></div><hr>'))
        self.assertFalse(validate_weml_paragraph('<!DOCTYPE html><w-para><hr></w-para>'))
        self.assert_invalid('<w-text-block><!DOCTYPE html>Text</w-text-block>')
