"""Test the temporary directories."""
from os.path import basename, dirname, exists, isdir, isfile, sep

from bookbuilderpy.temp import TempDir, TempFile


def test_temp_file() -> None:
    """Test temp files."""
    with TempFile.create() as tmp:
        assert isinstance(tmp, str)
        assert len(tmp) > 0
        assert isfile(tmp)
        assert exists(tmp)
    assert not isfile(tmp)
    assert not exists(tmp)

    with TempFile.create(prefix="aaaa", suffix=".xxx") as tmp:
        assert isinstance(tmp, str)
        assert len(tmp) > 0
        assert isfile(tmp)
        assert exists(tmp)
        bn = basename(tmp)
        assert bn.startswith("aaaa")
        assert bn.endswith(".xxx")
    assert not isfile(tmp)
    assert not exists(tmp)


def test_temp_dir() -> None:
    """Test temp directories."""
    with TempDir.create() as tmp:
        assert isinstance(tmp, str)
        assert len(tmp) > 0
        assert isdir(tmp)
        assert exists(tmp)
    assert not isdir(tmp)
    assert not exists(tmp)

    with TempDir.create() as path:
        assert isinstance(path, str)
        assert len(path) > 0
        assert isdir(path)
        assert exists(path)
        with TempFile.create(path) as path2:
            assert isinstance(path2, str)
            assert dirname(path2) == path
            assert len(path2) > 0
            assert isfile(path2)
            assert exists(path2)
        with TempFile.create(path) as path2:
            assert isinstance(path2, str)
            assert dirname(path2) == path
            assert len(path2) > 0
            assert isfile(path2)
            assert exists(path2)
        inner = (path + sep + "xx.y")
        with open(inner, "w"):
            pass
        assert isfile(inner)
        assert exists(inner)
    assert not isdir(path)
    assert not exists(path)
    assert not exists(path2)
    assert not exists(inner)
