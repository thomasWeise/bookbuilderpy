"""The build process: The main class of the book building tool chain."""

import datetime
import os
import sys
import traceback as tb
from contextlib import AbstractContextManager, ExitStack
from os.path import basename
from typing import Final, Optional, Dict, Any, Iterable, List, Tuple

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File, LangResult
from bookbuilderpy.compress import can_xz_compress, can_zip_compress, \
    compress_xz, compress_zip
from bookbuilderpy.git import Repo
from bookbuilderpy.logger import logger
from bookbuilderpy.pandoc import latex, html, epub, azw3
from bookbuilderpy.parse_metadata import load_initial_metadata, parse_metadata
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor import preprocess
from bookbuilderpy.preprocessor_input import load_input
from bookbuilderpy.resources import load_resource
from bookbuilderpy.strings import datetime_to_date_str, \
    datetime_to_datetime_str, enforce_non_empty_str, \
    enforce_non_empty_str_without_ws, lang_to_locale, to_string
from bookbuilderpy.temp import TempDir
from bookbuilderpy.types import type_error
from bookbuilderpy.versions import get_versions, has_tool, TOOL_PANDOC
from bookbuilderpy.website import build_website


class Build(AbstractContextManager):
    """A class to keep and access information about the build process."""

    def __init__(self,
                 input_file: str,
                 output_dir: str,
                 fail_without_pandoc: bool = True):
        """
        Set up the build.

        :param input_file: the input file
        :param output_dir: the output dir
        :param fail_without_pandoc: fail if pandoc is not available?
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
        self.__repo_urls: Dict[str, Repo] = {}
        #: the mapping of repo IDs to repositories
        self.__repo_ids: Dict[str, Repo] = {}
        #: the internal collection of build results
        self.__results: List[LangResult] = []
        #: the own repository information
        self.__repo: Optional[Repo] = None
        #: fail if pandoc is not available?
        self.__fail_without_pandoc: Final[bool] = fail_without_pandoc

    @property
    def input_dir(self) -> Path:
        """
        Get the input directory.

        :return: the input directory
        """
        return self.__input_dir

    @property
    def input_file(self) -> Path:
        """
        Get the input file.

        :return: the input file
        """
        return self.__input_file

    @property
    def output_dir(self) -> Path:
        """
        Get the output directory.

        :return: the output directory
        """
        return self.__output_dir

    def __get_meta(self, key: str, raise_on_none: bool = True) -> Any:
        """
        Get a meta-data element.

        :param key: the key
        :param raise_on_none: should we raise an error if the property
            was not found (True) or return None (False)?
        :return: the meta-data element
        """
        if not isinstance(key, str):
            raise type_error(key, "key", str)
        key = key.strip()

        if key == bc.META_DATE:
            return self.__start_date
        if key == bc.META_DATE_TIME:
            return self.__start_time
        if key == bc.META_YEAR:
            return self.__start_year

        if self.__metadata_lang is not None:
            if key in self.__metadata_lang:
                return self.__metadata_lang[key]

        if self.__metadata_raw is not None:
            if key in self.__metadata_raw:
                return self.__metadata_raw[key]

        # If no meta data language properties are set: return default values.
        if key == bc.META_LANG:
            return "en"
        if key == bc.META_LOCALE:
            return lang_to_locale(self.__get_meta(bc.META_LANG, False))
        if key in (bc.META_LANG_NAME, bc.META_CUR_LANG_NAME):
            return "English"

        if key in (bc.META_REPO_INFO_URL, bc.META_REPO_INFO_DATE,
                   bc.META_REPO_INFO_COMMIT, bc.META_REPO_INFO_NAME):
            if self.__repo is None:
                if raise_on_none:
                    raise ValueError(
                        f"Cannot access {key} if build is not based on repo.")
                return None
            if key == bc.META_REPO_INFO_URL:
                return self.__repo.get_base_url()
            if key == bc.META_REPO_INFO_DATE:
                return self.__repo.date_time
            if key == bc.META_REPO_INFO_COMMIT:
                return self.__repo.commit
            return self.__repo.get_name()

        if raise_on_none:
            raise ValueError(f"Metadata key '{key}' not found.")
        return None

    def __get_meta_no_error(self, key: str) -> Any:
        """
        Get a metadata element without raising an error if it is not present.

        :param key: the key
        :return: the metadata element, or None
        """
        return self.__get_meta(key, False)

    def get_meta(self, key: str) -> Any:
        """
        Get a meta-data element.

        :param key: the key
        :return: the meta-data element
        """
        return self.__get_meta(key, True)

    def get_meta_str(self, key: str) -> str:
        """
        Get a meta-data element as a string.

        :param key: the key
        :return: the meta-data element
        """
        return to_string(obj=self.get_meta(key),
                         locale=self.__get_meta_no_error(bc.META_LOCALE),
                         use_seq_and=key == bc.META_AUTHOR)

    def __load_repo(self, name: str, url: str) -> None:
        """
        Make the repository at the specified url available under the given id.

        :param name: the repository name
        :param url: the repository url
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

        :param meta: the metadata
        """
        if not isinstance(meta, dict):
            raise type_error(meta, "meta", Dict)
        logger("checking metadata for repositories.")
        if bc.META_REPOS in meta:
            repo_list = meta[bc.META_REPOS]
            if not isinstance(repo_list, Iterable):
                raise type_error(
                    repo_list, f"meta[{bc.META_REPOS}]", Iterable)
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

        :param name: the repository name
        :return: the repository structure
        """
        name = enforce_non_empty_str(name).strip()
        if not (name in self.__repo_ids):
            raise ValueError(f"unknown repository '{name}'.")
        r = self.__repo_ids[name]
        if not isinstance(r, Repo):
            raise type_error(name, f"invalid repository '{name}'?", Repo)
        return r

    def __get_resource(self, name: str, directory: Path) -> Optional[Path]:
        """
        Get an internal build resource to a directory.

        :param name: the resource name
        :param directory: the destination path
        :return: the path to the resource, or None if none was copied
        """
        return load_resource(enforce_non_empty_str_without_ws(name),
                             self.__input_dir, directory)

    def __pandoc_build(self,
                       input_file: Path,
                       output_dir: Path,
                       lang_id: Optional[str],
                       lang_name: Optional[str],
                       has_bibliography: bool) -> None:
        """
        Apply pandoc and build the input file to the output dir.

        :param input_file: the path to the input file
        :param output_dir: the path to the output directory
        :param lang_id: the language ID
        :param lang_name: the language name
        :param has_bibliography: is there a bibliography?
        """
        if not has_tool(TOOL_PANDOC):
            if self.__fail_without_pandoc:
                raise ValueError("Pandoc not installed.")
            return
        logger(f"now invoking pandoc build steps to file '{input_file}' "
               f"with target director '{output_dir}' for lang-id "
               f"'{lang_id}'.")
        input_file.enforce_file()
        output_dir.enforce_dir()
        name, _ = Path.split_prefix_suffix(os.path.basename(input_file))
        results: List[File] = []
        locale: Optional[str] = self.__get_meta_no_error(bc.META_LOCALE)

        results.append(latex(
            source_file=input_file,
            dest_file=output_dir.resolve_inside(f"{name}.pdf"),
            locale=locale,
            bibliography=has_bibliography,
            get_meta=self.__get_meta_no_error,
            resolve_resources=self.__get_resource))
        results.append(html(
            source_file=input_file,
            dest_file=output_dir.resolve_inside(f"{name}.html"),
            locale=locale,
            bibliography=has_bibliography,
            get_meta=self.__get_meta_no_error,
            resolve_resources=self.__get_resource))
        epub_res = epub(
            source_file=input_file,
            dest_file=output_dir.resolve_inside(f"{name}.epub"),
            locale=locale,
            bibliography=has_bibliography,
            get_meta=self.__get_meta_no_error,
            resolve_resources=self.__get_resource)
        results.append(epub_res)
        results.append(azw3(epub_res.path))

        # now trying to create compressed versions
        if can_xz_compress():
            tar_xz = compress_xz(results,
                                 output_dir.resolve_inside(f"{name}.tar.xz"))
        else:
            tar_xz = None
        if can_zip_compress():
            zipf = compress_zip(results,
                                output_dir.resolve_inside(f"{name}.zip"))
        else:
            zipf = None

        if tar_xz:
            results.append(tar_xz)
        if zipf:
            results.append(zipf)

        logger(f"finished pandoc build steps to file '{input_file}' "
               f"with target director '{output_dir}' for lang-id '{lang_id}'"
               f", produced {len(results)} files.")

        self.__results.append(LangResult(lang_id, lang_name, output_dir,
                                         tuple(results)))

    def __build_one_lang(self,
                         lang_id: Optional[str],
                         lang_name: Optional[str],
                         use_lang_id_as_suffix: bool = False) -> None:
        """
        Perform the book build for one language.

        :param lang_id: the language ID
        :param lang_name: the language name
        :param use_lang_id_as_suffix: should we use the language id as
            file name suffix?
        """
        self.__metadata_lang = None

        # Start up and define the output directory.
        if lang_id is None:
            logger("beginning build with no language set.")
            base_dir = self.output_dir
            if lang_name:
                raise ValueError("Cannot have language name "
                                 f"'{lang_name}' but no language id!")
        elif use_lang_id_as_suffix:
            lang_id = enforce_non_empty_str_without_ws(lang_id)
            logger(f"beginning multi-language build for language {lang_id}.")
            base_dir = self.output_dir.resolve_inside(lang_id)
            if lang_name:
                enforce_non_empty_str(lang_name)
        else:
            logger(f"beginning single-language build in language {lang_id}.")
            base_dir = self.output_dir
            if lang_name:
                enforce_non_empty_str(lang_name)
        base_dir.ensure_dir_exists()

        # First obtain the full language-specific input text.
        text = enforce_non_empty_str(
            load_input(self.__input_file, self.__input_dir, lang_id).strip())

        # Then we extract the meta-data.
        self.__metadata_lang = parse_metadata(text)
        logger("done parsing metadata.")
        if lang_id:
            # We set up the language id and lange name meta data properties.
            if bc.META_LANG not in self.__metadata_lang.keys():
                self.__metadata_lang[bc.META_LANG] = lang_id
            if bc.META_CUR_LANG_NAME not in self.__metadata_lang.keys():
                self.__metadata_lang[bc.META_CUR_LANG_NAME] = lang_name

        # Then load the repositories from the meta data.
        self.__load_repos_from_meta(self.__metadata_lang)

        with TempDir.create() as temp:
            logger(f"building in temp directory '{temp}': "
                   "first applying preprocessor.")

            text = enforce_non_empty_str(preprocess(
                text=text, input_dir=self.input_dir,
                get_meta=self.get_meta_str, get_repo=self.get_repo,
                repo=self.__repo, output_dir=temp))
            logger("finished applying preprocessor.")

            has_bibliography = False
            bib = self.__get_meta_no_error(bc.PANDOC_BIBLIOGRAPHY)
            if bib:
                logger(f"found bibliography spec '{bib}', so we load it.")
                Path.copy_resource(self.__input_dir,
                                   self.__input_dir.resolve_inside(bib),
                                   temp)
                has_bibliography = True

            prefix, suffix = Path.split_prefix_suffix(
                basename(self.__input_file))
            if use_lang_id_as_suffix:
                end = "_" + enforce_non_empty_str_without_ws(lang_id)
                if not prefix.endswith(end):
                    prefix = prefix + end
            file = temp.resolve_inside(f"{prefix}.{suffix}")
            logger("finished applying preprocessor, now storing "
                   f"{len(text)} characters to file '{file}'.")
            file.write_all(text)
            del prefix, suffix, text
            self.__pandoc_build(input_file=file,
                                output_dir=base_dir,
                                lang_id=lang_id,
                                lang_name=lang_name,
                                has_bibliography=has_bibliography)

        # Finalize the build.
        self.__metadata_lang = None
        if lang_id is None:
            logger("finished build with no language set.")
        else:
            logger(f"finished build in language {lang_id}.")

    def __load_self_repo(self) -> None:
        """Attempt to load the self repository information."""
        logger("checking if build process is based on git checkout.")
        check = self.__input_dir
        while True:
            if check == "/":
                break
            if not os.access(check, os.R_OK):
                break
            test = Path.path(os.path.join(check, ".git"))
            if os.path.isdir(test):
                self.__repo = Repo.from_local(check)
                logger(
                    f"build process is based on commit '{self.__repo.commit}'"
                    f" of repo '{self.__repo.url}'.")
                return
            check = Path.path(os.path.join(check, ".."))
        logger("build process is not based on git checkout.")

    def __build_all_langs(self) -> None:
        """Perform all the book build steps."""
        logger("beginning the build loop for all languages.")
        no_lang = True
        if bc.META_LANGS in self.__metadata_raw:
            langs = self.__metadata_raw[bc.META_LANGS]
            done = set()
            if not isinstance(langs, Iterable):
                raise type_error(
                    langs, f"self.__metadata_raw[{bc.META_LANGS}]", Iterable)
            llangs = list(langs)
            for lang in llangs:
                if not isinstance(lang, dict):
                    raise type_error(lang, "item of llangs", Dict)
                lang_id = enforce_non_empty_str_without_ws(
                    lang[bc.META_LANG_ID])
                if lang_id in done:
                    raise ValueError(f"Duplicate language id '{lang_id}'.")
                done.add(lang_id)
                lang_name = enforce_non_empty_str(enforce_non_empty_str(
                    lang[bc.META_LANG_NAME]).strip())
                self.__build_one_lang(lang_id, lang_name, len(llangs) > 1)
                no_lang = False

        if no_lang:
            self.__build_one_lang(
                self.__get_meta_no_error(bc.META_LANG), None, False)
        logger("finished the build loop for all languages.")

    def __build_website(self) -> None:
        """Build the website, if any."""
        template = self.__get_meta_no_error(bc.META_WEBSITE_OUTER)
        if template:
            logger(f"found website template spec '{template}'.")
            template = self.input_dir.resolve_inside(template)
            body = self.__get_meta_no_error(bc.META_WEBSITE_BODY)
            if body:
                logger(f"found website body spec '{body}'.")
                body = self.input_dir.resolve_inside(body)
            build_website(docs=self.__results,
                          outer_file=template,
                          body_file=body,
                          dest_dir=self.__output_dir,
                          input_dir=self.__input_dir,
                          get_meta=self.get_meta_str)

    def build(self) -> Tuple[LangResult, ...]:
        """
        Perform the build.

        :returns: the results
        """
        logger(f"starting the build process for input file "
               f"'{self.__input_file}', input dir '{self.__input_dir}', and "
               f"output dir '{self.__output_dir}' with the following tool "
               f"versions:\n{get_versions()}")
        self.__load_self_repo()
        self.__metadata_raw = load_initial_metadata(self.__input_file,
                                                    self.__input_dir)
        self.__load_repos_from_meta(self.__metadata_raw)
        self.__build_all_langs()
        self.__build_website()
        logger("build process completed, created "
               f"{sum(len(c.results) for c in self.__results)} "
               f"book files in total for {len(self.__results)} language(s).")
        res = tuple(self.__results)
        if (res is None) or (len(res) <= 0):
            raise ValueError("Did not build any results.")
        return res

    def __enter__(self) -> 'Build':
        """Nothing, just exists for `with`."""
        if not self.__is_open:
            raise ValueError("Build already closed.")
        logger(f"starting the build of '{self.__input_file}' "
               f"to '{self.__output_dir}'.")
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> bool:
        """
        Delete the temporary directory and everything in it.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it
        """
        opn = self.__is_open
        self.__is_open = False
        if opn:
            logger("cleaning up temporary files.")
            self.__exit.close()
            logger(f"finished the build of '{self.__input_file}' "
                   f"to '{self.__output_dir}'.")
        del exception_value
        del traceback
        return exception_type is None

    @staticmethod
    def run(input_file: str,
            output_dir: str,
            exit_on_error: bool = False) -> Tuple[LangResult, ...]:
        """
        Run a build on an input file to an output directory.

        :param input_file: the input file
        :param output_dir: the output directory
        :param exit_on_error: should we quit Python upon error?
        :return: a tuple of results
        """
        try:
            with Build(input_file, output_dir, True) as bd:
                res = bd.build()
            sys.stdout.flush()
            sys.stderr.flush()
        except BaseException as be:
            sys.stdout.flush()
            sys.stderr.flush()
            exinfo = "  ".join(tb.format_exception(type(be),
                                                   value=be,
                                                   tb=be.__traceback__))
            logger(f"The build process has FAILED with error '{be}':"
                   f"\n  {exinfo}")
            sys.stdout.flush()
            sys.stderr.flush()
            if exit_on_error:
                sys.exit(1)
            raise be if isinstance(be, ValueError) else ValueError(be)
        else:
            return res
