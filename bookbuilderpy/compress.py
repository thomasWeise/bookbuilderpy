"""Routines for compressing lists of files."""

import os.path
import subprocess  # nosec
from typing import Union, Iterable, List

from bookbuilderpy.build_result import File
from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.temp import TempFile


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
            raise TypeError(f"Type '{type(f)}' not supported.")
    if len(files) <= 1:
        raise ValueError("Nothing to compress?")

    base_dir = os.path.commonpath(files)
    if base_dir:
        return Path.directory(base_dir), \
            [f.relative_to(base_dir) for f in files]
    return None, files


def compress_xz(source: Iterable[Union[Path, File, str]],
                dest: str) -> File:
    """
    Compress a sequence of files to tar.xz.

    :param source: the list of files
    :param dest: the destination file
    """
    base_dir, files = __paths(source)
    log(f"Applying tar.xz compression to {files}.")

    out = Path.path(dest)
    if os.path.exists(out):
        raise ValueError(f"File '{out}' already exists!")
    out_dir = Path.directory(os.path.dirname(out))

    paths = '" "'.join(files)
    if not base_dir:
        base_dir = out_dir

    with TempFile.create() as tf:
        tf.write_all(
            f'#!/bin/bash\ntar -c "{paths}" | xz -v -9e -c > "{out}"\n')

        ret = subprocess.run(["sh", tf], check=True, text=True,  # nosec
                             timeout=360, cwd=base_dir)  # nosec

    if ret.returncode != 0:
        raise ValueError("Error when executing tar.xz compressor.")
    return File(out)


def compress_zip(source: Iterable[Union[Path, File, str]],
                 dest: str) -> File:
    """
    Compress a sequence of files to zip.

    :param source: the list of files
    :param dest: the destination file
    """
    base_dir, files = __paths(source)
    log(f"Applying zip compression to {files}.")

    out = Path.path(dest)
    if os.path.exists(out):
        raise ValueError(f"File '{out}' already exists!")
    out_dir = Path.directory(os.path.dirname(out))

    if not base_dir:
        base_dir = out_dir

    files.insert(0, out)
    files.insert(0, "-9")
    files.insert(0, "zip")

    ret = subprocess.run(files, check=True, text=True,  # nosec
                         timeout=360, cwd=base_dir)  # nosec

    if ret.returncode != 0:
        raise ValueError("Error when executing zip compressor.")
    return File(out)
