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


def __no_empty_after(line: str) -> bool:
    """
    No empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    :rtype: str
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
    An empty line is needed before this one.

    :param line: the line
    :return: a boolean value
    :rtype: str
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
    :rtype: str
    >>> __force_no_empty_after("@")
    True
    """
    return line.startswith("@")


def __format_lines(code: str) -> str:
    r"""
    Format Python code lines.

    :param str code: the original code
    :return: the formatted lines.
    :rtype: str

    >>> __format_lines("\ndef a():\n   return 7-   45\n\n")
    'def a():\n    return 7 - 45\n'
    >>> __format_lines("\n\n   \nclass b:\n   def bb(self):      x  =3/a()")
    'class b:\n    def bb(self):\n        x = 3 / a()\n'
    """
    return yapf.yapf_api.FormatCode(code)[0]


def __strip_hints(code: str) -> str:
    r"""
    Strip all type hints from the given code string.

    :param str code: the code string
    :return: the stripped code string
    :rtype: str
    >>> __format_lines(__strip_hints(
    ...     "a: int = 7\ndef b(c: int) -> List[int]:\n    return [4]"))
    'a = 7\n\n\ndef b(c):\n    return [4]\n'
    """
    return sh.strip_string_to_string(code, strip_nl=True, to_empty=True)


#: the regexes for java script
__REGEX_STRIP_LINE_COMMENT: reg.Regex = reg.compile(
    '\\n[ \\t]*?#.*?\\n', flags=reg.V1 | reg.MULTILINE)


def __strip_docstrings_and_comments(code: str,
                                    strip_docstrings: bool = True,
                                    strip_comments: bool = True) -> str:
    r"""
    Remove all docstrings and comments from a string.

    :param str code: the code
    :param bool strip_docstrings: should we delete docstrings?
    :param bool strip_comments: should we delete comments?
    :return: the stripped string
    :rtype: str

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
    code = reg.sub(__REGEX_STRIP_LINE_COMMENT, '\n', code)

    # Now we strip the doc strings and remaining comments.
    prev_toktype = token.INDENT
    last_lineno = -1
    last_col = 0
    with io.StringIO() as output:
        with io.StringIO(code) as reader:
            tokgen = tokenize.generate_tokens(reader.readline)
            for toktype, ttext, (slineno, scol), (elineno, ecol), _ in tokgen:
                if slineno > last_lineno:
                    last_col = 0
                if scol > last_col:
                    output.write(" " * (scol - last_col))
                if (toktype == token.STRING) and \
                        (prev_toktype in (token.INDENT, token.NEWLINE)):
                    if strip_docstrings:
                        ttext = ""
                elif toktype == tokenize.COMMENT:
                    if strip_comments:
                        ttext = ""
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

    :param Iterable[str] code: the code fragment
    :param bool strip_docstrings: should we delete docstrings?
    :param bool strip_comments: should we delete comments?
    :param bool strip_hints: should we delete type hints?
    :return: the formatted code
    :rtype: List[str]
    """
    if not isinstance(code, Iterable):
        raise TypeError(f"code must be Iterable, but is {type(code)}.")
    if not isinstance(strip_docstrings, bool):
        raise TypeError("strip_docstrings must be bool, "
                        f"but is {type(strip_docstrings)}.")
    if not isinstance(strip_comments, bool):
        raise TypeError(
            f"strip_comments must be bool, but is {type(strip_comments)}.")
    if not isinstance(strip_hints, bool):
        raise TypeError(
            f"strip_hints must be bool, but is {type(strip_hints)}.")

    old_len: Tuple[int, int] = sys.maxsize, sys.maxsize

    shortest: List[str] = list(code)
    rcode: List[str] = shortest
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
        new_len: Tuple[int, int] = text.count("\n"), len(text)
        if old_len <= new_len:
            break
        shortest = rcode
        old_len = new_len

        text = __format_lines(text)
        ntext = text
        if strip_docstrings or strip_comments:
            ntext = __strip_docstrings_and_comments(
                text, strip_docstrings=strip_docstrings,
                strip_comments=strip_comments)
        if strip_hints:
            ntext = __strip_hints(ntext)
        if ntext != text:
            text = __format_lines(ntext)
        del ntext

        new_len = text.count("\n"), len(text)
        if old_len <= new_len:
            break

        rcode = str_to_lines(text)
        shortest = rcode
        old_len = new_len

    if (len(shortest) <= 0) or (old_len[0] <= 0):
        raise ValueError(f"Text cannot become {shortest}.")

    return shortest


def preprocess_python(code: List[str],
                      lines: Optional[List[int]] = None,
                      labels: Optional[List[str]] = None,
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

    :param List[str] code: the code loaded from a file
    :param Optional[List[int]] lines: the lines to keep, or None if we
        keep all
    :param Optional[List[str]] labels: a list of labels marking start and end
        of code snippets to include
    :param Set[str] args: the arguments for the code formatter
    :return: the formatted code string
    :rtype: str
    """
    keep_lines = select_lines(code=code, labels=labels, lines=lines)

    # set up arguments
    strip_docstrings: bool = True
    strip_comments: bool = True
    strip_hints: bool = True
    if args:
        strip_docstrings = "doc" not in args
        strip_comments = "comments" not in args
        strip_hints = "hints" not in args

    return lines_to_str(format_python(keep_lines,
                                      strip_docstrings=strip_docstrings,
                                      strip_comments=strip_comments,
                                      strip_hints=strip_hints))
