"""Some utility methods for string processing."""
import datetime
import re
import string
from typing import Iterable, List, Union, Tuple, Final, Dict, Optional, \
    Pattern, Callable
from urllib.parse import urlparse

from bookbuilderpy.types import type_error


def str_to_lines(text: str) -> List[str]:
    r"""
    Convert a string to an iterable of lines.

    :param text: the original text string
    :return: the lines

    >>> str_to_lines("\n123\n  456\n789 \n 10\n\n")
    ['', '123', '  456', '789 ', ' 10', '', '']
    """
    if not isinstance(text, str):
        raise type_error(text, "text", str)
    return text.split("\n")


def lines_to_str(lines: Iterable[str],
                 trailing_newline: bool = True) -> str:
    r"""
    Convert an iterable of strings to a single string.

    :param lines: the lines
    :param trailing_newline: should the re be a newline at the end?
    :return: the single string

    >>> lines_to_str(["a", "b", "", "c", ""], trailing_newline=True)
    'a\nb\n\nc\n'
    >>> lines_to_str(["a", "b", "", "c"], trailing_newline=True)
    'a\nb\n\nc\n'
    >>> lines_to_str(["a", "b", "", "c"], trailing_newline=False)
    'a\nb\n\nc'
    >>> lines_to_str(["a", "b", "", "c", ""], trailing_newline=False)
    'a\nb\n\nc'
    """
    if not isinstance(lines, Iterable):
        raise type_error(lines, "lines", Iterable)

    res = "\n".join(lines).rstrip()
    if trailing_newline:
        return res + "\n"
    return res


def enforce_non_empty_str(text: str) -> str:
    """
    Enforce that a text is a non-empty string.

    :param text: the text
    :returns: the text
    :raises TypeError: if `text` is not a `str`
    :raises ValueError: if `text` is empty
    """
    if not isinstance(text, str):
        raise type_error(text, "text", str)
    if len(text) <= 0:
        raise ValueError(f"Non-empty str expected, but got '{text}'.")
    return text


def enforce_non_empty_str_without_ws(text: str) -> str:
    """
    Enforce that a text is a non-empty string without white space.

    :param text: the text
    :returns: the text
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

    :param date: the date
    :return: the date string
    """
    if not isinstance(date, datetime.datetime):
        raise type_error(date, "date", datetime.datetime)
    return date.strftime("%Y\u2011%m\u2011%d")


def datetime_to_datetime_str(date: datetime.datetime) -> str:
    """
    Convert a datetime object to a date-time string.

    :param date: the date
    :return: the date-time string
    """
    if not isinstance(date, datetime.datetime):
        raise type_error(date, "date", datetime.datetime)
    return date.strftime("%Y\u2011%m\u2011%d\u00a0%H:%M\u00a0%Z")


def enforce_url(url: str) -> str:
    """
    Enforce that a string is a valid url.

    :param url: the url
    :return: the url
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


def get_prefix_str(str_list: Union[Tuple[str, ...], List[str]]) -> str:
    r"""
    Compute the common prefix string.

    :param str_list: the list of strings
    :return: the common prefix

    >>> get_prefix_str(["abc", "acd"])
    'a'
    >>> get_prefix_str(["xyz", "gsdf"])
    ''
    >>> get_prefix_str([])
    ''
    >>> get_prefix_str(["abx"])
    'abx'
    >>> get_prefix_str(("\\relative.path", "\\relative.figure",
    ...     "\\relative.code"))
    '\\relative.'
    """
    if len(str_list) <= 0:
        return ''
    prefix_str = ''
    len_smallest_str = min([len(str_mem) for str_mem in str_list])
    str_list_0 = str_list[0]
    for i in range(len_smallest_str):
        f = str_list_0[i]
        if len([0 for ind in range(1, len(str_list))
                if f != str_list[ind][i]]) > 0:
            break
        prefix_str += f
    return prefix_str


#: The language to locale dictionary for base locales.
__LANG_DICT: Final[Dict[str, str]] = {
    "en": "en_US",
    "zh": "zh_CN",
    "cn": "zh_CN",
    "tw": "zh_TW",
    "de": "de_DE",
    "fr": "fr_FR",
    "it": "it_IT",
    "ja": "ja_JP",
    "ko": "ko_KR",
    "pt": "pt_BR",
    "es": "es_ES"
}


def lang_to_locale(lang: str) -> str:
    """
    Convert a language ID to a locale.

    :param lang: the language id
    :return: the locale
    """
    lang = enforce_non_empty_str_without_ws(lang)
    if lang in __LANG_DICT:
        return __LANG_DICT[lang]
    if "-" in lang:
        return "_".join(lang.split("-"))
    return lang


def file_size(size: int) -> str:
    """
    Convert a file size to a string.

    :param size: the size
    :return: the string
    """
    if isinstance(size, int) and (size >= 0):
        if size <= 0:
            return "0 B"
        base_size: int = 1
        for suffix in ["B", "KiB", "MiB", "GiB", "TiB", "PiB",
                       "EiB", "ZiB", "YiB"]:
            ret_size = int((size + base_size - 1) / base_size)
            if ret_size >= 1024:
                base_size *= 1024
                continue
            return f"{ret_size} {suffix}"
    raise ValueError(f"Invalid size: {size}.")


#: The dictionary with "and" concatenations
__AND_DICT: Dict[str, Tuple[str, str]] = {
    "de": (" und ", " und "),
    "en": (" and ", ", and ")
}


def to_string(obj,
              locale: Optional[str] = None,
              use_seq_and: bool = True) -> str:
    """
    Convert any object to a string, try to use a proper locale.

    :param obj: the input object
    :param locale: the locale
    :param use_seq_and: should we use "and" in sequences?
    :return: the string representation
    """
    if obj is None:
        return "None"

    if isinstance(obj, str):
        return obj.strip()

    if isinstance(obj, Iterable):
        merge = ", "
        if (locale is not None) and (locale.startswith("zh")):
            merge = ","

        seq = [to_string(r, locale, use_seq_and).strip() for r in obj]
        seql = len(seq)
        if seql == 1:
            return seq[0]

        if use_seq_and and (locale is not None):
            ands = __AND_DICT.get(locale, None)
            if not ands:
                ands = __AND_DICT.get(locale.split("_")[0], None)
            if ands:
                if seql == 2:
                    return ands[0].join(seq)
                res = merge.join(seq[:-1])
                return ands[1].join([res, seq[-1]])

        return merge.join(seq)

    return str(obj).strip()


def regex_sub(search: Union[str, Pattern],
              replace: Union[Callable, str],
              inside: str) -> str:
    r"""
    Replace all occurrences of 'search' in 'inside' with 'replace'.

    :param search: the regular expression to search
    :param replace: the regular expression to replace it with
    :param inside: the string in which to search/replace
    :return: the new string after the recursive replacement

    >>> regex_sub('[ \t]+\n', '\n', ' bla \nxyz\tabc\t\n')
    ' bla\nxyz\tabc\n'
    >>> regex_sub('[0-9]A', 'X', '23A7AA')
    '2XXA'
    """
    while True:
        text = re.sub(search, replace, inside, re.MULTILINE)
        if text is inside:
            return inside
        inside = text
