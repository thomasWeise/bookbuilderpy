"""Tools for interacting with git."""
import datetime
import re
import subprocess  # nosec
from typing import Final, Tuple

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws, \
    enforce_non_empty_str, datetime_to_datetime_str


def load_repo(url: str,
              dest_dir: str) -> Tuple[Path, str, str, str]:
    """
    Load a git repository.

    :param url: the repository url
    :param dest_dir: the destination directory
    :return: a tuple with the path representation of the destination
        directory, the repository url, the commit string, and the
        date-time of the commit
    :rtype: Tuple[Path, str, str, str]
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

    match = re.search("^\\s*commit\\s+(.+?)\\s+", stdout, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"Did not find commit information in repo '{url}'.")
    commit: Final[str] = enforce_non_empty_str_without_ws(match.group(1))
    if len(commit) != 40:
        raise ValueError(
            f"Invalid commit information '{commit}' for repo '{url}'.")
    try:
        int(commit, 16)
    except ValueError as e:
        raise ValueError("Invalid commit information "
                         f"'{commit}' for repo '{url}'.") from e

    match = re.search("^\\s*Date:\\s+(.+?)$", stdout, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"Did not find date information in repo '{url}'.")
    date_str: Final[str] = enforce_non_empty_str(match.group(1))
    date_raw: Final[datetime.datetime] = datetime.datetime.strptime(
        date_str, "%a %b %d %H:%M:%S %Y %z")
    if not isinstance(date_raw, datetime.datetime):
        raise TypeError(
            f"Expected datetime.datetime, but got {type(date_raw)} when "
            f"parsing date string '{date_str}' of repo '{url}'.")
    date_time: Final[str] = datetime_to_datetime_str(date_raw)

    return dest, url, commit, date_time
