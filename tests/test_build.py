"""Test the interaction with the file system."""
import datetime
import os.path

from bookbuilderpy.build import Build
from bookbuilderpy.temp import TempDir, Path


# noinspection PyPackageRequirements

def test_in_out_path():
    with TempDir.create() as src:
        with TempDir.create() as dst:
            f = Path.path(os.path.join(src, "test.md"))
            f.write_all(["bla"])

            with Build(f, dst) as build:
                assert build.start <= datetime.datetime.now(
                    datetime.timezone.utc)
