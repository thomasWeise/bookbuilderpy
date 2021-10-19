"""A formatter for python code."""
import io
import sys
import token
import tokenize
from typing import Iterable, Tuple, Sequence, Generator, Set, Optional, \
    List, Union

import strip_hints as sh  # type: ignore
import yapf  # type: ignore

from bookbuilderpy.strings import str_to_lines, lines_to_str


def __no_empty_after(line: str) -> bool:
    """
    No empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    :rtype: str
    >>> __no_empty_after("def ")
    True
    >>> __no_empty_after("  def ")
    True
    >>> __no_empty_after(" import ")
    True
    >>> __no_empty_after("from ")
    True
    >>> __no_empty_after("def")
    False
    >>> __no_empty_after(" import")
    False
    >>> __no_empty_after("from")
    False
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
    >>> __empty_before("def")
    False
    >>> __empty_before(" def ")
    True
    >>> __empty_before(" class")
    False
    >>> __empty_before(" class ")
    True
    """
    lstr = line.lstrip()
    return lstr.startswith("def ") or lstr.startswith("class ")


def __force_no_empty_after(line: str) -> bool:
    """
    Really no empty line is permitted after definition.

    :param line: the line
    :return: a boolean value
    :rtype: str
    >>> __force_no_empty_after("  @")
    True
    """
    lstr = line.lstrip()
    return lstr.startswith("@")


def __strip_double_empty(lines: Iterable[str]) -> Generator:
    """
    A generator that strips any consecutive empty lines.

    :param Iterable[str] lines: the original line iterable
    :return: the generation
    :rtype: str
    >>> list(__strip_double_empty(["a", "", "", "b", "def a",
    ...                            "  c", "", "class b", "", "",
    ...                            "@xx", "", "def c"]))
    ['a', '', 'b', '', 'def a', '  c', '', 'class b', '', '@xx', 'def c']
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
    r"""
    Strip a common whitespace prefix from a list of strings and merge them.

    :param Sequence[str] lines: the lines
    :return: the merged, whitespace-stripped lines
    :rtype: str

    >>> __strip_common_whitespace_prefix([" a", "  b"])
    'a\n b\n'
    >>> __strip_common_whitespace_prefix(["  a", "  b"])
    'a\nb\n'
    >>> __strip_common_whitespace_prefix([" a", "  b", "c"])
    ' a\n  b\nc\n'
    >>> __strip_common_whitespace_prefix(["  a", "  b", "    c"])
    'a\nb\n  c\n'
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
    return lines_to_str(lines)


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

    old_len: int = sys.maxsize
    shortest: Tuple[str, ...] = tuple(code)
    rcode: Union[List[str], Tuple[str, ...]] = shortest
    while True:
        rcode = tuple(__strip_double_empty(lines=rcode))
        if len(rcode) <= 0:
            raise ValueError("Code becomes empty.")
        while rcode[-1].strip() in ("", "\n"):
            rcode = rcode[:-1]
            if len(rcode) <= 0:
                raise ValueError("Code becomes empty.")
        text: str = __strip_common_whitespace_prefix(rcode)
        new_len: int = len(text)
        if old_len <= new_len:
            break
        shortest = rcode
        old_len = new_len
        text = __format_lines(text)
        text = __strip_docstrings_and_comments(
            text, strip_docstrings=strip_docstrings,
            strip_comments=strip_comments)
        if strip_hints:
            text = __strip_hints(text)
        rcode = str_to_lines(text)

    if (len(shortest) <= 0) or (old_len <= 0):
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

    >>> pc = ["def a():", "    b=c", "    return x"]
    >>> preprocess_python(pc)
    'def a():\n    b=c\n    return x\n'
    >>> pc = ["# start x", "def a():", " b=c # -x", "    return x", "# end x"]
    >>> preprocess_python(pc, labels=["x"])
    'def a():\n    return x\n'
    """
    keep_lines: List[str]
    if not labels:
        keep_lines = code
    else:
        keep_lines = []
        for label in labels:
            label = label.strip()
            start_label = f"# start {label}"
            end_label = f"# end {label}"
            inc_label = f"# +{label}"
            exc_label = f"# -{label}"
            inside: bool = False
            found: bool = True

            for cl in code:  # iterate over all code lines
                cls = cl.strip()  # ignore white space when processing labels
                if inside:  # we are in a selected section
                    if cls == end_label:  # end of selected section
                        inside = False
                    elif cls.endswith(exc_label):
                        continue  # exclude single line
                    else:
                        keep_lines.append(cl.rstrip())  # keep line
                        found = True  # we got a line
                elif cls == start_label:
                    inside = True  # found the beginning of a selected range
                elif cls.endswith(inc_label):  # single line to include
                    keep_lines.append(cl[:len(cl) - len(inc_label)].rstrip())
                    found = True

            if not found:
                raise ValueError(
                    f"Did not find any line to include for label {label}.")

    if lines:  # select the lines we want to keep
        keep_lines = [keep_lines[i] for i in lines]

    if len(keep_lines) <= 0:
        raise ValueError(
            f"Empty code after applying labels {labels} and lines {lines}.?")

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
