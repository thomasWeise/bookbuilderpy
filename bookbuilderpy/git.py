"""Tools for interacting with git."""
import datetime
import re
from dataclasses import dataclass
from shutil import rmtree
from subprocess import TimeoutExpired  # nosec
from typing import Final
from typing import Optional

from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.shell import shell
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str, datetime_to_datetime_str, enforce_url
from bookbuilderpy.types import type_error
from bookbuilderpy.versions import TOOL_GIT, has_tool


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
        Set up the information about a repository.

        :param path: the path
        :param url: the url
        :param commit: the commit
        :param date_time: the date and time
        """
        if not isinstance(path, Path):
            raise type_error(path, "path", Path)
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
        logger(f"found repository in path '{self.path}' with commit "
               f"'{self.commit}' for url '{self.url}' and "
               f"date '{self.date_time}'.")

    @staticmethod
    def download(url: str,
                 dest_dir: str) -> 'Repo':
        """
        Download a git repository.

        :param url: the repository url
        :param dest_dir: the destination directory
        :return: the repository information
        """
        if not has_tool(TOOL_GIT):
            raise ValueError(f"No '{TOOL_GIT}' installation found.")

        dest: Final[Path] = Path.path(dest_dir)
        dest.ensure_dir_exists()
        url = enforce_url(url)
        s = f" repository '{url}' to directory '{dest}'"
        logger(f"starting to load{s} via '{TOOL_GIT}'.")
        try:
            shell([TOOL_GIT, "-C", dest, "clone",
                   "--depth", "1", url, dest], timeout=300,
                  cwd=dest)
        except TimeoutExpired:
            if url.startswith("https://github.com"):
                url2 = enforce_url(f"ssh://git@{url[8:]}")
                logger(f"timeout when loading url '{url}', so we try "
                       f"'{url2}' instead, but first delete '{dest}'.")
                rmtree(dest, ignore_errors=True, onerror=None)
                dest.ensure_dir_exists()
                logger(f"'{dest}' deleted and created, now re-trying cloning.")
                shell([TOOL_GIT, "-C", dest, "clone",
                      "--depth", "1", url2, dest], timeout=300,
                      cwd=dest)
            else:
                logger(f"timeout when loading url '{url}'.")
                raise
        logger(f"successfully finished loading{s}.")

        return Repo.from_local(path=dest, url=url)

    @staticmethod
    def from_local(path: str,
                   url: Optional[str] = None) -> 'Repo':
        """
        Load all the information from an local repository.

        :param path: the path to the repository
        :param url: the url
        :return: the repository information
        """
        if not has_tool(TOOL_GIT):
            raise ValueError(f"No '{TOOL_GIT}' installation found.")

        dest: Final[Path] = Path.path(path)
        dest.enforce_dir()

        logger(
            f"checking commit information of repo '{dest}' via '{TOOL_GIT}'.")
        stdout: str = enforce_non_empty_str(shell(
            [TOOL_GIT, "-C", dest, "log", "--no-abbrev-commit", "-1"],
            timeout=120, cwd=dest, wants_stdout=True))

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
            raise type_error(date_raw, "date_raw", datetime.datetime)
        date_time: Final[str] = datetime_to_datetime_str(date_raw)
        logger(f"found commit '{commit}' and date/time '{date_time}' "
               f"for repo '{dest}'.")

        if url is None:
            logger(f"applying '{TOOL_GIT}' to get url information.")
            url = enforce_non_empty_str(shell(
                [TOOL_GIT, "-C", dest, "config", "--get", "remote.origin.url"],
                timeout=120, cwd=dest, wants_stdout=True))
            url = enforce_non_empty_str_without_ws(
                url.strip().split("\n")[0].strip())
            if url.endswith("/.git"):
                url = enforce_non_empty_str_without_ws(f"{url[:-5]}.git")
            if url.endswith("/"):
                url = enforce_non_empty_str_without_ws(url[:-1])
            logger(f"found url '{url}' for repo '{dest}'.")
            if url.startswith("ssh://git@github.com"):
                url = f"https://{url[10:]}"

        return Repo(dest, url, commit, date_time)

    def get_base_url(self) -> str:
        """
        Get the base url of this repository.

        :return: the base url of this repository
        """
        base_url = self.url
        base_url_lower = base_url.lower()
        if base_url_lower.startswith("ssh://git@github."):
            base_url = f"https://{enforce_non_empty_str(base_url[10:])}"
        if base_url_lower.endswith(".git"):
            base_url = enforce_non_empty_str(base_url[:-4])
        return enforce_url(base_url)

    def make_url(self, relative_path: str) -> str:
        """
        Make an url relative to this repository.

        :param relative_path: the relative path
        :return: the url
        """
        pt: Final[Path] = self.path.resolve_inside(relative_path)
        pt.ensure_file_exists()
        path: Final[str] = pt.relative_to(self.path)

        base_url = self.get_base_url()

        if "github.com" in base_url.lower():
            base_url = f"{base_url}/blob/{self.commit}/{path}"
        else:
            base_url = f"{base_url}/{path}"
        return enforce_url(base_url)

    def get_name(self) -> str:
        """
        Get the name of this repository in the form 'user/name'.

        :return: the name of this repository in the form 'user/name'.
        """
        base_url = self.url
        if base_url.lower().endswith(".git"):
            base_url = enforce_non_empty_str_without_ws(base_url[:-4])
        si = base_url.rfind("/")
        if si <= 0:
            return base_url
        si = max(0, base_url.rfind("/", 0, si - 1))
        return enforce_non_empty_str(base_url[si + 1:].strip())
