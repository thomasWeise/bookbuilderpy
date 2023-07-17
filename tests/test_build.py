"""Test the interaction with the build system."""
import os.path
import shutil
from typing import Final

from bookbuilderpy.build import Build
from bookbuilderpy.git import Repo
from bookbuilderpy.logger import logger
from bookbuilderpy.temp import Path, TempDir


def get_local_repo() -> Repo | None:
    """
    Get the local repository.

    :returns: the local repository, or None if none exists
    """
    logger("are we in a local repository?")
    check = Path.path(".")
    while True:
        if check == "/":
            break
        if not os.access(check, os.R_OK):
            break
        test = Path.path(os.path.join(check, ".git"))
        if os.path.isdir(test):
            repo = Repo.from_local(check)
            logger(f"build process is based on commit '{repo.commit}'"
                   f" of repo '{repo.url}'.")
            return repo
        check = Path.path(os.path.join(check, ".."))
    logger("build process is not based on git checkout.")
    return None


#: should we use git?
USE_GIT: bool = True

if "GITHUB_JOB" not in os.environ:
    __inner_repo: Final[Repo | None] = get_local_repo()
    if __inner_repo is None:
        logger("cannot patch repository loader")
        USE_GIT = False
    else:
        def __download(url: str, dest_dir: str,
                       rp: Repo = __inner_repo) -> Repo:
            dd = Path.directory(dest_dir)
            shutil.copytree(rp.path, dd, dirs_exist_ok=True)
            rr = Repo(dd, url, rp.commit, rp.date_time)
            logger("invoked patched repo downloader of "
                   f"{url} to {dest_dir}, returned {rr}.")
            return rr
        Repo.download = __download
        logger("repository loader patched")


def test_in_out_path() -> None:
    """Test the input/out path."""
    with TempDir.create() as src, TempDir.create() as dst:
        f = Path.path(os.path.join(src, "test.md"))
        f.write_all("\\relative.input{metadata.yaml}")
        f = Path.path(os.path.join(src, "metadata.yaml"))
        txt = ["---",
               "title: The Great Book of Many Things",
               "author: Thomas Weise"]
        if USE_GIT:
            txt.extend([
                "repos:",
                "  - id: bp",
                "    url: "
                "https://github.com/thomasWeise/bookbuilderpy.git",
                "  - id: mp",
                "    url: https://github.com/thomasWeise/moptipy.git"])
        txt.extend([
            "langs:",
            "  - id: en",
            "    name: English",
            "  - id: de",
            "    name: Deutsch (German)",
            "..."])

        f.write_all(txt)

        with Build(f, dst, False) as build:
            assert build.input_file is not None

            try:
                build.build()
            except ValueError as ve:
                if str(ve) != "Did not build any results.":
                    raise
            if USE_GIT:
                assert build.get_repo("bp").url == \
                    "https://github.com/thomasWeise/bookbuilderpy.git"
                assert build.get_repo("mp").url == \
                    "https://github.com/thomasWeise/moptipy.git"
