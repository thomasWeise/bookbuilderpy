"""Some utility methods for string processing."""
import datetime
import string
from typing import Iterable
from urllib.parse import urlparse


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


def datetime_to_date_str(date: datetime.datetime) -> str:
    """
    Convert a datetime object to a date string.

    :param datatime.datetime date: the date
    :return: the date string
    :rtype: str
    """
    if not isinstance(date, datetime.datetime):
        raise TypeError(f"Excepted datetime.datetime, but {type(date)}.")
    return date.strftime("%Y\u2011%m\u2011%d")


def datetime_to_datetime_str(date: datetime.datetime) -> str:
    """
    Convert a datetime object to a date-time string.

    :param datatime.datetime date: the date
    :return: the date-time string
    :rtype: str
    """
    if not isinstance(date, datetime.datetime):
        raise TypeError(f"Excepted datetime.datetime, but {type(date)}.")
    return date.strftime("%Y\u2011%m\u2011%d\u00a0%H:%M\u00a0%Z")


def enforce_url(url: str) -> str:
    """
    Enforce that a string is a valid url.

    :param str url: the url
    :return: the url
    :rtype: str
    """
    enforce_non_empty_str_without_ws(url)
    if ".." in url:
        raise ValueError(f"Invalid url '{url}', contains '..'.")
    res = urlparse(url)
    if res.scheme != "ssh":
        if res.scheme not in ("http", "https"):
            raise ValueError(f"Invalid scheme '{res.scheme}' in url '{url}'.")
        if "@" in url:
            raise ValueError(
                f"Non-ssh URL must not contain '@', but '{url}' does")
    enforce_non_empty_str_without_ws(res.netloc)
    enforce_non_empty_str_without_ws(res.path)
    return res.geturl()
