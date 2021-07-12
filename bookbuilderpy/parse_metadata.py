"""An internal package for loading metadata."""
import io
import re
from typing import Dict, Any

import yaml  # type: ignore

from bookbuilderpy.constants import CMD_INPUT
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_commands import create_preprocessor
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


def __raw_load(in_file: Path,
               in_dir: Path,
               resolve_cmd_only_once: bool = True,
               cmd_cooked: str = f"\\{CMD_INPUT}") -> str:
    """
    A raw version of the recursive path resolution.

    :param Path in_file: the input file path
    :param Path in_dir: the input directory
    :param bool resolve_cmd_only_once: should only one include be resolved?
    :param str cmd_cooked: the cooked command
    :return: the loaded string
    :rtype: str
    """
    text = in_file.read_all_str()

    i = text.find(cmd_cooked)
    if i < 0:
        return text
    if resolve_cmd_only_once:
        i = text.find(cmd_cooked, i + len(cmd_cooked))
        if i > 0:
            text = text[:i]

    def __side_load(path: str,
                    _in_file: Path = in_file,
                    _in_dir: Path = in_dir) -> str:
        src = _in_file.resolve_input_file(path)
        src.enforce_file()
        _in_dir.enforce_contains(_in_file)
        return __raw_load(src, _in_dir, False)

    cmd = create_preprocessor(name=CMD_INPUT,
                              func=__side_load,
                              n=1,
                              strip_white_space=True)
    return cmd(text)


def load_initial_metadata(in_file: Path,
                          in_dir: Path) -> Dict[str, Any]:
    """
    Load the initial metadata.

    This function does not process the complete document structure but only
    resolves at most one include. It also does not expand other commands and
    it does not perform any language-based resolution. It is only there to
    gain access to the raw metadata which should be the same over all builds
    of a book. This means things such as shared source code repositories.

    :param Path in_file: the input file
    :param Path in_dir: the input directory
    :return: the map with the meta-data
    :rtype: Dict[str,Any]
    """
    return parse_metadata(__raw_load(in_file, in_dir), True)
