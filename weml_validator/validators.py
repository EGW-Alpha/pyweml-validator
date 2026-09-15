from weml_validator.attribute_validators import AttributeRuleRequired, AttributeRuleEnum, AttributeRuleOptional, \
    AttributeRuleListMarker, AttributeRuleListStart, AttributeRuleInteger, AttributeRuleColor, \
    AttributeRuleLanguage, AttributeRuleLink
from weml_validator.repository import ValidatorRepository
from weml_validator.tag_validators import EmptyTagValidator, ChildrenSubsetValidator, CombinedValidator

validator_instance = ValidatorRepository.get_instance()

INLINES = ["", "a", "br", "w-color", "w-entity", "w-format", "w-lang", "w-non-egw", "w-note", "w-page", "w-sent"]
BLOCKS = ["figure", "w-list", "w-text-block", "table", "hr"]
CONTAINERS = ["w-heading", "w-page", "w-para", "w-para-group", "w-toc"]
COLOR_RULES = {"background": [AttributeRuleColor()], "foreground": [AttributeRuleColor()]}

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='div',
    attribute_rules={
        "id": [AttributeRuleInteger(1, 2147483647)],
        "hash": [AttributeRuleOptional()],
        "refcode-short": [AttributeRuleOptional()],
        "refcode-long": [AttributeRuleOptional()],
        "data-skip": [AttributeRuleOptional()],
    },
    allowed_children=CONTAINERS,
    expected_child_count=1
))

# region Container elements
validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-heading",
    attribute_rules={
        "skip": [AttributeRuleOptional()],
        "level": [AttributeRuleRequired(), AttributeRuleEnum("1", "2", "3", "4", "5", "6")],
        "alt-text": [AttributeRuleOptional()],
        "override-chapter-number": [AttributeRuleInteger(-2147483648, 2147483647)],
        **COLOR_RULES,
    },
    allowed_children=["w-text-block"],
    required_children={"w-text-block": 1},
    expected_child_count=1
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-para",
    attribute_rules={
        "skip": [AttributeRuleOptional()],
        "indent": [AttributeRuleInteger(-4)],
        "align": [AttributeRuleEnum(None, "left", "right", "center")],
        **COLOR_RULES,
        "role": [AttributeRuleEnum(None, "address", "addressee", "author", "date", "place", "introduction",
                                   "letterhead", "salutation", "signature-date", "signature-line", "signature-source",
                                   "bible-text", "devotional-text", "poem-source", "publication-info", "title")]
    },
    allowed_children=BLOCKS,
    expected_child_count=1

))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-para-group",
    attribute_rules={
        "skip": [AttributeRuleOptional()],
        "type": [AttributeRuleEnum(None, "frame")]
    },
    allowed_children=["w-para"],
    required_children={"w-para": None}
))

# endregion

# region Block elements
validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-text-block",
    attribute_rules={
        "type": [AttributeRuleEnum("paragraph", "blockquote", "poem", None)],
        "align": [AttributeRuleEnum(None, "left", "center", "right")],
    },
    allowed_children=INLINES
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='figure',
    attribute_rules={
        "align": [AttributeRuleEnum(None, "left", "center", "right", "justify")],
        "wrap": [AttributeRuleEnum(None, "0", "1")]
    },
    allowed_children=["img", "figcaption"],
    required_children={"img": 1, "figcaption": lambda x: x <= 1},
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='figcaption',
    allowed_children=["w-text-block"],
    required_children={"w-text-block": 1},
))

