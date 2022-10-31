"""Test all the links in the project's README.md file."""
import os.path
from time import sleep
from typing import Final, Set, List, Dict

import certifi
import urllib3

from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path


def replace_all(find: str, replace: str, src: str) -> str:
    """
    Perform a recursive replacement of strings.

    After applying this function, there will not be any occurence of `find`
    left in `src`. All of them will have been replaced by `replace`. If that
    produces new instances of `find`, these will be replaced as well.
    If `replace` contains `find`, this will lead to an endless loop!

    :param find: the string to find
    :param replace: the string with which it will be replaced
    :param src: the string in which we search
    :return: the string `src`, with all occurrences of find replaced by replace

    >>> replace_all("a", "b", "abc")
    'bbc'
    >>> replace_all("aa", "a", "aaaaa")
    'a'
    >>> replace_all("aba", "a", "abaababa")
    'aa'
    """
    new_len = len(src)
    while True:
        src = src.replace(find, replace)
        old_len = new_len
        new_len = len(src)
        if new_len >= old_len:
            return src


def __ve(msg: str, text: str, idx: int) -> ValueError:
    """
    Raise a value error for the given text piece.

    :param msg: the message
    :param text: the string
    :param idx: the index
    :returns: a value error ready to be raised
    """
    piece = text[max(0, idx - 32):min(len(text), idx + 64)].strip()
    return ValueError(f"{msg}: '...{piece}...'")


#: the headers
__HEADER: Final[Dict[str, str]] = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64;"
                  " rv:106.0) Gecko/20100101 Firefox/106.0"
}


def __check(url: str, valid_urls: Set[str],
            http: urllib3.PoolManager = urllib3.PoolManager(
                cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())) -> None:
    """
    Check if a url exists.

    :param url: str
    :param valid_urls: the set of valid urls
    :param http: the pool manager
    """
    if (url != url.strip()) or (len(url) < 3):
        raise ValueError(f"invalid url '{url}'")
    if url in valid_urls:
        return
    if url.startswith("mailto:"):
        return
    if not url.startswith("http"):
        raise ValueError(f"invalid url '{url}'")

    check_url: str = url
    i = url.find("#")
    if i > 0:
        check_url = url[:i]
    if check_url in valid_urls:
        return

    try:
        sleep(1)
        code = http.request("HEAD", check_url, timeout=35, redirect=True,
                            retries=5, headers=__HEADER).status
    except BaseException as be:
        # sometimes, I cannot reach github from here...
        if url.startswith("http://github.com") \
                or url.startswith("https://github.com"):
            valid_urls.add(check_url)
            return
        raise ValueError(f"invalid url '{url}'.") from be
    logger(f"checked url '{url}' got code {code}.")
    if code not in (200, 403):
        raise ValueError(f"url '{url}' returns code {code}.")
    valid_urls.add(check_url)


