"""A set of utilities interactions with the file system."""
import os
from contextlib import AbstractContextManager
from shutil import rmtree
from tempfile import mkstemp, mkdtemp
from typing import Optional

from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws


class TempDir(Path, AbstractContextManager):
    """
    A scoped temporary directory to be used in a 'with' block.

    The directory and everything in it will be deleted upon exiting the
    'with' block. You can obtain its absolute/real path via :func:`str`.
    """

    #: is the directory open?
    __is_open: bool

    def __new__(cls, value):
        """
        Construct the object.

        :param value: the string value
        """
        ret = super(TempDir, cls).__new__(cls, value)
        ret.enforce_dir()
        ret.__is_open = True
        return ret

    @staticmethod
    def create(directory: Optional[str] = None) -> 'TempDir':
        """
        Create the temporary directory.

        :param Optional[str] directory: an optional root directory
        :raises TypeError: if `directory` is not `None` but also no `str`
        """
        if not (directory is None):
            root_dir = Path.path(directory)
            root_dir.enforce_dir()
        else:
            root_dir = None
        return TempDir(mkdtemp(dir=root_dir))

    def __enter__(self) -> 'TempDir':
        """Nothing, just exists for `with`."""
        return self

    def close(self) -> None:
        """Delete the temporary directory and everything in it."""
        opn = self.__is_open
        self.__is_open = False
        if opn:
            rmtree(self, ignore_errors=True, onerror=None)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()


class TempFile(Path, AbstractContextManager):
    """
    A scoped temporary file to be used in a 'with' block.

    This file will be deleted upon exiting the 'with' block.
    You can obtain its absolute/real path via :func:`str`.
    """

    #: is the directory open?
    __is_open: bool

    def __new__(cls, value):
        """
        Construct the object.

        :param value: the string value
        """
        ret = super(TempFile, cls).__new__(cls, value)
        ret.enforce_file()
        ret.__is_open = True
        return ret

    @staticmethod
    def create(directory: Optional[str] = None,
               prefix: Optional[str] = None,
               suffix: Optional[str] = None) -> 'TempFile':
        """
        Create a temporary file.

        :param Optional[str] directory: a root directory or `TempDir` instance
        :param Optional[str] prefix: an optional prefix
        :param Optional[str] suffix: an optional suffix, e.g., `.txt`
        :raises TypeError: if any of the parameters does not fulfill the type
            contract
        """
        if prefix is not None:
            prefix = enforce_non_empty_str_without_ws(prefix)

        if suffix is not None:
            suffix = enforce_non_empty_str_without_ws(suffix)

        if directory is not None:
            base_dir = Path.path(directory)
            base_dir.enforce_dir()
        else:
            base_dir = None

        (handle, path) = mkstemp(suffix=suffix, prefix=prefix, dir=base_dir)
        os.close(handle)
        return TempFile(path)

    def __enter__(self) -> 'TempFile':
        """Nothing, just exists for `with`."""
        return self

    def close(self) -> None:
        """Delete the temporary file."""
        opn = self.__is_open
        self.__is_open = False
        if opn:
            os.remove(self)

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()
