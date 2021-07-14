"""Test the interaction with the build system with random data."""
import os
import os.path
from typing import Final, Tuple, List, Optional

from bookbuilderpy.temp import Path

#: The moptipy repository
MOPTIPY_REPO: Final[str] = "mp"


def create_metadata(dest: Path) -> Path:
    """
    Create the metadata of the build.

    :param Path dest: the directory
    :return: the path to the metadata file
    :rtype: Path
    """
    f: Final[Path] = dest.resolve_inside("metadata.yaml")
    txt = [
        "---",
        "repos:",
        f"  - id: {MOPTIPY_REPO}",
        "    url: https://github.com/thomasWeise/moptipy.git",
        "langs:",
        "  - id: en",
        "    name: English",
        "  - id: de",
        "    name: Deutsch (German)",
        "..."]
    f.write_all(txt)
    f.enforce_file()
    dest.enforce_contains(f)
    return f


def find_local_files() -> Tuple[Path, ...]:
    """
    Find proper files that can be used as external references.
    :return: the list of paths
    :rtype: Tuple[Path, ...]
    """
    tests = Path.file(__file__)
    package: Final[Path] = Path.directory(os.path.dirname(os.path.dirname(
        tests))).resolve_inside("bookbuilderpy")
    package.enforce_dir()
    result: List[Path] = list()
    for file in os.listdir(package):
        if file.endswith(".py") and not file.startswith("_"):
            full = os.path.join(package, file)
            if os.path.isfile(full):
                result.append(Path.file(full))
    assert len(result) > 0
    return tuple(result)


#: The possible code files to include
POSSIBLE_FILES: Tuple[Tuple[Optional[str], Tuple[str, ...]], ...] = (
    (None, find_local_files()),
    (MOPTIPY_REPO, (
        "moptipy/algorithms/ea1p1.py",
        "moptipy/algorithms/hillclimber.py"
        "moptipy/algorithms/random_sampling.py"
        "moptipy/algorithms/random_walk.py"
        "moptipy/algorithms/single_random_sample.py"
    ))
)


def test_build():
    assert len(POSSIBLE_FILES) > 0
