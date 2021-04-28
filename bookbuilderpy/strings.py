"""Some utility methods for string processing."""
from typing import Iterable


def str_to_lines(text: str) -> Iterable[str]:
    """
    Convert a string to an iterable of lines.

    :param str text: the original text string
    :return: the lines
    :rtype: Iterable[lines]
    """
    return text.split("\n")


def lines_to_str(lines: Iterable[str]) -> str:
    """
    Convert an iterable of strings to a single string.

    :param Iterable[str] lines: the lines
    :return: the single string
    :rtype: str
    """
    return "\n".join(lines)
