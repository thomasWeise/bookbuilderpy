"""A formatter for python code."""
import io
import sys
import token
import tokenize
from typing import Iterable, Tuple, Set, Optional, \
    List

import regex as reg  # type: ignore
import strip_hints as sh  # type: ignore
import yapf  # type: ignore

from bookbuilderpy.source_tools import select_lines, format_empty_lines, \
    strip_common_whitespace_prefix
from bookbuilderpy.strings import str_to_lines, lines_to_str
from bookbuilderpy.types import type_error


def __no_empty_after(line: str) -> bool:
    """
    No empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    >>> __no_empty_after("def ")
    True
    >>> __no_empty_after("import ")
    True
    >>> __no_empty_after("from ")
    True
    >>> __no_empty_after("def")
    False
    >>> __no_empty_after("import")
    False
    >>> __no_empty_after("from")
    False
    """
    return line.startswith("def ") or line.startswith("import ") \
        or line.startswith("from ")


def __empty_before(line: str) -> bool:
    """
    Check whether an empty line is needed before this one.

    :param line: the line
    :return: a boolean value
    >>> __empty_before("def")
    False
    >>> __empty_before("def ")
    True
    >>> __empty_before("class")
    False
    >>> __empty_before("class ")
    True
    """
    return line.startswith("def ") or line.startswith("class ")


def __force_no_empty_after(line: str) -> bool:
    """
    Really no empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    >>> __force_no_empty_after("@")
    True
    """
    return line.startswith("@")


#: the internal style for formatting Python code
__YAPF_STYLE = yapf.style.CreatePEP8Style()
__YAPF_STYLE["ARITHMETIC_PRECEDENCE_INDICATION"] = True
__YAPF_STYLE["BLANK_LINES_AROUND_TOP_LEVEL_DEFINITION"] = 1
__YAPF_STYLE["BLANK_LINE_BEFORE_NESTED_CLASS_OR_DEF"] = False
__YAPF_STYLE["COALESCE_BRACKETS"] = True
__YAPF_STYLE["COLUMN_LIMIT"] = 74
__YAPF_STYLE["EACH_DICT_ENTRY_ON_SEPARATE_LINE"] = False
__YAPF_STYLE["SPLIT_BEFORE_NAMED_ASSIGNS"] = False


def __format_lines(code: str) -> str:
    r"""
    Format Python code lines.

    :param code: the original code
    :return: the formatted lines.

    >>> __format_lines("\ndef a():\n   return 7-   45\n\n")
    'def a():\n    return 7 - 45'
    >>> __format_lines("\n\n   \nclass b:\n   def bb(self):      x  =3/a()")
    'class b:\n    def bb(self):\n        x = 3 / a()'
    """
    return yapf.yapf_api.FormatCode(code,
                                    style_config=__YAPF_STYLE)[0].rstrip()


#: the regexes stripping comments that occupy a complete line
__REGEX_STRIP_LINE_COMMENT: reg.Regex = reg.compile(
    '\\n[ \\t]*?#.*?\\n',
    flags=reg.V1 | reg.MULTILINE)  # pylint: disable=E1101


def __strip_hints(code: str,
                  strip_comments: bool = False) -> str:
    r"""
    Strip all type hints from the given code string.

    :param code: the code string
    :return: the stripped code string
    >>> __format_lines(__strip_hints(
    ...     "a: int = 7\ndef b(c: int) -> List[int]:\n    return [4]"))
    'a = 7\n\ndef b(c):\n    return [4]'
    """
    new_text: str = sh.strip_string_to_string(code,
                                              strip_nl=True,
                                              to_empty=True)

    # If we have single lines with type hints only, the above will turn
    # them into line comments. We need to get rid of those.

    if strip_comments:
        # In the ideal case, we want to strip all comments anyway.
        # Then we do not need to bother with anything complex and can
        # directly use a regular expression getting rid of them.
        new_text2 = None
        while new_text2 != new_text:
            new_text2 = new_text
            new_text = reg.sub(__REGEX_STRIP_LINE_COMMENT, '\n', new_text)
        return new_text

    # If we should preserve normal comments, all we can do is trying to
    # find these "new" comments in a very pedestrian fashion.
    orig_lines: List[str] = code.splitlines()
    new_lines: List[str] = new_text.splitlines()
    for i in range(min(len(orig_lines), len(new_lines)) - 1, -1, -1):
        t1: str = orig_lines[i].strip()
        t2: str = new_lines[i].strip()
        if t2.startswith("#") and (not t1.startswith("#")) \
                and t2.endswith(t1):
            del new_lines[i]
    return lines_to_str(new_lines, trailing_newline=False)


