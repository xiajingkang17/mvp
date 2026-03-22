from manimlib import *
import re
from typing import Pattern as Selector

class Text(MarkupText):
    def __init__(
        self,
        text: str,
        # For backward compatibility
        isolate: Selector = (re.compile(r"\w+", re.U), re.compile(r"\S+", re.U)),
        use_labelled_svg: bool = True,
        path_string_config: dict = dict(
            use_simple_quadratic_approx=True,
        ),
        **kwargs
    ):
        super().__init__(
            text,
            isolate=isolate,
            use_labelled_svg=use_labelled_svg,
            path_string_config=path_string_config,
            **kwargs
        )
        self.semantic_role = "text_label"
        self.semantic_content = text

    @staticmethod
    def get_command_matches(string: str) -> list[re.Match]:
        pattern = re.compile(r"""[<>&"']""")
        return list(pattern.finditer(string))

    @staticmethod
    def get_command_flag(match_obj: re.Match) -> int:
        return 0

    @staticmethod
    def replace_for_content(match_obj: re.Match) -> str:
        return Text.escape_markup_char(match_obj.group())

    @staticmethod
    def replace_for_matching(match_obj: re.Match) -> str:
        return match_obj.group()