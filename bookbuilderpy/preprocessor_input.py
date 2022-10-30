"""A preprocessor that loads one root file and resolves are relative inputs."""

from os.path import dirname
from typing import Optional, Final

import bookbuilderpy.constants as bc
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_commands import create_preprocessor
from bookbuilderpy.strings import get_prefix_str, enforce_non_empty_str

#: the common prefix
__REL_PREFIX: Final[str] = "\\" + get_prefix_str([bc.CMD_RELATIVE_CODE,
                                                  bc.CMD_RELATIVE_FIGURE,
                                                  bc.CMD_INPUT])


def __load_input(input_file: str,
                 input_dir: str,
                 lang_id: Optional[str]) -> str:
    """
    Recursively load an input file.

    :param input_file: the input file
    :param input_dir: the base directory
    :param lang_id: the language to use
    :return: the fully-resolved input
    """
    in_file = Path.file(input_file)
    in_dir = Path.directory(input_dir)
    in_dir.enforce_contains(in_file)
    logger(f"now loading file '{in_file}'.")

    text = in_file.read_all_str()

    if __REL_PREFIX not in text:
        return text

    def __relative_input(_in_file: str,
                         _in_dir: Path = in_dir,
                         _lang: Optional[str] = lang_id) -> str:
        the_file = _in_dir.resolve_input_file(_in_file, _lang)
        the_dir = Path.directory(dirname(the_file))
        _in_dir.enforce_contains(the_dir)
        return __load_input(the_file, the_dir, _lang)

    rel_input = create_preprocessor(name=bc.CMD_INPUT,
                                    func=__relative_input,
                                    n=1,
                                    strip_white_space=True,
                                    wrap_in_newlines=2)

    def __relative_code(_label: str,
                        _caption: str,
                        _in_file: str,
                        _lines: str,
                        _labels: str,
                        _args: str,
                        _in_dir: Path = in_dir,
                        _lang: Optional[str] = lang_id) -> str:
        f = _in_dir.resolve_input_file(_in_file, _lang)
        return f"\\{bc.CMD_ABSOLUTE_CODE}{{{_label}}}{{{_caption}}}" \
               f"{{{f}}}{{{_lines}}}{{{_labels}}}{{{_args}}}"

    rel_code = create_preprocessor(name=bc.CMD_RELATIVE_CODE,
                                   func=__relative_code,
                                   n=6,
                                   strip_white_space=True)

    def __relative_figure(_label: str,
                          _caption: str,
                          _in_file: str,
                          _args: str,
                          _in_dir: Path = in_dir,
                          _lang: Optional[str] = lang_id) -> str:
        f = _in_dir.resolve_input_file(_in_file, _lang)
        return f"\\{bc.CMD_ABSOLUTE_FIGURE}{{{_label}}}{{{_caption}}}" \
               f"{{{f}}}{{{_args}}}"

    rel_fig = create_preprocessor(name=bc.CMD_RELATIVE_FIGURE,
                                  func=__relative_figure,
                                  n=4,
                                  strip_white_space=True)

    return rel_input(rel_code(rel_fig(text)))


def load_input(input_file: str,
               input_dir: str,
               lang_id: Optional[str]) -> str:
    """
    Recursively load an input file.

    :param input_file: the input file
    :param input_dir: the base directory
    :param lang_id: the language to use
    :return: the fully-resolved input
    """
    logger(f"beginning to load file '{input_file}' from input dir "
           f"'{input_dir}' under lang id '{lang_id}'.")
    res = enforce_non_empty_str(enforce_non_empty_str(
        __load_input(input_file=input_file,
                     input_dir=input_dir,
                     lang_id=lang_id)).strip())
    logger(f"done loading input file '{input_file}' from input dir "
           f"'{input_dir}' under lang id '{lang_id}', found {len(res)} "
           f"characters.")
    return res
