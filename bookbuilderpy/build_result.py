"""A collection for build results."""
import os.path
from dataclasses import dataclass
from typing import Optional, Tuple

from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str
from bookbuilderpy.types import type_error


@dataclass(frozen=True, init=False, order=True)
class File:
    """A single file created by a build."""

    #: the path of the file
    path: Path
    #: the size of the file
    size: int
    #: the file name suffix
    suffix: str

    def __init__(self,
                 path: Path):
        """
        Create the build result as a file.

        :param path: the path of the file
        """
        if not isinstance(path, Path):
            raise type_error(path, "path", Path)
        path.enforce_file()
        object.__setattr__(self, "path", path)
        size = os.path.getsize(self.path)
        if not isinstance(size, int):
            raise type_error(size, f"os.path.getsize({self.path})", int)
        if size <= 0:
            raise ValueError(f"File size of '{path}' is {size}.")
        object.__setattr__(self, "size", size)
        _, ext = Path.split_prefix_suffix(os.path.basename(path))
        object.__setattr__(self, "suffix", ext)


@dataclass(frozen=True, init=False, order=True)
class LangResult:
    """All the results created for one language."""

    #: the language code
    lang: Optional[str]
    #: the language name
    lang_name: Optional[str]
    #: the directory containing the results
    directory: Path
    #: the generated files
    results: Tuple[File, ...]

    def __init__(self,
                 lang: Optional[str],
                 lang_name: Optional[str],
                 directory: Path,
                 results: Tuple[File, ...]):
        """
        Create the build result of a given language.

        :param lang: the language
        :param lang_name: the language name
        :param directory: the path of directory containing all the files
        :param results: the result files
        """
        if (lang is None) != (lang_name is None):
            raise ValueError(
                f"lang cannot be '{lang}' if lang name is '{lang_name}'.")
        if lang is None:
            object.__setattr__(self, "lang", None)
            object.__setattr__(self, "lang_name", None)
        else:
            object.__setattr__(self, "lang",
                               enforce_non_empty_str_without_ws(lang))
            if lang_name is not None:
                object.__setattr__(self, "lang_name",
                                   enforce_non_empty_str(lang_name))
            else:
                object.__setattr__(self, "lang_name", None)
        if not isinstance(directory, Path):
            raise type_error(directory, "directory", Path)
        directory.enforce_dir()
        object.__setattr__(self, "directory", directory)

        if not isinstance(results, tuple):
            raise type_error(results, "results", Tuple)
        if len(results) <= 0:
            raise ValueError("results list cannot be empty.")
        for f in results:
            self.directory.enforce_contains(f.path)
        object.__setattr__(self, "results", results)

    def __iter__(self):
        """Iterate over this result list."""
        return iter(self.results)
