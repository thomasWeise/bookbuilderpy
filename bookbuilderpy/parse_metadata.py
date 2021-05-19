"""An internal package for loading metadata."""
import io
import re
from typing import Dict, Any

import yaml

from bookbuilderpy.strings import enforce_non_empty_str


def parse_metadata(text: str,
                   escape_backslash: bool = False) -> Dict[str, Any]:
    """
    Extract the metadata of a string and parse it.

    :param str text: the text
    :param bool escape_backslash: should backslash characters be escaped?
    :return: the metadata
    :rtype: str
    """
    enforce_non_empty_str(text)
    if not isinstance(escape_backslash, bool):
        raise TypeError("escape_backslash must be bool, "
                        f"but is '{type(escape_backslash)}'.")

    start = re.search(r"^\s*-{3,}\s*$", text, re.MULTILINE)
    if start is None:
        raise ValueError("No metadata start mark (---) found.")
    end = re.search(r"^\s*\.{3,}\s*$", text, re.MULTILINE)
    if end is None:
        raise ValueError("No metadata end mark (...) found.")
    s = start.end()
    e = end.start()
    if s >= e:
        raise ValueError(
            f"End of start mark {s} is >= than start of end mark {e}.")
    text = text[s:e].strip()
    if (text is None) or (len(text) <= 0):
        raise ValueError(f"Metadata is '{text}'.")

    if escape_backslash:
        text = text.replace("\\", "\\\\")

    with io.StringIO(text) as stream:
        res = yaml.safe_load(stream)

    if not isinstance(res, dict):
        raise ValueError(f"Metadata should be dict, but is '{type(res)}'.")
    if len(res) <= 0:
        raise ValueError(f"Metadata should not be empty, but is '{res}'.")
    return res
