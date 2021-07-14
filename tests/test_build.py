"""Test the interaction with the build system."""
import os.path
from os import environ

from bookbuilderpy.build import Build
from bookbuilderpy.temp import TempDir, Path


# noinspection PyPackageRequirements

def test_in_out_path():
    with TempDir.create() as src:
        with TempDir.create() as dst:
            f = Path.path(os.path.join(src, "test.md"))
            f.write_all("\\relative.input{metadata.yaml}")
            f = Path.path(os.path.join(src, "metadata.yaml"))
            txt = [
                "---",
            ]
            has_github = "GITHUB_JOB" in environ
            if has_github:
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

            with Build(f, dst) as build:
                assert build.input_file is not None

                build.build()
                if has_github:
                    assert build.get_repo("bp").url == \
                           "https://github.com/thomasWeise/bookbuilderpy.git"
                    assert build.get_repo("mp").url == \
                           "https://github.com/thomasWeise/moptipy.git"
