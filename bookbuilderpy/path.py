"""The base class with the information of a build."""

import gzip
import io
import os.path
import shutil
from typing import cast, Optional, List, Iterable, Final, Union, Tuple

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


def _copy_pure(path_in: str, path_out: str):
    """
    The internal method to copy a file.

    :param str path_in: the path to the input file
    :param str path_out: the path to the output file
    """
    shutil.copyfile(path_in, path_out)


def _copy_un_gzip(path_in: str, path_out: str):
    """
    The internal method for copying a gzip-compressed file.

    :param str path_in: the path to the input file
    :param str path_out: the path to the output file
    """
    with gzip.open(path_in, 'rb') as f_in:
        with open(path_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


class Path(str):
    """An immutable representation of a path."""

    #: the common path version of this path, if any
    __common: Optional[str]
    #: the internal state: 0=don't know, 1=file, 2=dir
    __state: int

    def __new__(cls, value):
        """
        Construct the object.

        :param value: the string value
        """
        ret = super(Path, cls).__new__(cls, _canonicalize_path(value))
        ret.__common = None  # pylint: disable=W0238
        ret.__state = 0  # pylint: disable=W0238
        return ret

    def enforce_file(self) -> None:
        """
        A method which enforces that a path references an existing file.

        :raises ValueError:  if `path` does not reference an existing file
        """
        if self.__state == 0:
            if os.path.isfile(self):
                self.__state = 1
        if self.__state != 1:
            raise ValueError(f"Path '{self}' does not identify a file.")

    def enforce_dir(self) -> None:
        """
        A method which enforces that a path references an existing directory.

        :raises ValueError:  if `path` does not reference an existing directory
        """
        if self.__state == 0:
            if os.path.isdir(self):
                self.__state = 2
        if self.__state != 2:
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
        opath: Final[Path] = Path.path(other)
        joint: Final[str] = os.path.commonpath([self, opath])
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
        opath: Final[Path] = Path.path(base_path)
        opath.enforce_contains(self)
        return enforce_non_empty_str_without_ws(
            os.path.relpath(self, opath))

    def resolve_inside(self, relative_path: str) -> 'Path':
        """
        Resolve a relative path to an absolute path inside this path.

        :param str relative_path: the path to resolve
        :return: the resolved child path
        :rtype: Path
        :raises ValueError: If the path would resolve to something outside of
            this path and/or if it is empty.
        """
        opath: Final[Path] = Path.path(os.path.join(
            self, enforce_non_empty_str_without_ws(relative_path)))
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
        existed: bool = False
        try:
            os.close(os.open(self, os.O_CREAT | os.O_EXCL))
        except FileExistsError:
            existed = True
        except Exception as err:
            raise ValueError(
                f"Error when trying to create file '{self}'.") from err
        self.enforce_file()
        return existed

    def ensure_dir_exists(self) -> None:
        """Make sure that the directory exists, create it otherwise."""
        os.makedirs(name=self, exist_ok=True)
        self.enforce_dir()

    def read_all_list(self) -> List[str]:
        """
        Read all the lines in a file.

        :return: the list of strings of text
        :rtype: List[str]
        """
        self.enforce_file()
        with io.open(self, "rt") as reader:
            ret = reader.readlines()
        if not isinstance(ret, List):
            raise TypeError("List of strings expected, but "
                            f"found {type(ret)} in '{self}'.")
        if len(ret) <= 0:
            raise ValueError(f"File '{self}' contains no text.")
        return ret

    def read_all_str(self) -> str:
        """
        Read a file as a single string.

        :return: the single string of text
        :rtype: str
        """
        self.enforce_file()
        with io.open(self, "rt") as reader:
            ret = reader.read()
        if not isinstance(ret, str):
            raise TypeError("String expected, but "
                            f"found {type(ret)} in '{self}'.")
        if len(ret) <= 0:
            raise ValueError(f"File '{self}' contains no text.")
        return ret

    def write_all(self, contents: Union[str, Iterable[str]]) -> None:
        """
        Read all the lines in a file.

        :param Iterable[str] contents: the contents to write
        """
        self.ensure_file_exist()
        if not isinstance(contents, (str, Iterable)):
            raise TypeError(
                f"Excepted str or Iterable, got {type(contents)}.")
        with io.open(self, "wt") as writer:
            all_text = contents if isinstance(contents, str) \
                else "\n".join(contents)
            if len(all_text) <= 0:
                raise ValueError("Writing empty text is not permitted.")
            writer.write(all_text)
            if all_text[-1] != "\n":
                writer.write("\n")

    def as_directory(self) -> 'Path':
        """
        Return the closest directory along this path.

        :return: the directory: either this path if it already identifies a
            directory, or the parent directory if this path identifies a file.
        :rtype: Path
        :raises ValueError: if no containing directory exists
        """
        if os.path.isfile(self):
            base_dir = Path.path(os.path.dirname(self))
        else:
            base_dir = self
        base_dir.enforce_dir()
        return base_dir

    def resolve_input_file(self,
                           relative_path: str,
                           lang: Optional[str] = None) -> 'Path':
        """
        Resolve a path to an input file relative to this path.

        :param str relative_path: the relative path to resolve
        :param Optional[str] lang: the language to use
        :return: the resolved path
        :raises ValueError: if the path cannot be resolved to a file
        """
        relative_path = enforce_non_empty_str_without_ws(relative_path)
        lang = None if lang is None \
            else enforce_non_empty_str_without_ws(lang)

        base_dir: Final[Path] = self.as_directory()
        candidate: Path

        if lang is not None:
            prefix, suffix = Path.split_prefix_suffix(relative_path)
            candidate = base_dir.resolve_inside(f"{prefix}_{lang}.{suffix}")
            if os.path.isfile(candidate):
                candidate.__state = 1  # pylint: disable=W0238
                return candidate
        candidate = base_dir.resolve_inside(relative_path)
        candidate.enforce_file()
        return candidate

    @staticmethod
    def split_prefix_suffix(name: str) -> Tuple[str, str]:
        """
        Split the file name 'name' into a prefix and a suffix.

        :param str name: the file name
        :return: a tuple of [prefix, suffix]
        :rtype: Tuple[str, str]
        """
        dot: Final[int] = name.rfind(".")
        if (dot < 0) or (dot >= (len(name) - 1)):
            raise ValueError(f"'{name}' does not have suffix?")
        prefix: Final[str] = enforce_non_empty_str_without_ws(
            name[:dot])
        if prefix.strip() != prefix:
            raise ValueError(f"Prefix '{prefix}' contains white space?")
        suffix: Final[str] = enforce_non_empty_str_without_ws(
            name[dot + 1:])
        if suffix.strip() != suffix:
            raise ValueError(f"Suffix '{suffix}' contains white space?")
        return prefix, suffix

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

    @staticmethod
    def file(path: str) -> 'Path':
        """
        Get a path identifying a file.

        :param str path: the path
        :return: the file
        :rtype: Path
        """
        fi: Final[Path] = Path.path(path)
        fi.enforce_file()
        return fi

    @staticmethod
    def directory(path: str) -> 'Path':
        """
        Get a path identifying a directory.

        :param str path: the path
        :return: the file
        :rtype: Path
        """
        fi: Final[Path] = Path.path(path)
        fi.enforce_dir()
        return fi

    @staticmethod
    def copy_resource(source_dir: str,
                      input_file: str,
                      dest_dir: str) -> 'Path':
        """
        Copy an input file to an distination directory.

        :param str source_dir: the source directory
        :param str input_file: the input file
        :param str dest_dir: the destination directory
        :return: the path
        """
        in_dir = Path.path(source_dir)
        in_dir.enforce_dir()
        in_file = Path.path(input_file)
        in_file.enforce_file()
        out_dir = Path.path(dest_dir)
        out_dir.enforce_dir()
        in_dir.enforce_neither_contains(out_dir)

        rel_path = in_file.relative_to(in_dir)
        dot: Final[int] = rel_path.rfind(".")
        if (dot < 0) or (dot >= (len(rel_path) - 1)):
            raise ValueError(f"'{rel_path}' does not have suffix?")
        prefix: Final[str] = enforce_non_empty_str_without_ws(
            rel_path[:dot])
        suffix: Final[str] = enforce_non_empty_str_without_ws(
            rel_path[dot + 1:])
        if suffix == ".svgz":
            rel_path = f"{prefix}.svg"
            copy = _copy_un_gzip
        else:
            copy = _copy_pure

        out_path = out_dir.resolve_inside(rel_path)
        inner_dir = Path.path(os.path.dirname(out_path))
        out_dir.enforce_contains(inner_dir)
        inner_dir.ensure_dir_exists()

        copy(in_file, out_path)
        out_path.enforce_file()
        return out_path