def test_all_examples_from_readme_md():
    # First, we load the README.md file as a single string
    base_dir = Path.directory(os.path.join(os.path.dirname(__file__), "../"))
    readme = Path.file(base_dir.resolve_inside("README.md"))
    logger(f"testing all links from README.md file '{readme}'.")
    text = readme.read_all_str()
    logger(f"got {len(text)} characters.")
    if len(text) <= 0:
        raise ValueError(f"README.md file at '{readme}' is empty?")
    del readme

    # remove all code blocks
    start: int = -1
    lines: Final[List[str]] = []
    while True:
        start += 1
        i = text.find("\n```", start)
        if i < start:
            lines.append(text[start:].strip())
            break
        j = text.find("\n```", i + 1)
        if j < i:
            raise __ve("Multi-line code start without end", text, i)
        k = text.find("\n", j + 1)
        if k < j:
            raise __ve("Code end without newline", text, i)
        lines.append(text[start:i].strip())
        start = k

    text = "\n".join(lines).strip()
    lines.clear()

    # these are all urls that have been verified
    valid_urls: Final[Set[str]] = set()

    # build the map of local reference marks
    start = -1
    while True:
        start += 1
        i = text.find("\n#", start)
        if i < start:
            break
        j = text.find(" ", i + 1)
        if j < i:
            raise __ve("Headline without space after #", text, i)
        k = text.find("\n", j + 1)
        if k < j:
            raise __ve("Headline without end", text, i)
        rid: str = text[j:k].strip().replace(" ", "-")
        for ch in ".:,()`/":
            rid = rid.replace(ch, "")
        rid = replace_all("--", "-", rid).lower()
        if (len(rid) <= 2) or ((rid[0] not in "123456789")
                               and (start > 0)) or ("-" not in rid):
            raise __ve(f"invalid id '{rid}'", text, i)
        valid_urls.add(f"#{rid}")
        start = k

    # remove all inline code
    start = -1
    while True:
        start += 1
        i = text.find("`", start)
        if i < start:
            lines.append(text[start:].strip())
            break
        j = text.find("`", i + 1)
        if j < i:
            raise __ve("Multi-line code start without end", text, i)
        lines.append(text[start:i].strip())
        start = j
    text = "\n".join(lines).strip()
    lines.clear()

    logger("now checking '![...]()' style urls")

    # now gather the links to images and remove them
    start = -1
    lines.clear()
    while True:
        start += 1
        i = text.find("![", start)
        if i < start:
            lines.append(text[start:])
            break
        j = text.find("]", i + 1)
        if j <= i:
            break
        if "\n" in text[i:j]:
            start = i
        j += 1
        if text[j] != '(':
            raise __ve("invalid image sequence", text, i)
        k = text.find(")", j + 1)
        if k <= j:
            raise __ve("no closing gap for image sequence", text, i)

        __check(text[j + 1:k], valid_urls)

        lines.append(text[start:i])
        start = k

    text = "\n".join(lines)
    lines.clear()

    logger("now checking '[...]()' style urls")

    # now gather the links and remove them
    start = -1
    lines.clear()
    while True:
        start += 1
        i = text.find("[", start)
        if i < start:
            lines.append(text[start:])
            break
        j = text.find("]", i + 1)
        if j <= i:
            break
        if "\n" in text[i:j]:
            lines.append(text[start:i])
            start = i
            continue
        j += 1
        if text[j] != '(':
            raise __ve("invalid link", text, i)
        k = text.find(")", j + 1)
        if k <= j:
            raise __ve("no closing gap for link", text, i)

        __check(text[j + 1:k], valid_urls)

        lines.append(text[start:i])
        start = k

    text = "\n".join(lines)
    lines.clear()

    logger("now checking ' href=' style urls")

    # now gather the href links and remove them
    for quot in "'\"":
        start = -1
        lines.clear()
        while True:
            start += 1
            start_str = f" href={quot}"
            i = text.find(start_str, start)
            if i < start:
                lines.append(text[start:])
                break
            j = text.find(quot, i + len(start_str))
            if j <= i:
                break
            if "\n" in text[i:j]:
                lines.append(text[start:i])
                start = i
                continue
            __check(text[i + len(start_str):j], valid_urls)

            lines.append(text[start:i])
            start = j

        text = "\n".join(lines)
        lines.clear()

    logger("now checking ' src=' style urls")
    # now gather the image links and remove them
    for quot in "'\"":
        start = -1
        lines.clear()
        while True:
            start += 1
            start_str = f" src={quot}"
            i = text.find(start_str, start)
            if i < start:
                lines.append(text[start:])
                break
            j = text.find(quot, i + len(start_str))
            if j <= i:
                break
            if "\n" in text[i:j]:
                lines.append(text[start:i])
                start = i
                continue
            __check(text[i + len(start_str):j], valid_urls)

            lines.append(text[start:i])
            start = j

        text = "\n".join(lines)
        lines.clear()

    logger("finished testing all links from README.md.")
