"""Routines for compressing lists of files."""

import os.path
from typing import Union, Iterable, List

from bookbuilderpy.build_result import File
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.shell import shell
from bookbuilderpy.temp import TempFile
from bookbuilderpy.types import type_error
from bookbuilderpy.versions import TOOL_TAR, TOOL_ZIP, TOOL_XZ, has_tool


def __paths(source: Iterable[Union[Path, File, str]]):
    """
    Convert the iterable of input files into a common path list.

    :param source: the paths
    :return: a tuple of a common base path (if any) and the paths
    """
    files: List[Path] = []
    for f in source:
        if isinstance(f, Path):
            f.enforce_file()
            files.append(f)
        elif isinstance(f, File):
            f.path.enforce_file()
            files.append(f.path)
        elif isinstance(f, str):
            files.append(Path.file(f))
        else:
            raise type_error(f, "path element", (Path, File, str))
    if len(files) <= 1:
        raise ValueError("Nothing to compress?")

    base_dir = os.path.commonpath(files)
    if base_dir:
        return Path.directory(base_dir), \
            [f.relative_to(base_dir) for f in files]
    return None, files


def can_xz_compress() -> bool:
    """
    Check if xz compression is available.

    :return: `True` if xz compression is available, `False` otherwise
    """
    return has_tool(TOOL_TAR) and has_tool(TOOL_XZ)


def compress_xz(source: Iterable[Union[Path, File, str]],
                dest: str) -> File:
    """
    Compress a sequence of files to tar.xz.

    :param source: the list of files
    :param dest: the destination file
    :return: the created archive
    """
    if not has_tool(TOOL_TAR):
        raise ValueError(f"tool {TOOL_TAR} not installed.")
    if not has_tool(TOOL_XZ):
        raise ValueError(f"tool {TOOL_XZ} not installed.")

    base_dir, files = __paths(source)
    logger(f"Applying tar.xz compression to {files}.")

    out = Path.path(dest)
    if os.path.exists(out):
        raise ValueError(f"File '{out}' already exists!")
    out_dir = Path.directory(os.path.dirname(out))

    paths = '" "'.join(files)
    if not base_dir:
        base_dir = out_dir

    with TempFile.create() as tf:
        tf.write_all(
            f'#!/bin/bash\n{TOOL_TAR} -c "{paths}" | '
            f'{TOOL_XZ} -v -9e -c > "{out}"\n')
        shell(["sh", tf], timeout=360, cwd=base_dir)

    return File(out)


def can_zip_compress() -> bool:
    """
    Check if zip compression is available.

    :return: `True` if zip compression is available, `False` otherwise
    """
    return has_tool(TOOL_ZIP)


def compress_zip(source: Iterable[Union[Path, File, str]],
                 dest: str) -> File:
    """
    Compress a sequence of files to zip.

    :param source: the list of files
    :param dest: the destination file
    :return: the created archive
    """
    if not has_tool(TOOL_ZIP):
        raise ValueError(f"Tool {TOOL_ZIP} not installed.")

    base_dir, files = __paths(source)
    logger(f"Applying zip compression to {files}.")

    out = Path.path(dest)
    if os.path.exists(out):
        raise ValueError(f"File '{out}' already exists!")
    out_dir = Path.directory(os.path.dirname(out))

    if not base_dir:
        base_dir = out_dir

    files.insert(0, out)
    files.insert(0, "-9")
    files.insert(0, "-X")
    files.insert(0, "-UN=UTF8")
    files.insert(0, TOOL_ZIP)

    shell(files, timeout=360, cwd=base_dir)  # nosec
    return File(out)
