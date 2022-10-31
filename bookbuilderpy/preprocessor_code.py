"""A preprocessor for loading code."""

from os.path import basename
from typing import List, Optional, Set, Final

import bookbuilderpy.constants as bc
from bookbuilderpy.format_python import preprocess_python
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    lines_to_str
from bookbuilderpy.types import type_error


def get_programming_language(path: str) -> Optional[str]:
    """
    Get the programming language corresponding to a path.

    :param path: the path to the source file
    :return: a string identifying the programming language, or None if none
        detected.
    """
    _, suffix = Path.split_prefix_suffix(basename(Path.path(path)))
    suffix = suffix.lower()
    if suffix == "py":
        return bc.LANG_PYTHON
    return bc.LANG_UNDEFINED


def load_code(path: str, lines: str, labels: str, args: str) -> str:
    """
    Load a piece of code from the given path.

    :param path: the path
    :param lines: a line definition string
    :param labels: a label definition string
    :param args: a string of arguments to be passed to the formatter
    :return: the code
    """
    src = Path.file(path)
    logger(f"Now loading code from '{src}'.")

    keep_lines: Optional[List[int]] = None
    if lines is not None:
        if not isinstance(lines, str):
            raise type_error(lines, "lines", str)

        if len(lines) > 0:
            keep_lines = []
            for line in lines.split(","):
                line = line.strip()
                if "-" in line:
                    ab = line.split("-")
                    if len(ab) != 2:
                        raise ValueError(f"Invalid lines: {lines}.")
                    keep_lines.extend(range(int(ab[0]) - 1, int(ab[1])))
                else:
                    keep_lines.append(int(line) - 1)

    keep_labels: Optional[Set[str]] = None
    if labels is not None:
        if not isinstance(labels, str):
            raise type_error(labels, "labels", str)
        if len(labels) > 0:
            keep_labels = set()
            for label in labels.split(","):
                ll = enforce_non_empty_str_without_ws(label.strip())
                if ll in keep_labels:
                    raise ValueError(f"duplicate label: '{ll}'")
                keep_labels.add(ll)
            if len(keep_labels) <= 0:
                raise ValueError(f"labels='{labels}'.")

    arg_set: Final[Set[str]] = set()
    if args is not None:
        if not isinstance(args, str):
            raise type_error(args, "args", str)
        if len(args) > 0:
            for arg in args.split(","):
                aa = enforce_non_empty_str_without_ws(arg.strip())
                if aa in arg_set:
                    raise ValueError(f"duplicate argument: '{aa}'")
                arg_set.add(aa)

    text: Final[List[str]] = src.read_all_list()
    if len(text) <= 0:
        raise ValueError(f"File '{path}' is empty.")

    if get_programming_language(path) == bc.LANG_PYTHON:
        return preprocess_python(text, keep_lines, keep_labels, arg_set)

    if keep_lines is None:
        return lines_to_str([t.rstrip() for t in text])

    return lines_to_str([text[i].rstrip() for i in keep_lines])
