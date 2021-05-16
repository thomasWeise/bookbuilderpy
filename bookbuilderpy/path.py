"""The base class with the information of a build."""

import io
import os.path
from typing import cast, Optional, List, Iterable

from bookbuilderpy.strings import enforce_non_empty_str_without_ws


def _canonicalize_path(path: str) -> str:
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

    path = os.path.normcase(
        os.path.abspath(
            os.path.realpath(
                os.path.expanduser(
                    os.path.expandvars(path)))))
    if not isinstance(path, str):
        raise TypeError("Path canonicalization should yield string, but "
                        f"returned {type(path)}.")
    if len(path) <= 0:
        raise ValueError("Canonicalization must yield non-empty string, "
                         f"but returned '{path}'.")
    if path in ['.', '..']:
        raise ValueError(f"Canonicalization cannot yield '{path}'.")
    return path


class Path(str):
    """An immutable representation of a path."""

    #: the common path version of this path, if any
    __common: Optional[str]

    def __new__(cls, value):
        """
        Construct the object.

        :param value: the string value
        """
        ret = super(Path, cls).__new__(cls, _canonicalize_path(value))
        ret.__common = None
        return ret

    def enforce_file(self) -> None:
        """
        A method which enforces that a path references an existing file.

        :raises ValueError:  if `path` does not reference an existing file
        """
        if not os.path.isfile(self):
            raise ValueError(f"Path '{self}' does not identify a file.")

    def enforce_dir(self) -> None:
        """
        A method which enforces that a path references an existing directory.

        :raises ValueError:  if `path` does not reference an existing directory
        """
        if not os.path.isdir(self):
            raise ValueError(f"Path '{self}' does not identify a directory.")

    def contains(self, other: str) -> bool:
        """
        Check whether another path is contained in this path.

        :param str other: the other path
        :return: `True` is this path contains the other path, `False` of mpt
        :rtype: bool
        """
        if self.__common is None:
            self.__common = os.path.commonpath([self])
        return self.__common == os.path.commonpath([self, Path.path(other)])

    def enforce_contains(self, other: str) -> None:
        """
        Raise an exception if this path does not contain the other path.

        :param str other: the other path
        :raises ValueError: if `other` is not a sub-path of this path
        """
        self.enforce_dir()
        if not self.contains(other):
            raise ValueError(f"Path '{self}' does not contain '{other}'.")

    def enforce_neither_contains(self, other: str) -> None:
        """
        Enforce that neither path contains another one.

        :param str other: the other path
        :raises ValueError: if `other` is contained in this path or vice versa
        """
        if self.__common is None:
            self.__common = os.path.commonpath([self])
        opath = Path.path(other)
        joint = os.path.commonpath([self, opath])
        if joint == self.__common:
            raise ValueError(f"Path '{self}' contains '{opath}'.")
        if opath.__common is None:
            opath.__common = os.path.commonpath([opath])
        if joint == opath.__common:
            raise ValueError(f"Path '{opath}' contains '{self}'.")

    def relative_to(self, base_path: str) -> str:
        """
        Compute a relative path of this path towards the given base path.

        :param str base_path: the string
        :return: a relative path
        :rtype: str
        :raises ValueError: if this path is not inside `base_path`
        """
        opath = Path.path(base_path)
        opath.enforce_contains(self)
        return enforce_non_empty_str_without_ws(
            os.path.relpath(opath, self))

    def resolve_inside(self, relative_path: str) -> 'Path':
        """
        Resolve a relative path to an absolute path inside this path.

        :param str relative_path: the path to resolve
        :return: the resolved child path
        :rtype: Path
        :raises ValueError: If the path would resolve to something outside of
            this path and/or if it is empty.
        """
        opath = Path.path(os.path.join(self, enforce_non_empty_str_without_ws(
            relative_path)))
        self.enforce_contains(opath)
        return opath

    def ensure_file_exist(self) -> bool:
        """
        Atomically ensure that the file exists and create it otherwise.

        :return:  `True` if the file already existed and
            `False` if it was newly and atomically created.
        :rtype: bool
        :raises: ValueError if anything goes wrong during the file creation
        """
        existed = False
        try:
            os.close(os.open(self, os.O_CREAT | os.O_EXCL))
        except FileExistsError:
            existed = True
        except Exception as err:
            raise ValueError(
                f"Error when trying to create file '{self}'.") from err
        self.enforce_file()
        return existed

    def dir_ensure_exists(self) -> None:
        """Make sure that the directory exists, create it otherwise."""
        os.makedirs(name=self, exist_ok=True)
        self.enforce_dir()

    def read_all(self) -> List[str]:
        """
        Read all the lines in a file.

        :return: the list of strings of text
        :rtype: List[str]
        """
        self.enforce_file()
        with io.open(self, "rt") as reader:
            return reader.readlines()

    def write_all(self, contents: Iterable[str]) -> None:
        """
        Read all the lines in a file.

        :param Iterable[str] contents: the contents to write
        """
        self.ensure_file_exist()
        with io.open(self, "wt") as writer:
            all_text = "\n".join(contents)
            if len(all_text) <= 0:
                raise ValueError("Writing empty text is not permitted.")
            writer.write(all_text)
            if all_text[-1] != "\n":
                writer.write("\n")

    @staticmethod
    def path(path: str) -> 'Path':
        """
        Get a canonical path.

        :param str path: the path to canonicalize
        :return: the `Path` instance
        :rtype: Path
        """
        if isinstance(path, Path):
            return cast(Path, path)
        return Path(path)
