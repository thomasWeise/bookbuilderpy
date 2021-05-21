"""A preprocessor for loading code."""

from typing import List, Optional

from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws


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
    src = Path.path(path)
    src.enforce_file()

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
            for label in labels.split(","):
                keep_labels.append(
                    enforce_non_empty_str_without_ws(label.strip()))

    arg_list: List[str] = list()
    if args is not None:
        if not isinstance(args, str):
            raise TypeError(f"args needs to be str, but is {type(args)}.")
        if len(args) > 0:
            for arg in args.split(","):
                arg_list.append(
                    enforce_non_empty_str_without_ws(arg.strip()))

    # do something for now - this must be removed later
    if (len(keep_lines) < 0) or (len(arg_list) < 0) or \
            (len(keep_labels) < 0):
        raise ValueError

    text = src.read_all_list()
    return "\n".join(text)
