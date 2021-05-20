"""Test the interaction with the file system."""

from bookbuilderpy.git import Repo
from bookbuilderpy.temp import TempDir


# noinspection PyPackageRequirements

def test_load_git_repo():
    with TempDir.create() as dst:
        repo = "https://github.com/thomasWeise/bookbuilderpy.git"
        ret = Repo.load(repo, dst)
        assert isinstance(ret, Repo)
        assert len(ret.commit) == 40
        assert len(ret.date_time) > 0
        assert ret.path == dst
        assert ret.url == repo
