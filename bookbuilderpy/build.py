"""The state of a build."""

import datetime
from contextlib import AbstractContextManager
from typing import Final

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path


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
        self.start: Final[datetime.datetime] = datetime.datetime.now(tz)
        #: the input file path
        self.input_file: Final[Path] = Path.file(input_file)
        #: the input directory
        self.input_dir: Final[Path] = self.input_file.as_directory()
        #: the output directory path
        self.output_dir: Final[Path] = Path.path(output_dir)
        self.output_dir.ensure_dir_exists()
        self.output_dir.enforce_neither_contains(self.input_dir)
        #: are we open for business?
        self.__is_open = True
        #: the start date
        self.start_date: Final[str] = \
            self.start.strftime("%Y\u2011%m\u2011%d")
        #: the start date and time
        self.start_time: Final[str] = \
            self.start.strftime("%Y\u2011%m\u2011%d\u00a0%H:%M\u00a0%Z")

    def __enter__(self) -> 'Build':
        """Nothing, just exists for `with`."""
        if not self.__is_open:
            raise ValueError("Build already closed.")
        log(f"starting the build of '{self.input_file}' "
            f"to '{self.output_dir}'.")
        return self

    def close(self) -> None:
        """Delete the temporary directory and everything in it."""
        opn = self.__is_open
        self.__is_open = False
        if opn:
            log(f"finished the build of '{self.input_file}' "
                f"to '{self.output_dir}'.")

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Call :meth:`close`.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        """
        self.close()
