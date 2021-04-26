"""A formatter for python code."""
from typing import Iterable, Tuple

import yapf  # type: ignore


def format_python(code: Iterable[str]) -> Tuple[str, ...]:
    """
    Format a python code fragment.

    :param Iterable[str] code: the code fragment
    :return: the formatted code
    :rtype: Tuple[str, ...]
    """
    # first, convert code to a single string
    c_list = [c.rstrip() for c in code]
    if c_list[-1] != "":
        c_list.append("")
    joined = "\n".join(c_list)
    del c_list

    # now apply yapf
    formatted = str(yapf.yapf_api.FormatCode(joined)[0])
    del joined

    return tuple(formatted.split("\n"))
