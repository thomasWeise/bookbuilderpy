"""The base class with the information of a build."""

import datetime
import gzip
import os.path
import shutil
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional

import bookbuilderpy.io as bio
from bookbuilderpy.strings import enforce_non_empty_str_without_ws


@dataclass(frozen=True, init=False, order=True)
class _StepCtx(AbstractContextManager):
    #: the name of the build step
    name: str
    #: the start date and time
    start: datetime.datetime

    def __init__(self, name: str):
        """
        Create the context manager for a build step.

        :param name: the name of the build step
        """
        object.__setattr__(self, "name",
                           enforce_non_empty_str_without_ws(name))
        object.__setattr__(self, "start", datetime.datetime.now())

    def __enter__(self):
        self.log("starting up")

    def __exit__(self, *args):
        self.log("finished after "
                 f"{(datetime.datetime.now() - self.start).total_seconds()}.")

    def log(self, message: str) -> None:
        """
        Write a message to the log.

        :param str message: the message
        """
        print(f"{datetime.datetime.now()}/{self.name}: {message}.")


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


@dataclass(frozen=True, init=False, order=True)
class Build(_StepCtx):
    """The immutable setup of a build."""

    #: The language used for the build.
    lang: str

    #: The input directory.
    in_dir: str

    #: The output directory.
    out_dir: str

    #: The start date as string.
    start_date: str
    #: The start date and time as string.
    start_datetime: str

    def __init__(self,
                 in_dir: str,
                 out_dir: str,
                 lang: Optional[str] = "en"):
        """
        Create the immutable build setup data.

        :param str in_dir: the input directory
        :param str out_dir: the output directory
        :param Optional[str] lang: the language
        """
        super().__init__("build")
        object.__setattr__(self, "in_dir", bio.enforce_dir(in_dir))
        out_dir = bio.dir_ensure_exists(out_dir)
        if bio.contains_path(in_dir, out_dir):
            raise ValueError(
                f"in_dir '{in_dir}' contains out_dir '{out_dir}'!")
        if bio.contains_path(out_dir, in_dir):
            raise ValueError(
                f"out_dir '{out_dir}' contains in_dir '{in_dir}'!")
        object.__setattr__(self, "out_dir", out_dir)
        if lang is None:
            lang = "en"
        if not isinstance(lang, str):
            raise TypeError(f"lang must be str but is {type(lang)}.")
        object.__setattr__(self, "lang", lang.strip())
        if len(self.lang) <= 0:
            raise ValueError(f"invalid language '${lang}'.")

        object.__setattr__(self, "start_date", self.start.strftime("%Y-%m-%d"))
        tz = self.start.strftime("%z")
        dt = f"{self.start_date} {self.start.strftime('%H:%M')}"
        object.__setattr__(self, "start_datetime",
                           dt if (len(tz) <= 0) else f"{dt} UTC{tz}")

    def resolve_input_file(self,
                           relative_path: str,
                           current_file: Optional[str] = None) -> str:
        """
        Resolved as an input file, optionally relative to another input file.

        If `relative_path` cannot be resolved to an existing file inside the
        input directory, then a `ValueError` will be raised. If no error is
        raised, then the string returned by this method is guaranteed to be
        the path of an existing file in the input folder.

        :param str relative_path: the file to resolve
        :param Optional[str] current_file: either a path to a current file or
            `None`, in which case the resolution is relative to `self.in_dir`.
        :return: the absolute path of the input file, which is guaranteed to
            exist
        :rtype: str
        """
        if current_file is None:
            base_dir = self.in_dir
        else:
            current_file = bio.enforce_file(
                enforce_non_empty_str_without_ws(current_file))
            if not bio.contains_path(self.in_dir, current_file):
                raise ValueError(f"File '{current_file}' is not included"
                                 f" in {self.in_dir}.")
            base_dir = os.path.dirname(current_file)
            if not bio.contains_path(self.in_dir, base_dir):
                raise ValueError(f"Directory '{base_dir}' is not included"
                                 f" in {self.in_dir}.")

        dirname, prefix, suffix = bio.file_path_split(relative_path)

        resolve_1 = bio.canonicalize_path(
            os.path.join(base_dir, bio.file_path_merge(
                f"{prefix}_{self.lang}", suffix, dirname)))
        if not bio.contains_path(self.in_dir, resolve_1):
            raise ValueError(f"Directory '{self.in_dir}' does not contain "
                             f"relative path '{resolve_1}'.")
        if not os.path.isfile(resolve_1):
            resolve_2 = bio.canonicalize_path(
                os.path.join(base_dir, bio.file_path_merge(
                    prefix, suffix, dirname)))
            if not bio.contains_path(self.in_dir, resolve_2):
                raise ValueError(f"Directory '{self.in_dir}' does not contain "
                                 f"relative path '{resolve_2}'.")
            if os.path.isfile(resolve_2):
                resolve_1 = resolve_2
            else:
                raise ValueError(f"Neither '{resolve_1}' nor '{resolve_2}' "
                                 "exists as a file.")
        resolve_1 = bio.enforce_file(resolve_1)
        if not bio.contains_path(self.in_dir, resolve_1):
            raise ValueError(f"Directory '{self.in_dir}' does not contain "
                             f"relative path '{resolve_1}'.")
        return resolve_1

    def copy_file_from_input_to_output(self, in_path: str) -> str:
        """
        Copy a file from the input to the output.

        :param str in_path: the absolute path to the input file, as returned
            by :meth:`resolve_input_file`.
        :return: the path to the output file, relative to the output folder
        :rtype: str
        """
        orig_in_path = in_path
        in_path = bio.enforce_file(in_path)
        if not bio.contains_path(self.in_dir, in_path):
            raise ValueError(
                f"'{orig_in_path}' is not in director '{self.in_dir}'.")

        dirname, prefix, suffix = bio.file_path_split(in_path)
        out_dir = bio.canonicalize_path(os.path.join(
            self.out_dir, os.path.relpath(dirname, self.in_dir)))
        if not bio.contains_path(self.out_dir, out_dir):
            raise ValueError(f"Output path '{out_dir}' resulting from path "
                             f"'{orig_in_path}' is not in the output "
                             f"directory '{self.out_dir}'.")
        out_dir = bio.dir_ensure_exists(out_dir)
        if suffix == "svgz":
            copier = _copy_un_gzip
            suffix = "svg"
        else:
            copier = _copy_pure

        dest_path = bio.canonicalize_path(os.path.join(
            out_dir, bio.file_path_merge(prefix, suffix)))
        if not bio.contains_path(self.out_dir, dest_path):
            raise ValueError(f"Destination path '{dest_path}' resulting from"
                             f"path '{orig_in_path}' is not in the output "
                             f"directory '{self.out_dir}'.")
        copier(in_path, dest_path)
        dest_path = bio.enforce_file(dest_path)
        ret = os.path.relpath(self.out_dir, dest_path)

        self.log(f"copied resource '{orig_in_path}' from input "
                 f"to output path '{ret}'.")
        return ret

    # noinspection PyMethodMayBeStatic
    def step(self, name: str) -> AbstractContextManager:
        """
        Perform a step of the build.

        :param str name: the name of the step
        :return: the context manager of the step
        :rtype: AbstractContextManager
        """
        return _StepCtx(name)
