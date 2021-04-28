"""A formatter for python code."""
import io
import sys
import token
import tokenize
from typing import Iterable, Tuple, Sequence, Generator

import strip_hints as sh  # type: ignore
import yapf  # type: ignore

from bookbuilderpy.strings import str_to_lines


def __no_empty_after(line: str) -> bool:
    """
    No empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    :rtype: str
    """
    lstr = line.lstrip()
    return lstr.startswith("def ") or \
        lstr.startswith("import ") or \
        lstr.startswith("from ")


def __empty_before(line: str) -> bool:
    """
    An empty line is needed before this one.

    :param line: the line
    :return: a boolean value
    :rtype: str
    """
    lstr = line.lstrip()
    return lstr.startswith("def ") or lstr.startswith("class ")


def __force_no_empty_after(line: str) -> bool:
    """
    Really no empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    :rtype: str
    """
    lstr = line.lstrip()
    return lstr.startswith("@")


def __strip_double_empty(lines: Iterable[str]) -> Generator:
    """
    A generator that strips any consecutive empty lines.

    :param Iterable[str] lines: the original line iterable
    :return: the generation
    :rtype: str
    """
    printed_empty = had_empty_or_equivalent = True
    force_no_empty = False
    for line in lines:
        line = line.rstrip()

        if len(line) > 0:
            if __empty_before(line) and (not printed_empty) \
                    and (not force_no_empty):
                yield ""
            had_empty_or_equivalent = __no_empty_after(line)
            force_no_empty = __force_no_empty_after(line)
            yield line
            printed_empty = False
            continue

        if had_empty_or_equivalent or force_no_empty:
            continue

        printed_empty = had_empty_or_equivalent = True
        yield ""


def __format_lines(code: str) -> str:
    """
    Format Python code lines.

    :param str code: the original code
    :return: the formatted lines.
    :rtype: str
    """
    return yapf.yapf_api.FormatCode(code)[0]


def __strip_hints(code: str) -> str:
    """
    Strip all type hints from the given code string.

    :param str code: the code string
    :return: the stripped code string
    :rtype: str
    """
    return sh.strip_string_to_string(code, strip_nl=True, to_empty=True)


def __strip_docstrings_and_comments(code: str,
                                    strip_docstrings: bool = True,
                                    strip_comments: bool = True) -> str:
    """
    Remove all docstrings and comments from a string.

    :param str code: the code
    :param bool strip_docstrings: should we delete docstrings?
    :param bool strip_comments: should we delete comments?
    :return: the stripped string
    :rtype: str
    """
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
        return output.getvalue()


def __strip_common_whitespace_prefix(lines: Sequence[str]) -> str:
    """
    Strip a common whitespace prefix.

    :param Sequence[str] lines: the lines
    :return: the merged, whitespace-stripped lines
    :rtype: str
    """
    prefix_len = sys.maxsize
    for line in lines:
        ll = len(line)
        if ll <= 0:
            continue
        for k in range(min(ll, prefix_len)):
            if line[k] != " ":
                prefix_len = k
                break
    if prefix_len > 0:
        lines = [line[prefix_len:] for line in lines]
    return "\n".join(lines)


def format_python(code: Iterable[str],
                  strip_docstrings: bool = True,
                  strip_comments: bool = True,
                  strip_hints: bool = True) -> Tuple[str, ...]:
    """
    Format a python code fragment.

    :param Iterable[str] code: the code fragment
    :param bool strip_docstrings: should we delete docstrings?
    :param bool strip_comments: should we delete comments?
    :param bool strip_hints: should we delete type hints?
    :return: the formatted code
    :rtype: Tuple[str, ...]
    """
    old_len = sys.maxsize
    shortest = tuple(code)
    while True:
        code = tuple(__strip_double_empty(lines=code))
        text = __strip_common_whitespace_prefix(code)
        new_len = len(text)
        if old_len <= new_len:
            break
        shortest = code
        old_len = new_len
        text = __format_lines(text)
        text = __strip_docstrings_and_comments(
            text, strip_docstrings=strip_docstrings,
            strip_comments=strip_comments)
        if strip_hints:
            text = __strip_hints(text)
        code = str_to_lines(text)

    return tuple(shortest)
