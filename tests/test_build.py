"""Test the interaction with the file system."""
import os.path

from bookbuilderpy.build import Build
from bookbuilderpy.temp import TempDir, Path
from os import environ

# noinspection PyPackageRequirements

def test_in_out_path():
    lt = "GITHUB_JOB" in environ
    with TempDir.create() as src:
        with TempDir.create() as dst:
            f = Path.path(os.path.join(src, "test.md"))
            f.write_all("\\relative.input{metadata.yaml}")
            f = Path.path(os.path.join(src, "metadata.yaml"))
            f.write_all([
                "---",
                "repos:",
                "  - id: bp",
                "    url: https://github.com/thomasWeise/bookbuilderpy.git",
                "  - id: mp" if lt else "",
                "    url: https://github.com/thomasWeise/moptipy.git"
                if lt else "",
                "..."])

            with Build(f, dst) as build:
                assert build.input_file is not None

                build.build()
                assert build.get_repo("bp").url == \
                       "https://github.com/thomasWeise/bookbuilderpy.git"
                if lt:
                    assert build.get_repo("mp").url == \
                           "https://github.com/thomasWeise/moptipy.git"
