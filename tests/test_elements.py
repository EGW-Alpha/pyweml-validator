import unittest

from assertpy import fail

from weml_validator import validate_weml_element


def assert_correct_node(node_html: str):
    validation_result = validate_weml_element(node_html)
    if not validation_result:
        for error in validation_result.errors:
            print(f"Node is invalid: {error.message} at {error.line}:{error.column}")
        fail(f"Node {node_html} must be valid")


def assert_incorrect_node(node_html: str):
    validation_result = validate_weml_element(node_html)
    if validation_result:
        fail(f"Node {node_html} must not be valid")


# noinspection PyMethodMayBeStatic
class ContainerBlockTestCase(unittest.TestCase):
    def test_heading(self):
        assert_correct_node('<w-heading level="1"><w-text-block>text</w-text-block></w-heading>')
        assert_correct_node('<w-heading skip="1" level="1"><w-text-block>text</w-text-block></w-heading>')
        assert_incorrect_node('<w-heading level="1"><br/></w-heading>')
        assert_incorrect_node('<w-heading level="0"><w-text-block>text</w-text-block></w-heading>')
        assert_incorrect_node('<w-heading level="7"><w-text-block>text</w-text-block></w-heading>')
        assert_incorrect_node('<w-heading skip="0" level="1"><w-text-block>text</w-text-block></w-heading>')
        assert_incorrect_node('''<w-heading level="1">
                                    <w-text-block>text</w-text-block>
                                    <w-text-block>text</w-text-block>
                                </w-heading>''')
        assert_incorrect_node('<w-heading level="1" attr="value"><w-text-block>text</w-text-block></w-heading>')

    def test_para(self):
        assert_correct_node('<w-para><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para attr="value"><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para> x <w-text-block>text</w-text-block></w-para>')
        assert_correct_node(
            '<w-para skip="1" indent="-5" role="date" align="right"><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para indent="a"><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para role="a"><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para align="a"><w-text-block>text</w-text-block></w-para>')
        assert_incorrect_node('<w-para skip="a"><w-text-block>text</w-text-block></w-para>')
        assert_correct_node('<w-para ><hr/></w-para>')
        assert_incorrect_node('<w-para><hr/><hr/></w-para>')
        assert_correct_node('<w-para ><w-list><w-li><w-text-block></w-text-block></w-li></w-list></w-para>')

    def test_para_group(self):
        para = '<w-para><w-text-block>text</w-text-block></w-para>'
        assert_correct_node(f'<w-para-group>{para}</w-para-group>')
        assert_correct_node(f'<w-para-group skip="1">{para}</w-para-group>')
        assert_correct_node(f'<w-para-group>{para}{para}</w-para-group>')
        assert_incorrect_node(f'<w-para-group skip="2">{para}</w-para-group>')
        assert_incorrect_node(f'<w-para-group></w-para-group>')
        assert_incorrect_node(f'<w-para-group>{para}a{para}</w-para-group>')

    def test_figure(self):
        assert_correct_node(f'<figure><img src="https://example.com" alt="text" /></figure>')
        assert_correct_node(f'<figure><img src="https://example.com" /></figure>')
        assert_incorrect_node(f'<figure><img src="https://example.com" /><img src="https://example.com" /></figure>')
        assert_correct_node(
            f'<figure>'
            f'<img src="https://example.com" alt="text" /><figcaption><w-text-block>text</w-text-block></figcaption>'
            f'</figure>')
        assert_incorrect_node(
            f'<figure>'
            f'<img src="https://example.com" alt="text" />'
            f'<figcaption><w-text-block>text</w-text-block></figcaption>'
            f'<figcaption><w-text-block>text</w-text-block></figcaption>'
            f'</figure>')
        assert_incorrect_node(
            f'<figure><img src="https://example.com" alt="text" /><figcaption>text</figcaption></figure>')
        assert_incorrect_node(
            f'<figure><img src="https://example.com" alt="text" /><img src="https://example.com" /></figure>')
        assert_incorrect_node(f'<figure>a<img src="https://example.com" alt="text" />b</figure>')
        assert_incorrect_node(f'<figure></figure>')

    def test_td(self):
        assert_correct_node(f'<td></td>')
        assert_correct_node(
            f'<td><w-text-block>a</w-text-block><w-list><w-li><w-text-block></w-text-block></w-li></w-list></td>')
        assert_correct_node(f'<td align="left"></td>')
        assert_correct_node(f'<td align="right"></td>')
        assert_correct_node(f'<td align="center"></td>')
        assert_incorrect_node(f'<td align="bad"></td>')
        assert_correct_node(f'<td valign="top"></td>')
        assert_correct_node(f'<td valign="middle"></td>')
        assert_correct_node(f'<td valign="bottom"></td>')
        assert_incorrect_node(f'<td valign="bad"></td>')
        assert_correct_node(f'<td colspan="1"></td>')
        assert_correct_node(f'<td colspan="10"></td>')
        assert_incorrect_node(f'<td colspan="0"></td>')
        assert_incorrect_node(f'<td colspan="11"></td>')
        assert_correct_node(f'<td rowspan="1"></td>')
        assert_correct_node(f'<td rowspan="10"></td>')
        assert_incorrect_node(f'<td rowspan="0"></td>')
        assert_incorrect_node(f'<td rowspan="11"></td>')

    def test_th(self):  # TODO improve
        assert_correct_node(f'<th></th>')

    def test_tr(self):
        assert_correct_node(f'<tr></tr>')
        assert_correct_node(
            f'<tr><td></td><td></td></tr>')

        assert_correct_node(
            f'<tr><th></th></tr>')
        assert_incorrect_node(
            f'<tr><hr/></tr>')

    def test_thead(self):
        assert_correct_node(f'<thead></thead>')
        assert_correct_node(
            f'<thead><tr><td></td><td></td></tr></thead>')
        assert_incorrect_node(
            f'<thead><hr/></thead>')

    def test_table(self):
        assert_correct_node(f'<table></table>')
        assert_incorrect_node(f'<table>x</table>')
        assert_correct_node(f'<table><thead></thead></table>')
        assert_correct_node(f'<table><tbody></tbody></table>')
        assert_incorrect_node(f'<table><tbody></tbody><tbody></tbody></table>')


