"""A collection for build results."""
import os.path
from dataclasses import dataclass
from typing import Optional, Tuple

from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str


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

        :param Path path: the path of the file
        """
        if not isinstance(path, Path):
            raise TypeError(f"Expected Path, got '{type(path)}'.")
        path.enforce_file()
        object.__setattr__(self, "path", path)
        size = os.path.getsize(self.path)
        if not isinstance(size, int):
            raise TypeError(
                f"File size of '{path}' must be int, but is '{type(size)}'.")
        if size <= 0:
            raise ValueError(f"File size of '{path}' is {size}.")
        object.__setattr__(self, "size", size)
        i = path.rfind(".")
        if (i <= 0) or (i >= (len(path) - 1)):
            raise ValueError(f"File '{path}' has no suffix?")
        suffix = path[i + 1:]
        if len(suffix) <= 0:
            raise ValueError(f"File '{path}' has suffix '{suffix}'?")
        object.__setattr__(self, "suffix", suffix)


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

        :param Optional[str] lang: the language
        :param Optional[str] lang_name: the language name
        :param Path directory: the path of directory containing all the files
        :param Tuple[File, ...] results: the result files
        """
        if (lang is None) != (lang_name is None):
            raise ValueError(
                f"lang cannot be '{lang}' if lang name is '{lang_name}'.")
        if lang is None:
            object.__setattr__(self, "lang", lang)
            object.__setattr__(self, "lang_name", lang_name)
        else:
            object.__setattr__(self, "lang",
                               enforce_non_empty_str_without_ws(lang))
            object.__setattr__(self, "lang_name",
                               enforce_non_empty_str(lang_name))
        if not isinstance(directory, Path):
            raise TypeError(
                f"directory must be Path, but is {type(directory)}.")
        directory.enforce_dir()
        object.__setattr__(self, "directory", directory)

        if not isinstance(results, tuple):
            raise TypeError(
                f"results must be Tuple, but are {type(results)}.")
        if len(results) <= 0:
            raise ValueError("results list cannot be empty.")
        for f in results:
            self.directory.enforce_contains(f.path)
        object.__setattr__(self, "results", results)

    def __iter__(self):
        """Iterate over this result list."""
        return iter(self.results)