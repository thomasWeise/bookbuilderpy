"""Tools for interacting with git."""
import datetime
import re
import subprocess  # nosec
from dataclasses import dataclass
from typing import Final

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str, datetime_to_datetime_str


@dataclass(frozen=True, init=False, order=True)
class Repo:
    """An immutable record of a git repository."""

    #: the repository path
    path: Path
    #: the repository url
    url: str
    #: the commit
    commit: str
    #: the date and time
    date_time: str

    def __init__(self,
                 path: Path,
                 url: str,
                 commit: str,
                 date_time: str):
        """
        The information about a repository.

        :param Path path: the path
        :param str url: the url
        :param str commit: the commit
        :param str date_time: the date and time
        """
        if not isinstance(path, Path):
            raise TypeError(f"Expected Path, got '{type(path)}'.")
        path.enforce_dir()
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "url", enforce_non_empty_str_without_ws(url))
        object.__setattr__(self, "commit",
                           enforce_non_empty_str_without_ws(commit))
        if len(self.commit) != 40:
            raise ValueError(f"Invalid commit: '{self.commit}'.")
        try:
            int(self.commit, 16)
        except ValueError as e:
            raise ValueError("Invalid commit information "
                             f"'{self.commit}' for repo '{url}'.") from e
        object.__setattr__(self, "date_time",
                           enforce_non_empty_str(date_time))

    @staticmethod
    def load(url: str,
             dest_dir: str) -> 'Repo':
        """
        Load a git repository.

        :param url: the repository url
        :param dest_dir: the destination directory
        :return: the repository information
        :rtype: Repo
        """
        dest: Final[Path] = Path.path(dest_dir)
        dest.ensure_dir_exists()
        url = enforce_non_empty_str_without_ws(url)
        s = f" repository '{url}' to directory '{dest}'"
        log(f"starting to load{s}.")
        ret = subprocess.run(["git", "-C", dest, "clone", "--depth",  # nosec
                              "1", url, dest], text=True, check=True,  # nosec
                             timeout=300)  # nosec
        if ret.returncode != 0:
            raise ValueError(f"Error when loading{s}.")

        log(f"successfully finished loading{s},"
            f"now checking its commit information.")

        ret = subprocess.run(["git", "-C", dest, "log",  # nosec
                              "--no-abbrev-commit"], check=True,  # nosec
                             text=True, stdout=subprocess.PIPE,  # nosec
                             timeout=120)  # nosec
        if ret.returncode != 0:
            raise ValueError(
                f"Error when loading commit information for '{url}'.")
        stdout: str = enforce_non_empty_str(ret.stdout)

        match = re.search("^\\s*commit\\s+(.+?)\\s+", stdout,
                          flags=re.MULTILINE)
        if match is None:
            raise ValueError(
                f"Did not find commit information in repo '{url}'.")
        commit: Final[str] = enforce_non_empty_str_without_ws(match.group(1))
        match = re.search("^\\s*Date:\\s+(.+?)$", stdout, flags=re.MULTILINE)
        if match is None:
            raise ValueError(
                f"Did not find date information in repo '{url}'.")
        date_str: Final[str] = enforce_non_empty_str(match.group(1))
        date_raw: Final[datetime.datetime] = datetime.datetime.strptime(
            date_str, "%a %b %d %H:%M:%S %Y %z")
        if not isinstance(date_raw, datetime.datetime):
            raise TypeError(
                f"Expected datetime.datetime, but got {type(date_raw)} when "
                f"parsing date string '{date_str}' of repo '{url}'.")
        date_time: Final[str] = datetime_to_datetime_str(date_raw)

        return Repo(dest, url, commit, date_time)