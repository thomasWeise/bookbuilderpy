"""The state of a build."""

import datetime
import os
from contextlib import AbstractContextManager, ExitStack
from os.path import basename
from typing import Final, Optional, Dict, Any, Iterable, List

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File, LangResult
from bookbuilderpy.git import Repo
from bookbuilderpy.latex import latex
from bookbuilderpy.logger import log
from bookbuilderpy.pandoc import has_pandoc
from bookbuilderpy.parse_metadata import load_initial_metadata, parse_metadata
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor import preprocess
from bookbuilderpy.preprocessor_input import load_input
from bookbuilderpy.resources import load_resource
from bookbuilderpy.strings import datetime_to_date_str, \
    datetime_to_datetime_str, enforce_non_empty_str, \
    enforce_non_empty_str_without_ws
from bookbuilderpy.temp import TempDir


class Build(AbstractContextManager):
    """A class to keep and access information about the build process."""

    def __init__(self,
                 input_file: str,
                 output_dir: str,
                 fail_without_pandoc: bool = True):
        """
        Set up the build.

        :param str input_file: the input file
        :param str output_dir: the output dir
        :param bool fail_without_pandoc: fail if pandoc is not available?
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
        #: the start year
        self.__start_year: Final[str] = self.__start.strftime("%Y")
        #: the raw metadata
        self.__metadata_raw: Optional[Dict[str, Any]] = None
        #: the language-specific metadata
        self.__metadata_lang: Optional[Dict[str, Any]] = None
        #: the mapping of urls to repositories
        self.__repo_urls: Dict[str, Repo] = dict()
        #: the mapping of repo IDs to repositories
        self.__repo_ids: Dict[str, Repo] = dict()
        #: the internal collection of build results
        self.__results: List[LangResult] = list()
        #: the own repository information
        self.__repo: Optional[Repo] = None
        #: fail if pandoc is not available?
        self.__fail_without_pandoc: Final[bool] = fail_without_pandoc

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

    def __get_meta(self, key: str, raise_on_none: bool = True) -> Any:
        """
        Get a meta-data element.

        :param str key: the key
        :param bool raise_on_none: should we raise an error if the property
            was not found (True) or return None (False)?
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
        if key == bc.META_YEAR:
            return self.__start_year
        if key in (bc.META_GIT_URL, bc.META_GIT_DATE, bc.META_GIT_COMMIT):
            if self.__repo is None:
                if raise_on_none:
                    raise ValueError(
                        f"Cannot access {key} if build is not based on repo.")
                return None
            if key == bc.META_GIT_URL:
                return self.__repo.url
            if key == bc.META_GIT_COMMIT:
                return self.__repo.commit
            if key == bc.META_GIT_DATE:
                return self.__repo.date_time
            if raise_on_none:
                raise ValueError("Huh?")
            return None

        if self.__metadata_lang is not None:
            if key in self.__metadata_lang:
                return self.__metadata_lang[key]

        if self.__metadata_raw is not None:
            if key in self.__metadata_raw:
                return self.__metadata_raw[key]

        if raise_on_none:
            raise ValueError(f"Metadata key '{key}' not found.")
        return None

    def __get_meta_no_error(self, key: str) -> Any:
        """
        Get a meta data element without raising an error if it is not present.

        :param str key: the key
        :return: the meta data element, or None
        :rtype: Any
        """
        return self.__get_meta(key, False)

    def get_meta(self, key: str) -> Any:
        """
        Get a meta-data element.

        :param str key: the key
        :return: the meta-data element
        :rtype: Any
        """
        self.__get_meta(key, True)

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
        r = Repo.download(url, dest)
        self.__repo_ids[name] = r
        self.__repo_urls[r.url] = r

    def __load_repos_from_meta(self, meta: Dict[str, Any]) -> None:
        """
        Load the repositories listed in the metadata.

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

    def __get_resource(self, name: str, directory: Path) -> Optional[Path]:
        """
        A function used for getting an internal build resource to a directory.

        :param str name: the resource name
        :param Path directory: the destination path
        :return: the path to the resource, or None if none was copied
        :rtype: Optional[Path]
        """
        return load_resource(enforce_non_empty_str_without_ws(name),
                             self.__input_dir, directory)

    def __pandoc_build(self,
                       input_file: Path,
                       output_dir: Path,
                       lang_id: Optional[str],
                       lang_name: Optional[str]) -> None:
        """
        Apply pandoc and build the input file to the output dir.

        :param Path input_file: the path to the input file
        :param Path output_dir: the path to the output directory
        :param Optional[str] lang_id: the language ID
        :param Optional[str] lang_name: the language name
        """
        if not has_pandoc():
            if self.__fail_without_pandoc:
                raise ValueError("Pandoc not installed.")
            return
        input_file.enforce_file()
        output_dir.enforce_dir()
        name, _ = Path.split_prefix_suffix(os.path.basename(input_file))
        results: List[File] = list()

        results.append(latex(
            source_file=input_file,
            dest_file=output_dir.resolve_inside(f"{name}.pdf"),
            lang=lang_id,
            get_meta=self.__get_meta_no_error,
            resolve_resources=self.__get_resource))

        self.__results.append(LangResult(lang_id, lang_name, output_dir,
                                         tuple(results)))

    def __build_one_lang(self,
                         lang_id: Optional[str],
                         lang_name: Optional[str]) -> None:
        """
        Perform the book build for one language.

        :param Optional[str] lang_id: the language ID
        :param Optional[str] lang_name: the language name
        """
        self.__metadata_lang = None

        # Start up and define the output directory.
        if lang_id is None:
            log("Beginning build with no language set.")
            base_dir = self.output_dir
        else:
            lang_id = enforce_non_empty_str_without_ws(lang_id)
            log(f"Beginning build in language {lang_id}.")
            base_dir = self.output_dir.resolve_inside(lang_id)
            enforce_non_empty_str(lang_name)
        base_dir.ensure_dir_exists()

        # First obtain the full language-specific input text.
        text = enforce_non_empty_str(
            load_input(self.__input_file, self.__input_dir, lang_id).strip())

        # Then we extract the meta-data.
        self.__metadata_lang = parse_metadata(text)

        # Then load the repositories from the meta data.
        self.__load_repos_from_meta(self.__metadata_lang)

        with TempDir.create() as temp:
            log(f"Building in temp directory '{temp}': "
                "First applying preprocessor.")

            bib = self.__get_meta_no_error(bc.PANDOC_BIBLIOGRAPHY)
            if bib is not None:
                Path.copy_resource(self.__input_dir,
                                   self.__input_dir.resolve_inside(bib),
                                   temp)

            text = enforce_non_empty_str(preprocess(
                text=text, input_dir=self.input_dir,
                get_meta=self.get_meta, get_repo=self.get_repo,
                repo=self.__repo, output_dir=temp))

            prefix, suffix = Path.split_prefix_suffix(
                basename(self.__input_file))
            if lang_id is not None:
                end = "_" + lang_id
                if not prefix.endswith(end):
                    prefix = prefix + end
            file = temp.resolve_inside(f"{prefix}.{suffix}")
            log("Finished applying preprocessor, "
                f"now storing to file '{file}'.")
            file.write_all(text)
            del prefix, suffix, text
            self.__pandoc_build(file, base_dir, lang_id, lang_name)

        # Finalize the build.
        self.__metadata_lang = None
        if lang_id is None:
            log("Finished build with no language set.")
        else:
            log(f"Finished build in language {lang_id}.")

    def __load_self_repo(self) -> None:
        """Attempt to load the self repository information."""
        check = self.__input_dir
        while True:
            if check == "/":
                return
            if not os.access(check, os.R_OK):
                return
            test = Path.path(os.path.join(check, ".git"))
            if os.path.isdir(test):
                self.__repo = Repo.from_local(test)
                return
            check = Path.path(os.path.join(check, ".."))

    def __build_all_langs(self) -> None:
        """Perform all the book build steps."""
        no_lang = True
        if bc.META_LANGS in self.__metadata_raw:
            langs = self.__metadata_raw[bc.META_LANGS]
            done = set()
            if not isinstance(langs, Iterable):
                raise TypeError(
                    f"{bc.META_LANGS} must be Iterable but is {type(langs)}.")
            for lang in langs:
                if not isinstance(lang, dict):
                    raise TypeError(
                        f"Language item must be dict, but is {type(lang)}.")
                lang_id = enforce_non_empty_str_without_ws(
                    lang[bc.META_LANG_ID])
                if lang_id in done:
                    raise ValueError(f"Duplicate language id '{lang_id}'.")
                done.add(lang_id)
                lang_name = enforce_non_empty_str(enforce_non_empty_str(
                    lang[bc.META_LANG_NAME]).strip())
                self.__build_one_lang(lang_id, lang_name)
                no_lang = False

        if no_lang:
            self.__build_one_lang(None, None)

        # if len(self.__results) <= 0:
        #    raise ValueError("No builds discovered!")

    def build(self) -> None:
        """Perform the build."""
        self.__load_self_repo()
        self.__metadata_raw = load_initial_metadata(self.__input_file,
                                                    self.__input_dir)
        self.__load_repos_from_meta(self.__metadata_raw)
        self.__build_all_langs()

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
