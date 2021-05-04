"""A set of utilities interactions with the file system."""
import io
import os
from os.path import realpath, isfile, isdir, abspath, expanduser, \
    expandvars, normcase
from shutil import rmtree
from tempfile import mkstemp, mkdtemp
from typing import Optional, Union, Tuple, Iterable, List

from bookbuilderpy.strings import enforce_non_empty_str_without_ws


def canonicalize_path(path: str) -> str:
    """
    An method which will check and canonicalize a path.

    :param str path: the path
    :return: the canonicalized path
    :rtype: str
    """
    if not isinstance(path, str):
        raise TypeError(
            f"path must be instance of str, but is {type(path)}.")
    if len(path) <= 0:
        raise ValueError("Path must not be empty.")

    path = normcase(abspath(realpath(expanduser(expandvars(path)))))
    if not isinstance(path, str):
        raise TypeError("Path canonicalization should yield string, but "
                        f"returned {type(path)}.")
    if len(path) <= 0:
        raise ValueError("Canonicalization must yield non-empty string, "
                         f"but returned '{path}'.")
    return path


def enforce_file(path: str) -> str:
    """
    A method which enforces that a path references an existing file.

    :param path: the path identifying the file
    :return: the path
    :rtype: str
    :raises ValueError:  if `path` does not reference an existing file
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be str, but is {type(path)}.")
    if not isfile(path):
        raise ValueError(f"Path '{path}' does not identify a file.")
    return path


def enforce_dir(path: str) -> str:
    """
    A method which enforces that a path references an existing directory.

    :param str path: the path identifying the directory
    :return: the path
    :rtype: str
    :raises ValueError:  if `path` does not reference an existing directory
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be str, but is {type(path)}.")
    if not isdir(path):
        raise ValueError(f"Path '{path}' does not identify a directory.")
    return path


class TempDir:
    """
    A scoped temporary directory to be used in a 'with' block.

    The directory and everything in it will be deleted upon exiting the
    'with' block. You can obtain its absolute/real path via :func:`str`.
    """

    def __init__(self, directory: Optional[str] = None) -> None:
        """
        Create the temporary directory.

        :param Optional[str] directory: an optional root directory
        :raises TypeError: if `directory` is not `None` but also no `str`
        """
        if not (directory is None):
            if not isinstance(directory, str):
                raise TypeError(
                    f"directory must be str, but is {type(directory)}.")
            if len(directory) <= 0:
                raise ValueError("directory must not be empty string.")
        self.__path = enforce_dir(canonicalize_path(mkdtemp(dir=directory)))
        self.__open = True

    def __enter__(self) -> 'TempDir':
        """Nothing, just exists for `with`."""
        return self

    def close(self) -> None:
        """Delete the temporary directory and everything in it."""
        opn = self.__open
        self.__open = False
        if opn:
            rmtree(self.__path, ignore_errors=True, onerror=None)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()

    def __str__(self) -> str:
        """
        Get the path to the temporary directory.

        :return: the path
        :rtype: str
        """
        return self.__path

    __repr__ = __str__


class TempFile:
    """
    A scoped temporary file to be used in a 'with' block.

    This file will be deleted upon exiting the 'with' block.
    You can obtain its absolute/real path via :func:`str`.
    """

    def __init__(self, directory: Union[TempDir, Optional[str]] = None,
                 prefix: Optional[str] = None,
                 suffix: Optional[str] = None) -> None:
        """
        Create a temporary file.

        :param str directory: a root directory or `TempDir` instance
        :param Optional[str] prefix: an optional prefix
        :param Optional[str] suffix: an optional suffix, e.g., `.txt`
        :raises TypeError: if any of the parameters does not fulfill the type
            contract
        """
        if not (prefix is None):
            if not isinstance(prefix, str):
                raise TypeError(f"prefix must be str, but is {type(prefix)}.")
            if len(prefix) <= 0:
                raise ValueError("prefix must not be empty string.")

        if not (suffix is None):
            if not isinstance(suffix, str):
                raise TypeError(f"suffix must be str, but is {type(suffix)}.")
            if len(suffix) <= 0:
                raise ValueError("suffix must not be empty string.")

        usedir: Optional[str]
        if directory is None:
            usedir = None
        else:
            if isinstance(directory, TempDir):
                usedir = str(directory)
            else:
                usedir = directory
            if not isinstance(usedir, str):
                raise TypeError("directory must translate to str, "
                                f"but is {type(usedir)}.")
            if len(usedir) <= 0:
                raise ValueError("directory must not be empty string.")

        (handle, path) = mkstemp(suffix=suffix, prefix=prefix,
                                 dir=usedir)
        os.close(handle)
        self.__path = enforce_file(canonicalize_path(path))
        self.__open = True

    def __enter__(self) -> 'TempFile':
        """Nothing, just exists for `with`."""
        return self

    def close(self) -> None:
        """Delete the temporary file."""
        opn = self.__open
        self.__open = False
        if opn:
            os.remove(self.__path)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()

    def __str__(self) -> str:
        """
        Get the path of this temp file.

        :return: the path of this temp file
        :rtype: str
        """
        return self.__path

    __repr__ = __str__


