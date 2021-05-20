"""The state of a build."""

import datetime
from contextlib import AbstractContextManager, ExitStack
from typing import Final, Optional, Dict, Any, Iterable

import bookbuilderpy.constants as bc
from bookbuilderpy.git import Repo
from bookbuilderpy.logger import log
from bookbuilderpy.parse_metadata import load_initial_metadata
from bookbuilderpy.path import Path
from bookbuilderpy.strings import datetime_to_date_str, \
    datetime_to_datetime_str, enforce_non_empty_str
from bookbuilderpy.temp import TempDir


class Build(AbstractContextManager):
    """A class to keep and access information about the build process."""

    def __init__(self,
                 input_file: str,
                 output_dir: str):
        """
        Set up the build.

        :param str input_file: the input file
        :param str output_dir: the output dir
        """
        super().__init__()

        #: the start time
        tz: Final[datetime.timezone] = datetime.timezone.utc
        self.__start: Final[datetime.datetime] = datetime.datetime.now(tz)
        #: the internal exit stack
        self.__exit: Final[ExitStack] = ExitStack()
        #: the input file path
        self.__input_file: Final[Path] = Path.file(input_file)
        #: the input directory
        self.__input_dir: Final[Path] = self.__input_file.as_directory()
        #: the output directory path
        self.__output_dir: Final[Path] = Path.path(output_dir)
        self.__output_dir.ensure_dir_exists()
        self.__output_dir.enforce_neither_contains(self.__input_dir)
        #: are we open for business?
        self.__is_open = True
        #: the start date
        self.__start_date: Final[str] = datetime_to_date_str(self.__start)
        #: the start date and time
        self.__start_time: Final[str] = datetime_to_datetime_str(self.__start)
        #: the raw metadata
        self.__metadata_raw: Optional[Dict[str, Any]] = None
        #: the language-specific metadata
        self.__metadata_lang: Optional[Dict[str, Any]] = None
        #: the mapping of urls to repositories
        self.__repo_urls: Dict[str, Repo] = dict()
        #: the mapping of repo IDs to repositories
        self.__repo_ids: Dict[str, Repo] = dict()

    @property
    def input_dir(self) -> Path:
        """
        Get the input directory.

        :return: the input directory
        :rtype: Path
        """
        return self.__input_dir

    @property
    def input_file(self) -> Path:
        """
        Get the input file.

        :return: the input file
        :rtype: Path
        """
        return self.__input_file

    @property
    def output_dir(self) -> Path:
        """
        Get the output directory.

        :return: the output directory
        :rtype: Path
        """
        return self.__output_dir

    def get_meta(self, key: str) -> Any:
        """
        Get a meta-data element.

        :param str key: the key
        :return: the meta-data element
        :rtype: Any
        """
        if not isinstance(key, str):
            raise TypeError(f"key must be str, but is {type(key)}.")
        key = key.strip()

        if key == bc.META_DATE:
            return self.__start_date
        if key == bc.META_DATE_TIME:
            return self.__start_time

        if self.__metadata_lang is not None:
            if key in self.__metadata_lang:
                return self.__metadata_lang[key]

        if self.__metadata_raw is not None:
            if key in self.__metadata_raw:
                return self.__metadata_raw[key]

        raise ValueError(f"Metadata key '{key}' not found.")

    def __load_repo(self, name: str, url: str) -> None:
        """
        Make the repository at the specified url available under the given id.

        :param str name: the repository name
        :param str url: the repository url
        """
        name = enforce_non_empty_str(name).strip()
        url = enforce_non_empty_str(url).strip()
        if name in self.__repo_ids:
            r = self.__repo_ids[name]
            if r.url == url:
                return
            del self.__repo_ids[name]
        if url in self.__repo_urls:
            self.__repo_ids[name] = self.__repo_urls[url]
        dest = TempDir.create()
        self.__exit.push(dest)
        r = Repo.load(url, dest)
        self.__repo_ids[name] = r
        self.__repo_urls[r.url] = r

    def __load_repos_from_meta(self, meta: Dict[str, Any]) -> None:
        """
        Load the repositories listed in the metadata-

        :param Dict[str, Any] meta: the metadata
        """
        if not isinstance(meta, dict):
            raise TypeError(f"Expected dict, got {type(meta)}.")
        if bc.META_REPOS in meta:
            repo_list = meta[bc.META_REPOS]
            if not isinstance(repo_list, Iterable):
                raise TypeError(f"{bc.META_REPOS} must be iterable, "
                                f"but is {type(repo_list)}.")
            for repo in repo_list:
                if bc.META_REPO_ID not in repo:
                    raise ValueError(
                        f"repo {repo} must include '{bc.META_REPO_ID}'.")
                if bc.META_REPO_URL not in repo:
                    raise ValueError(
                        f"repo {repo} must include '{bc.META_REPO_URL}'.")
                self.__load_repo(repo[bc.META_REPO_ID],
                                 repo[bc.META_REPO_URL])

    def get_repo(self, name: str) -> Repo:
        """
        Get a repository of the given name.

        :param str name: the repository name
        :return: the repository structure
        :rtype: Repo
        """
        name = enforce_non_empty_str(name).strip()
        if not (name in self.__repo_ids):
            raise ValueError(f"unknown repository '{name}'.")
        r = self.__repo_ids[name]
        if not isinstance(r, Repo):
            raise ValueError(f"invalid repository '{name}'?")
        return r

    def build(self) -> None:
        """Perform the build."""
        self.__metadata_raw = load_initial_metadata(self.__input_file,
                                                    self.__input_dir)
        self.__load_repos_from_meta(self.__metadata_raw)

    def __enter__(self) -> 'Build':
        """Nothing, just exists for `with`."""
        if not self.__is_open:
            raise ValueError("Build already closed.")
        log(f"starting the build of '{self.__input_file}' "
            f"to '{self.__output_dir}'.")
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Delete the temporary directory and everything in it.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        opn = self.__is_open
        self.__is_open = False
        if opn:
            log("cleaning up temporary files.")
            self.__exit.close()
            log(f"finished the build of '{self.__input_file}' "
                f"to '{self.__output_dir}'.")
