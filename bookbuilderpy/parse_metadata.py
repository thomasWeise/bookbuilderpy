"""An internal package for loading metadata."""
import io
import os.path
import re
from typing import Dict, Any, Final

import yaml  # type: ignore

import bookbuilderpy.constants as bc
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_commands import create_preprocessor
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.types import type_error


#: the full metadata command
__FULL_META_CMD: Final[str] = f"\\{bc.CMD_GET_META}"


def parse_metadata(text: str) -> Dict[str, Any]:
    """
    Extract the metadata of a string and parse it.

    :param text: the text
    :return: the metadata
    """
    enforce_non_empty_str(text)

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

    text = "\n".join([t for t in text.split("\n") if __FULL_META_CMD not in t])

    with io.StringIO(text) as stream:
        try:
            res = yaml.safe_load(stream)
        except BaseException as e:
            raise ValueError(f"Invalid metadata '{text}'.") from e

    if not isinstance(res, dict):
        raise type_error(res, "metadata", dict)
    if len(res) <= 0:
        raise ValueError(f"Metadata should not be empty, but is '{res}'.")
    return res


#: the full input command
__FULL_INPUT_CMD: Final[str] = f"\\{bc.CMD_INPUT}"


def __raw_load(in_file: Path,
               in_dir: Path,
               resolve_cmd_only_once: bool = True) -> str:
    """
    Perform a raw version of the recursive path resolution.

    :param in_file: the input file path
    :param in_dir: the input directory
    :param resolve_cmd_only_once: should only one include be resolved?
    :return: the loaded string
    """
    text = in_file.read_all_str()

    i = text.find(__FULL_INPUT_CMD)
    if i < 0:
        return text
    if resolve_cmd_only_once:
        i = text.find(__FULL_INPUT_CMD, i + len(__FULL_INPUT_CMD))
        if i > 0:
            text = text[:i]

    def __side_load(path: str,
                    _in_file: Path = in_file,
                    _in_dir: Path = in_dir) -> str:
        src = _in_dir.resolve_input_file(path)
        src.enforce_file()
        _new_dir = Path.directory(os.path.dirname(src))
        _in_dir.enforce_contains(_new_dir)
        return __raw_load(src, _new_dir, False)

    cmd = create_preprocessor(name=bc.CMD_INPUT,
                              func=__side_load,
                              n=1,
                              strip_white_space=False,
                              wrap_in_newlines=1)
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

    :param in_file: the input file
    :param in_dir: the input directory
    :return: the map with the meta-data
    """
    return parse_metadata(__raw_load(in_file, in_dir, True))
