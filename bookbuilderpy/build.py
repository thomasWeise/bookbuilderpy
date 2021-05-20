"""The state of a build."""

import datetime
from contextlib import AbstractContextManager
from typing import Final, Optional, Dict, Any

from bookbuilderpy.logger import log
from bookbuilderpy.parse_metadata import load_initial_metadata
from bookbuilderpy.path import Path
from bookbuilderpy.strings import datetime_to_date_str, \
    datetime_to_datetime_str


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

        if key == "date":
            return self.__start_date
        if key == "time":
            return self.__start_time

        if self.__metadata_lang is not None:
            if key in self.__metadata_lang:
                return self.__metadata_lang[key]

        if self.__metadata_raw is not None:
            if key in self.__metadata_raw:
                return self.__metadata_raw[key]

        raise ValueError(f"Metadata key '{key}' not found.")

    def build(self) -> None:
        """Perform the build."""
        self.__metadata_raw = load_initial_metadata(self.__input_file,
                                                    self.__input_dir)

    def __enter__(self) -> 'Build':
        """Nothing, just exists for `with`."""
        if not self.__is_open:
            raise ValueError("Build already closed.")
        log(f"starting the build of '{self.__input_file}' "
            f"to '{self.__output_dir}'.")
        return self

    def close(self) -> None:
        """Delete the temporary directory and everything in it."""
        opn = self.__is_open
        self.__is_open = False
        if opn:
            log(f"finished the build of '{self.__input_file}' "
                f"to '{self.__output_dir}'.")

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()