validator_instance.add_validator(EmptyTagValidator(
    tag='img',
    attribute_rules={
        "src": [AttributeRuleRequired()],
        "alt": [AttributeRuleOptional()],
        "width": [AttributeRuleInteger(-2147483648, 2147483647)],
        "height": [AttributeRuleInteger(-2147483648, 2147483647)]
    }
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='w-list',
    attribute_rules={
        "type": [AttributeRuleEnum(None, "ordered", "unordered")],
        "marker": [AttributeRuleListMarker()],
        "start": [AttributeRuleListStart()]
    },
    allowed_children=["w-li"],
))
validator_instance.add_validator(ChildrenSubsetValidator(
    tag='w-li',
    attribute_rules={
    },
    allowed_children=BLOCKS,
    minimum_child_count=1
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='table',
    allowed_children=["thead", "tbody"],
    required_children={"thead": lambda x: x <= 1, "tbody": lambda x: x <= 1},
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='thead',
    allowed_children=["tr"],
    required_children={"tr": None},
))
validator_instance.add_validator(ChildrenSubsetValidator(
    tag='tbody',
    allowed_children=["tr"],
    required_children={"tr": None},
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='tr',
    allowed_children=["th", "td"],
))
table_cell_rules = {
    "align": [AttributeRuleEnum(None, "left", "right", "center")],
    "valign": [AttributeRuleEnum(None, "top", "center", "bottom")],
    "indent": [AttributeRuleInteger(-4)],
    "colspan": [AttributeRuleInteger(1)],
    "rowspan": [AttributeRuleInteger(1)],
}
validator_instance.add_validator(ChildrenSubsetValidator(
    tag='th',
    attribute_rules=table_cell_rules,
    allowed_children=BLOCKS,
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag='td',
    attribute_rules=table_cell_rules,
    allowed_children=BLOCKS,
))

validator_instance.add_validator(EmptyTagValidator(
    tag='hr'
))

# endregion

# region Inlines
validator_instance.add_validator(CombinedValidator(
    "a",
    ChildrenSubsetValidator(
        tag="a",
        allowed_children=INLINES,
        attribute_rules={
            "href": [AttributeRuleRequired(), AttributeRuleLink()],
            "title": [AttributeRuleOptional()],
        },
        unique=True
    ),
    EmptyTagValidator(
        tag="a",
        attribute_rules={
            "id": [AttributeRuleRequired()]
        }
    )
))

validator_instance.add_validator(EmptyTagValidator(
    tag="br",
    attribute_rules={}
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-color",
    attribute_rules=COLOR_RULES,
    required_any_attributes=("background", "foreground"),
    allowed_children=INLINES,
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-entity",
    attribute_rules={
        "type": [
            AttributeRuleRequired(),
            AttributeRuleEnum("addressee", "date", "place", "topic", "topic-word")
        ],
        "value": [AttributeRuleOptional()]
    },
    allowed_children=INLINES
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-format",
    attribute_rules={
        "type": [
            AttributeRuleRequired(),
            AttributeRuleEnum("bold", "italic", "underline", "superscript", "subscript", "small-caps",
                              "all-caps", "overline")
        ],
    },
    allowed_children=INLINES
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-lang",
    attribute_rules={
        "lang": [AttributeRuleLanguage()],
        "dir": [AttributeRuleEnum(None, "ltr", "rtl")]
    },
    allowed_children=INLINES
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-non-egw",
    attribute_rules={
        "type": [
            AttributeRuleRequired(),
            AttributeRuleEnum("appendix", "comment", "foreword", "intro", "note", "preface", "text")
        ],
    },
    allowed_children=INLINES))
validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-note",
    attribute_rules={
        "type": [
            AttributeRuleEnum(None, "footnote", "chapter-endnote", "book-endnote")
        ]
    },
    allowed_children=["w-note-header", "w-note-body"],
    required_children={"w-note-header": 1, "w-note-body": 1},
    expected_child_count=2
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-note-body",
    allowed_children=["w-note-para"],
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-note-para",
    attribute_rules={
        "indent": [AttributeRuleInteger(0)],
        "align": [AttributeRuleEnum(None, "left", "center", "right")]
    },
    allowed_children=BLOCKS,
    expected_child_count=1
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-note-header",
    allowed_children=INLINES
))

validator_instance.add_validator(EmptyTagValidator(
    tag="w-page",
    attribute_rules={
        "number": [AttributeRuleRequired()]
    }
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-sent",
    allowed_children=INLINES,
    unique=True
))

validator_instance.add_validator(ChildrenSubsetValidator(
    tag="w-toc",
    allowed_children=["w-text-block"],
    expected_child_count=1,
))

# endregion

__all__ = ["validator_instance"]