def file_ensure_exists(path: str) -> Tuple[str, bool]:
    """
    Atomically ensure that the file `path` exists and create it otherwise.

    :param str path: the path
    :return: a tuple `(path, existed)` with the canonicalized `path` and a
        Boolean value `existed` which is `True` if the file already existed and
        `False` if it was newly and atomically created.
    :rtype: Tuple[str, bool]
    :raises: ValueError if anything goes wrong during the file creation
    """
    path = canonicalize_path(path)
    existed = False
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL))
    except FileExistsError:
        existed = True
    except Exception as err:
        raise ValueError(
            f"Error when trying to create file '{path}'.") from err
    return enforce_file(path), existed


def dir_ensure_exists(dir_name: str) -> str:
    """
    Make sure that the directory referenced by `dir_name` exists.

    :param str dir_name: the directory name
    :return: the string
    :rtype: str
    """
    dir_name = canonicalize_path(dir_name)
    os.makedirs(name=dir_name, exist_ok=True)
    return enforce_dir(dir_name)


def read_all(file: str) -> List[str]:
    """
    Read all the lines in a file.

    :param str file: the file
    :return: the list of strings of text
    :rtype: List[str]
    """
    with io.open(enforce_file(file), "rt") as reader:
        return reader.readlines()


def write_all(file: str, contents: Iterable[str]) -> None:
    """
    Read all the lines in a file.

    :param str file: the file
    :param Iterable[str] contents: the contents to write
    """
    with io.open(file_ensure_exists(file)[0], "wt") as writer:
        all_text = "\n".join(contents)
        if len(all_text) <= 0:
            raise ValueError("Writing empty text is not permitted.")
        writer.write(all_text)
        if all_text[-1] != "\n":
            writer.write("\n")


def contains_path(basedir: str, sub: str) -> bool:
    """
    Check whether one directory contains a possible sub-directory of file.

    It is expected that both `basedir` and `sub` are the results of
    :meth:`canonicalize_path`.

    :param str basedir: the directory
    :param str sub: the path to the file or directory that may be contained
        in `basedir`
    :return: `TRUE` if `basedir` contains `sub`, `FALSE` otherwise
    :rtype: bool
    """
    return os.path.commonpath([basedir]) == os.path.commonpath([basedir, sub])


def file_path_split(path: str) -> Tuple[str, str, str]:
    """
    Split a file path into a directory, prefix, and a suffix component.

    :param str path: the path to split
    :return: a tuple of directory part, prefix, and suffix
    :rtype: Tuple[str, str, str]
    """
    if not isinstance(path, str):
        raise TypeError(f"File path must be str, but is {type(path)}.")
    if (len(path) <= 0) or (path.strip() != path):
        raise ValueError(f"File path '{path}' is invalid due to white space.")

    filename = enforce_non_empty_str_without_ws(os.path.basename(path))
    dirname = enforce_non_empty_str_without_ws(os.path.dirname(path))

    dot_idx = filename.rfind(".")
    if (dot_idx <= 0) or (dot_idx >= (len(filename) - 1)):
        raise ValueError(f"File path '{path}' is invalid due to last dot "
                         f"index {dot_idx} in file name '{filename}'.")
    prefix = enforce_non_empty_str_without_ws(filename[:dot_idx])
    suffix = enforce_non_empty_str_without_ws(filename[dot_idx + 1:])
    return dirname, prefix, suffix


def file_path_merge(prefix: str, suffix: str,
                    dirname: Optional[str] = None) -> str:
    """
    Merge a file name from a directory, prefix, and suffix component.

    :param str prefix: the file name prefix
    :param str suffix: the file name suffix
    :param Optional[str] dirname: the directory name, or `None` if only
        prefix and suffix should be checked and merged
    :return: the merged prefix and suffix
    :rtype: str
    """
    if dirname is not None:
        if not isinstance(dirname, str):
            raise TypeError(f"Dirname must be str but is {type(dirname)}.")
        enforce_non_empty_str_without_ws(dirname)
    enforce_non_empty_str_without_ws(prefix)
    enforce_non_empty_str_without_ws(suffix)
    rv = f"{prefix}.{suffix}"
    return rv if dirname is None else os.path.join(dirname, rv)
