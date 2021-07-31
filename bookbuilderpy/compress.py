"""Routines for compressing lists of files."""

import os.path
import subprocess  # nosec
from typing import Union, Iterable, List

from bookbuilderpy.build_result import File
from bookbuilderpy.path import Path
from bookbuilderpy.temp import TempFile


def compress_xz(source: Iterable[Union[Path, File, str]],
                dest: str) -> File:
    """
    Compress a sequence of files.

    :param source: the list of files
    :param dest: the destination file
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

    out = Path.path(dest)
    if os.path.exists(out):
        raise ValueError(f"File '{out}' already exists!")
    out_dir = Path.directory(os.path.dirname(out))

    base_dir = os.path.commonpath(files)
    if base_dir:
        base_dir = Path.directory(base_dir)
        paths = '" "'.join([f.relative_to(base_dir) for f in files])
    else:
        base_dir = out_dir
        paths = '" "'.join(files)

    with TempFile.create() as tf:
        tf.write_all(
            f'#!/bin/bash\ntar -c "{paths}" | xz -v -9e -c > "{out}"\n')

        ret = subprocess.run(["sh", tf], check=True, text=True,  # nosec
                             timeout=360, cwd=base_dir)  # nosec

    if ret.returncode != 0:
        raise ValueError("Error when executing compressor.")
    return File(out)
