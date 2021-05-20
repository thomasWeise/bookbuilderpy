"""Test the interaction with the file system."""

from bookbuilderpy.git import load_repo
from bookbuilderpy.temp import TempDir


# noinspection PyPackageRequirements

def test_load_git_repo():
    with TempDir.create() as dst:
        repo = "https://github.com/thomasWeise/bookbuilderpy.git"
        ret = load_repo(repo, dst)
        assert isinstance(ret, tuple)
        assert len(ret) == 4
        assert ret[0] == dst
        assert ret[1] == repo
        assert len(ret[2]) == 40
        assert len(ret[3]) > 0
