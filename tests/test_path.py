"""Test the interaction with the file system."""

import os.path

from bookbuilderpy.temp import TempDir, Path


# noinspection PyPackageRequirements

def test_in_out_path():
    with TempDir.create() as src:
        with TempDir.create() as dst:
            input_dir = src.resolve_inside("test/inner/tmp")
            input_dir.ensure_dir_exists()
            src.enforce_contains(input_dir)
            input_file_pure = input_dir.resolve_inside("test.txt")
            src.enforce_contains(input_file_pure)
            input_file_pure.write_all(["123", "456", "789"])

            input_file_en = input_dir.resolve_inside("test_en.txt")
            src.enforce_contains(input_file_en)
            input_file_en.write_all(["abc", "def", "ghi"])

            res = input_dir.resolve_input_file("test.txt")
            out_en = Path.copy_resource(src, res, dst)
            assert os.path.basename(out_en) == "test_en.txt"
            assert out_en.read_all() == ["abc\n", "def\n", "ghi\n"]

            out_en = Path.copy_resource(
                src, input_dir.resolve_input_file("test.txt", lang="cn"),
                dst)
            assert os.path.basename(out_en) == "test.txt"
            assert out_en.read_all() == ["123\n", "456\n", "789\n"]
