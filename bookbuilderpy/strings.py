"""Some utility methods for string processing."""
import string
from typing import Iterable


def str_to_lines(text: str) -> Iterable[str]:
    r"""
    Convert a string to an iterable of lines.

    :param str text: the original text string
    :return: the lines
    :rtype: Iterable[lines]

    >>> str_to_lines("\n123\n  456\n789 \n 10\n\n")
    ['', '123', '  456', '789 ', ' 10', '', '']
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, but is {type(text)}.")
    return text.split("\n")


def lines_to_str(lines: Iterable[str]) -> str:
    r"""
    Convert an iterable of strings to a single string (no trailing newline).

    :param Iterable[str] lines: the lines
    :return: the single string
    :rtype: str

    >>> lines_to_str(["a", "b", "", "c", ""])
    'a\nb\n\nc\n'
    """
    if not isinstance(lines, Iterable):
        raise TypeError(f"lines must be str, but is {type(lines)}.")
    return "\n".join(lines)


def enforce_non_empty_str(text: str) -> str:
    """
    Enforce that a text is a non-empty string.

    :param str text: the text
    :returns: the text
    :rtype: str
    :raises TypeError: if `text` is not a `str`
    :raises ValueError: if `text` is empty
    """
    if not isinstance(text, str):
        raise TypeError(f"str expected, but got {type(text)}.")
    if len(text) <= 0:
        raise ValueError(f"Non-empty str expected, but got '{text}'.")
    return text


def enforce_non_empty_str_without_ws(text: str) -> str:
    """
    Enforce that a text is a non-empty string without white space.

    :param str text: the text
    :returns: the text
    :rtype: str
    :raises TypeError: if `text` is not a `str`
    :raises ValueError: if `text` is empty or contains any white space
        characters
    """
    text = enforce_non_empty_str(text)
    if any(c in text for c in string.whitespace):
        raise ValueError(
            f"No white space allowed in string, but got '{text}'.")
    return text
