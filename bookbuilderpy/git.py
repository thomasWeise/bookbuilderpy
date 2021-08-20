"""Tools for interacting with git."""
import datetime
import re
import subprocess  # nosec
from dataclasses import dataclass
from typing import Final
from typing import Optional

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str, datetime_to_datetime_str, enforce_url


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
        object.__setattr__(self, "url", enforce_url(url))
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
    def download(url: str,
                 dest_dir: str) -> 'Repo':
        """
        Download a git repository.

        :param url: the repository url
        :param dest_dir: the destination directory
        :return: the repository information
        :rtype: Repo
        """
        dest: Final[Path] = Path.path(dest_dir)
        dest.ensure_dir_exists()
        url = enforce_url(url)
        s = f" repository '{url}' to directory '{dest}'"
        log(f"starting to load{s}.")
        ret = subprocess.run(["git", "-C", dest, "clone", "--depth",  # nosec
                              "1", url, dest], text=True, check=True,  # nosec
                             timeout=300)  # nosec
        if ret.returncode != 0:
            raise ValueError(f"Error when loading{s}.")

        log(f"successfully finished loading{s}.")

        return Repo.from_local(path=dest, url=url)

    @staticmethod
    def from_local(path: str,
                   url: Optional[str] = None) -> 'Repo':
        """
        Load all the information from an local repository.

        :param path: the path to the repository
        :param Optional[str] url: the url
        :return: the repository information
        :rtype: Repo
        """
        dest: Final[Path] = Path.path(path)
        dest.enforce_dir()

        log(f"checking commit information of repo '{dest}'.")

        ret = subprocess.run(["git", "-C", dest, "log",  # nosec
                              "--no-abbrev-commit"], check=True,  # nosec
                             text=True, stdout=subprocess.PIPE,  # nosec
                             timeout=120)  # nosec
        if ret.returncode != 0:
            raise ValueError(
                f"Error when loading commit information for '{dest}'.")
        stdout: str = enforce_non_empty_str(ret.stdout)

        match = re.search("^\\s*commit\\s+(.+?)\\s+", stdout,
                          flags=re.MULTILINE)
        if match is None:
            raise ValueError(
                f"Did not find commit information in repo '{dest}'.")
        commit: Final[str] = enforce_non_empty_str_without_ws(match.group(1))
        match = re.search("^\\s*Date:\\s+(.+?)$", stdout, flags=re.MULTILINE)
        if match is None:
            raise ValueError(
                f"Did not find date information in repo '{dest}'.")
        date_str: Final[str] = enforce_non_empty_str(match.group(1))
        date_raw: Final[datetime.datetime] = datetime.datetime.strptime(
            date_str, "%a %b %d %H:%M:%S %Y %z")
        if not isinstance(date_raw, datetime.datetime):
            raise TypeError(
                f"Expected datetime.datetime, but got {type(date_raw)} when "
                f"parsing date string '{date_str}' of repo '{dest}'.")
        date_time: Final[str] = datetime_to_datetime_str(date_raw)
        log(f"Found commit '{commit}' and date/time '{date_time}' "
            f"for repo '{dest}'.")

        if url is None:
            ret = subprocess.run(["git", "-C", dest, "config",  # nosec
                                  "--get", "remote.origin.url"],  # nosec
                                 check=True, text=True,  # nosec
                                 stdout=subprocess.PIPE, timeout=120)  # nosec
            if ret.returncode != 0:
                raise ValueError(
                    f"Error when loading origin url information of '{dest}'.")
            url = enforce_non_empty_str(ret.stdout)
            url = enforce_non_empty_str_without_ws(
                url.strip().split("\n")[0].strip())
            log(f"Found url '{url}' for repo '{dest}'.")
            if url.startswith("ssh://git@github.com"):
                url = f"https://{url[10:]}"

        return Repo(dest, url, commit, date_time)

    def make_url(self, relative_path: str) -> str:
        """
        Make a url relative to this repository.

        :param str relative_path: the relative path
        :return: the url
        :rtype: str
        """
        pt: Final[Path] = self.path.resolve_inside(relative_path)
        pt.ensure_file_exist()
        path: Final[str] = pt.relative_to(self.path)

        base_url = self.url
        if base_url.lower().endswith(".git"):
            base_url = enforce_non_empty_str_without_ws(base_url[:-4])

        return enforce_url(f"{base_url}/blob/{self.commit}/{path}")

    def get_name(self) -> str:
        """
        Get the name of this repository in the form 'user/name'.

        :return: the name of this repository in the form 'user/name'.
        :rtype: str
        """
        base_url = self.url
        if base_url.lower().endswith(".git"):
            base_url = enforce_non_empty_str_without_ws(base_url[:-4])
        si = base_url.rfind("/")
        if si <= 0:
            return base_url
        si = max(0, base_url.rfind("/", 0, si - 1))
        return enforce_non_empty_str(base_url[si + 1:].strip())