# noinspection PyMethodMayBeStatic
class BlockTestCase(unittest.TestCase):
    def test_text_block(self):
        assert_correct_node('<w-text-block>text</w-text-block>')
        assert_correct_node('<w-text-block type="paragraph">text</w-text-block>')
        assert_correct_node('<w-text-block type="blockquote">text</w-text-block>')
        assert_correct_node('<w-text-block type="poem">text</w-text-block>')
        assert_incorrect_node('<w-text-block type="wrong">text</w-text-block>')
        assert_correct_node('<w-text-block>text<w-lang lang="en">note</w-lang></w-text-block>')
        assert_incorrect_node('<w-text-block>text <w-text-block>subtext</w-text-block> text </w-text-block>')

    def test_hr(self):
        assert_correct_node('<hr />')
        assert_correct_node('<hr></hr>')
        assert_incorrect_node('<hr>content</hr>')

    def test_w_list(self):
        assert_correct_node('<w-list><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_correct_node('<w-list type="ordered"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_correct_node('<w-list type="unordered"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_incorrect_node('<w-list type="bad"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_correct_node('<w-list><w-li><w-text-block>item</w-text-block></w-li></w-list>')
        assert_correct_node('<w-list><w-li><w-text-block>item</w-text-block></w-li><w-li><hr/></w-li></w-list>')
        assert_incorrect_node('<w-list><w-li>item</w-li><w-li>item</w-li></w-list>')
        assert_incorrect_node('<w-list>item</w-list>')
        assert_incorrect_node('<w-list><w-li>item</w-li></w-list>')
        assert_correct_node('<w-list type="unordered" marker="•"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_correct_node('<w-list type="ordered" marker="A"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_correct_node('<w-list type="ordered" marker="I" start="3"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_incorrect_node('<w-list type="ordered" marker="A" start="a"><w-li><w-text-block></w-text-block></w-li></w-list>')
        assert_incorrect_node('<w-list type="ordered" marker="*" start="a"><w-li><w-text-block></w-text-block></w-li></w-list>')


# noinspection PyMethodMayBeStatic
class InlinesTestCase(unittest.TestCase):
    def test_correct_format(self):
        assert_correct_node('<w-page number="12"/>')
        assert_correct_node('<w-page number="12"></w-page>')
        assert_correct_node('<w-page number="a"></w-page>')

    def test_incorrect_format(self):
        assert_incorrect_node('<w-page />')
        assert_incorrect_node('<w-page number=""></w-page>')
        assert_incorrect_node('<w-page number="1">content</w-page>')

    def test_incorrect_tag(self):
        assert_incorrect_node('<unknown-tag />')

    def test_page_break(self):
        assert_correct_node('<br />')
        assert_correct_node('<br></br>')
        assert_incorrect_node('<br>content</br>')

    def test_w_format(self):
        def create_typed_format(f_type: str, text: str = ""):
            return f'<w-format type="{f_type}">{text}</w-format>'

        assert_correct_node(create_typed_format("bold"))
        assert_correct_node(create_typed_format("italic"))
        assert_correct_node(create_typed_format("underline"))
        assert_correct_node(create_typed_format("superscript"))
        assert_correct_node(create_typed_format("subscript"))
        assert_correct_node(create_typed_format("small-caps"))
        assert_correct_node(create_typed_format("all-caps"))
        assert_correct_node(create_typed_format("bold", "text"))
        assert_incorrect_node(create_typed_format("bold", "<z/>"))

    def test_w_lang(self):
        assert_correct_node("<w-lang lang='en' dir='ltr'>test</w-entity>")
        assert_correct_node("<w-lang lang='en' dir='rtl'>test</w-entity>")
        assert_correct_node("<w-lang lang='en'>test</w-entity>")
        assert_incorrect_node("<w-lang dir='ltr'>test</w-entity>")
        assert_incorrect_node("<w-lang lang='very long'></w-entity>")

    def test_w_entity(self):
        assert_correct_node("<w-entity type='addressee' value='value'></w-entity>")
        assert_correct_node("<w-entity type='addressee' value='value'>text</w-entity>")
        assert_incorrect_node("<w-entity type='wrong'></w-entity>")

    def test_note(self):
        correct_content = ('<w-note-header>Header</w-note-header>'
                           '<w-note-body><w-text-block>Body</w-text-block></w-note-body>')
        assert_correct_node(f'<w-note>{correct_content}</w-note>')
        assert_incorrect_node('<w-note></w-note>')
        assert_correct_node(
            '''<w-note>
                <w-note-header>Header</w-note-header>
                <w-note-body><w-text-block>Body<br/></w-text-block></w-note-body>
            </w-note>'''
        )
        assert_incorrect_node(
            '''<w-note>
                <w-note-header>Header</w-note-header>
                <w-note-header>Header</w-note-header>
                <w-note-body><w-text-block>Body<br/></w-text-block></w-note-body>
            </w-note>'''
        )
        assert_incorrect_node(
            '''<w-note>
                <w-note-body><w-text-block>Body<br/></w-text-block></w-note-body>
                <w-note-header>Header</w-note-header>
                <w-note-body><w-text-block>Body<br/></w-text-block></w-note-body>
            </w-note>'''
        )
        assert_incorrect_node(
            '<w-note>'
            '<w-note-head>Header</w-note-head>'
            '<w-note-body><w-text-block>Body</w-text-block></w-note-body>'
            '</w-note>')
        assert_incorrect_node(
            f'''<w-note>
                {correct_content}
                text
            </w-note>'''
        )
        assert_incorrect_node(
            '''<w-note>
                <w-note-header>Header<br/></w-note-header>
                <w-note-body><w-text-block>Body</w-text-block></w-note-body>
            </w-note>'''
        )

    def test_sent(self):
        assert_correct_node('<w-sent></w-sent>')
        assert_correct_node('<w-sent>text</w-sent>')
        assert_correct_node('<w-sent>text<w-lang lang="en">note</w-lang></w-sent>')
        assert_incorrect_node('<w-sent>text <w-sent>sub sentence</w-sent> text </w-sent>')

    def test_a(self):
        assert_correct_node('<a href="https://example.com">text</a>')
        assert_correct_node('<a href="https://example.com" title="something">text</a>')
        assert_correct_node('<a href="egw://bible/1965.63113#" title="Test">Revelation 14</a>')
        assert_correct_node('<a id="xxx"></a>')
        assert_correct_node('<a id="xxx"/>')
        assert_incorrect_node('<a>text</a>')
        assert_incorrect_node('<a href="https://google.com">text <a href="zzz">zzz</a></a>')
