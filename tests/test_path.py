"""Test the interaction with the file system."""

import os.path
from typing import cast

# noinspection PyPackageRequirements
import pytest

from bookbuilderpy.temp import Path, TempDir, TempFile


def test_path_1() -> None:
    """Test the Path class 1."""
    with TempDir.create() as src, TempDir.create() as dst:
        input_dir = src.resolve_inside("test/inner/tmp")
        input_dir.ensure_dir_exists()
        src.enforce_contains(input_dir)
        input_file_pure = input_dir.resolve_inside("test.txt")
        src.enforce_contains(input_file_pure)
        input_file_pure.write_all(["123", "456", "789"])

        input_file_en = input_dir.resolve_inside("test_en.txt")
        src.enforce_contains(input_file_en)
        input_file_en.write_all(["abc", "def", "ghi"])

        res = input_dir.resolve_input_file("test.txt", lang="en")
        out_en = Path.copy_resource(src, res, dst)
        assert os.path.basename(out_en) == "test_en.txt"
        assert out_en.read_all_list() == ["abc\n", "def\n", "ghi\n"]

        out_en = Path.copy_resource(
            src, input_dir.resolve_input_file("test.txt", lang="cn"),
            dst)
        assert os.path.basename(out_en) == "test.txt"
        assert out_en.read_all_str() == "123\n456\n789\n"


def test_path_creation() -> None:
    """Test that path creation failes with wrong time."""
    with pytest.raises(TypeError):
        Path.path(cast(str, 1))
    with pytest.raises(TypeError):
        Path.directory(cast(str, 1))
    with pytest.raises(TypeError):
        Path.file(cast(str, 1))
    with pytest.raises(ValueError):
        Path.path("")


def test_write_all_read_all_and_enforce_exists() -> None:
    """Test writing and reading text as well as enforcing existence."""
    with TempFile.create() as tf:
        with pytest.raises(ValueError):
            tf.write_all([])
        with pytest.raises(ValueError):
            tf.write_all("")
        with pytest.raises(ValueError):
            tf.write_all(" ")
        with pytest.raises(TypeError):
            tf.write_all(cast(str, 2))

        tf.write_all(" \nbla\n\n x \n99 x   y\n\n")
        assert tf.read_all_str() == "\nbla\n\n x\n99 x   y\n"
        assert tf.read_all_list() == [
            "\n", "bla\n", "\n", " x\n", "99 x   y\n"]

        tf.write_all([" ", "bla", "", " x ", "99 x   y", ""])
        assert tf.read_all_str() == "\nbla\n\n x\n99 x   y\n"
        assert tf.read_all_list() == [
            "\n", "bla\n", "\n", " x\n", "99 x   y\n"]

        tf.enforce_file()
        tf.ensure_file_exists()

        with pytest.raises(ValueError):
            tf.enforce_dir()
        with pytest.raises(ValueError):
            tf.ensure_dir_exists()


def test_enforce_exists() -> None:
    """Test writing and reading text as well as enforcing existence."""
    with TempFile.create() as tf:
        tf.enforce_file()
        tf.ensure_file_exists()

        with pytest.raises(ValueError):
            tf.enforce_dir()
        with pytest.raises(ValueError):
            tf.ensure_dir_exists()
    del tf

    with TempDir.create() as td:
        td.enforce_dir()
        td.ensure_dir_exists()

        with pytest.raises(ValueError):
            td.enforce_file()
        with pytest.raises(ValueError):
            td.ensure_file_exists()
        with pytest.raises(ValueError):
            td.write_all("test")
        with pytest.raises(ValueError):
            td.write_all(cast(str, 2))
        with pytest.raises(ValueError):
            td.write_all("")


def test_enforce_contains_and_empty_readall() -> None:
    """Test that enforce_contains works."""
    with TempDir.create() as td1:

        assert os.path.exists(td1)
        assert os.path.isdir(td1)
        td1.enforce_dir()
        td1.enforce_contains(td1)
        assert td1.contains(td1)
        s1 = td1.resolve_inside("a")
        assert td1.contains(s1)
        td1.enforce_contains(s1)
        with pytest.raises(ValueError):
            td1.resolve_inside("../b" if td1.endswith("a") else "../a")
        with pytest.raises(ValueError):
            td1.resolve_inside("")

        with TempFile.create() as tf1:
            assert os.path.exists(tf1)
            assert os.path.isfile(tf1)
            tf1.enforce_file()
            assert not td1.contains(tf1)
            with pytest.raises(ValueError):
                td1.enforce_contains(tf1)
            assert not tf1.contains(td1)
            with pytest.raises(ValueError):
                tf1.enforce_contains(td1)
            with pytest.raises(ValueError):
                tf1.read_all_str()
            with pytest.raises(ValueError):
                tf1.read_all_list()

        with TempFile.create(directory=td1) as tf2:
            assert os.path.exists(tf2)
            assert os.path.isfile(tf2)
            assert td1.contains(tf2)
            td1.enforce_contains(tf2)
            assert not tf2.contains(td1)
            with pytest.raises(ValueError):
                tf2.enforce_contains(td1)

        with TempDir.create(directory=td1) as td2:
            assert os.path.exists(td2)
            assert os.path.isdir(td2)
            assert td1.contains(td2)
            td1.enforce_contains(td2)
            assert not td2.contains(td1)
            with pytest.raises(ValueError):
                td2.enforce_contains(td1)
            with TempFile.create(directory=td2) as tf3:
                assert os.path.exists(tf3)
                assert os.path.isfile(tf3)
                assert td1.contains(tf3)
                td1.enforce_contains(tf3)
                assert not tf3.contains(td1)
                with pytest.raises(ValueError):
                    tf3.enforce_contains(td1)
                assert td2.contains(tf3)
                td2.enforce_contains(tf3)
                assert not tf3.contains(td2)
                with pytest.raises(ValueError):
                    tf3.enforce_contains(td2)