def __strip_docstrings_and_comments(code: str,
                                    strip_docstrings: bool = True,
                                    strip_comments: bool = True) -> str:
    r"""
    Remove all docstrings and comments from a string.

    :param code: the code
    :param strip_docstrings: should we delete docstrings?
    :param strip_comments: should we delete comments?
    :return: the stripped string

    >>> __strip_docstrings_and_comments("a = 5# bla\n", False, False)
    'a = 5# bla\n'
    >>> __strip_docstrings_and_comments("a = 5# bla\n", False, True)
    'a = 5\n'
    >>> __strip_docstrings_and_comments('def b():\n  \"\"\"bla!\"\"\"', True)
    'def b():\n  '
    >>> __strip_docstrings_and_comments('# 1\na = 5\n# 2\nb = 6\n')
    'a = 5\nb = 6\n'
    """
    # First, we strip line comments that are hard to catch correctly with
    # the tokenization approach later.
    if strip_comments:
        code2 = None
        while code2 != code:
            code2 = code
            code = reg.sub(__REGEX_STRIP_LINE_COMMENT, '\n', code)
        del code2

    # Now we strip the doc strings and remaining comments.
    prev_toktype: int = token.INDENT
    last_lineno: int = -1
    last_col: int = 0
    eat_newline: int = 0
    with io.StringIO() as output:
        with io.StringIO(code) as reader:
            for toktype, ttext, (slineno, scol), (elineno, ecol), _ in \
                    tokenize.generate_tokens(reader.readline):
                eat_newline -= 1
                if slineno > last_lineno:
                    last_col = 0
                if scol > last_col:
                    output.write(" " * (scol - last_col))
                if (toktype == token.STRING) and \
                        (prev_toktype in (token.INDENT, token.NEWLINE)):
                    if strip_docstrings:
                        ttext = ""
                        eat_newline = 1
                elif toktype == tokenize.COMMENT:
                    if strip_comments:
                        ttext = ""
                elif toktype == tokenize.NEWLINE:
                    if eat_newline >= 0:
                        ttext = ""
                        elineno += 1
                output.write(ttext)
                prev_toktype = toktype
                last_col = ecol
                last_lineno = elineno

        result = output.getvalue()

    # remove leading newlines
    while result:
        if result[0] == "\n":
            result = result[1:]
            continue
        return result

    raise ValueError(f"code {code} becomes empty after docstring "
                     "and comment stripping!")


def format_python(code: Iterable[str],
                  strip_docstrings: bool = True,
                  strip_comments: bool = True,
                  strip_hints: bool = True) -> List[str]:
    """
    Format a python code fragment.

    :param code: the code fragment
    :param strip_docstrings: should we delete docstrings?
    :param strip_comments: should we delete comments?
    :param strip_hints: should we delete type hints?
    :return: the formatted code
    """
    if not isinstance(code, Iterable):
        raise type_error(code, "code", Iterable)
    if not isinstance(strip_docstrings, bool):
        raise type_error(strip_docstrings, "strip_docstrings", bool)
    if not isinstance(strip_comments, bool):
        raise type_error(strip_comments, "strip_comments", bool)
    if not isinstance(strip_hints, bool):
        raise type_error(strip_hints, "strip_hints", bool)

    old_len: Tuple[int, int] = (sys.maxsize, sys.maxsize)

    shortest: List[str] = list(code)
    rcode: List[str] = shortest
    not_first_run: bool = False
    while True:
        rcode = strip_common_whitespace_prefix(format_empty_lines(
            lines=rcode,
            empty_before=__empty_before,
            no_empty_after=__no_empty_after,
            force_no_empty_after=__force_no_empty_after,
            max_consecutive_empty_lines=1))
        if len(rcode) <= 0:
            raise ValueError("Code becomes empty.")

        text = lines_to_str(rcode)
        new_len: Tuple[int, int] = (text.count("\n"), len(text))
        if not_first_run and (old_len <= new_len):
            break
        shortest = rcode
        old_len = new_len

        text = __format_lines(text)
        ntext = text
        if strip_docstrings or strip_comments:
            ntext = __strip_docstrings_and_comments(
                text, strip_docstrings=strip_docstrings,
                strip_comments=strip_comments).rstrip()
        if strip_hints:
            ntext = __strip_hints(ntext,
                                  strip_comments=strip_comments)
        if ntext != text:
            text = __format_lines(ntext)
        del ntext

        text = text.rstrip()
        new_len = text.count("\n"), len(text)
        if not_first_run and (old_len <= new_len):
            break

        rcode = str_to_lines(text)
        shortest = rcode
        old_len = new_len
        not_first_run = True

    if (len(shortest) <= 0) or (old_len[0] <= 0):
        raise ValueError(f"Text cannot become {shortest}.")

    return shortest


def preprocess_python(code: List[str],
                      lines: Optional[List[int]] = None,
                      labels: Optional[Iterable[str]] = None,
                      args: Optional[Set[str]] = None) -> str:
    r"""
    Preprocess Python code.

    First, we select all lines of the code we want to keep.
    If labels are defined, then lines can be kept as ranges or as single
    lines.
    Otherwise, all lines are selected in this step.

    Then, if line numbers are provided, we selected the lines based on the
    line numbers from the lines we have preserved.

    Finally, the Python formatter is applied.

    :param code: the code loaded from a file
    :param lines: the lines to keep, or `None` if we keep all
    :param labels: a list of labels marking start and end of code snippets
        to include
    :param args: the arguments for the code formatter
    :return: the formatted code string
    """
    keep_lines = select_lines(code=code, labels=labels, lines=lines)

    # set up arguments
    strip_docstrings: bool = True
    strip_comments: bool = True
    strip_hints: bool = True
    do_format: bool = True
    if args:
        do_format = "format" not in args
        strip_docstrings = "doc" not in args
        strip_comments = "comments" not in args
        strip_hints = "hints" not in args

    if do_format:
        return lines_to_str(format_python(keep_lines,
                                          strip_docstrings=strip_docstrings,
                                          strip_comments=strip_comments,
                                          strip_hints=strip_hints),
                            trailing_newline=True)
    return lines_to_str(keep_lines, trailing_newline=True)
