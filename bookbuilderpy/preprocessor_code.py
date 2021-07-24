"""A preprocessor for loading code."""

from os.path import basename
from typing import List, Optional, Set, Final

import bookbuilderpy.constants as bc
from bookbuilderpy.format_python import preprocess_python
from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    lines_to_str


def get_programming_language(path: str) -> Optional[str]:
    """
    Get the programming language corresponding to a path.

    :param str path: the path to the source file
    :return: a string identifying the programming language, or None if none
        detected.
    :rtype: Optional[str]
    """
    _, suffix = Path.split_prefix_suffix(basename(Path.path(path)))
    suffix = suffix.lower()
    if suffix == "py":
        return bc.LANG_PYTHON
    return bc.LANG_UNDEFINED


def load_code(path: str,
              lines: str,
              labels: str,
              args: str) -> str:
    """
    Load a piece of code from the given path.

    :param str path: the path
    :param str lines: a line definition string
    :param str labels: a label definition string
    :param str args: a string of arguments to be passed to the formatter
    :return: the code
    :rtype: str
    """
    src = Path.file(path)
    log(f"Now loading code from '{src}'.")

    keep_lines: Optional[List[int]] = None
    if lines is not None:
        if not isinstance(lines, str):
            raise TypeError(
                f"line info needs to be str, but is {type(lines)}.")

        if len(lines) > 0:
            keep_lines = list()
            for line in lines.split(","):
                line = line.strip()
                if "-" in line:
                    ab = line.split("-")
                    if len(ab) != 2:
                        raise ValueError(f"Invalid lines: {lines}.")
                    keep_lines.extend(range(int(ab[0]) - 1, int(ab[1])))
                else:
                    keep_lines.append(int(line) - 1)

    keep_labels: Optional[List[str]] = None
    if labels is not None:
        if not isinstance(labels, str):
            raise TypeError(
                f"labels info needs to be str, but is {type(labels)}.")
        if len(labels) > 0:
            keep_labels = list()
            for label in labels.split(","):
                keep_labels.append(
                    enforce_non_empty_str_without_ws(label.strip()))

    arg_set: Final[Set[str]] = set()
    if args is not None:
        if not isinstance(args, str):
            raise TypeError(f"args needs to be str, but is {type(args)}.")
        if len(args) > 0:
            for arg in args.split(","):
                arg_set.add(
                    enforce_non_empty_str_without_ws(arg.strip()))

    text: Final[List[str]] = src.read_all_list()
    if len(text) <= 0:
        raise ValueError(f"File '{path}' is empty.")

    if get_programming_language(path) == bc.LANG_PYTHON:
        return preprocess_python(text, keep_lines, keep_labels, arg_set)

    if keep_lines is None:
        return lines_to_str([t.rstrip() for t in text])

    return lines_to_str([text[i].rstrip() for i in keep_lines])