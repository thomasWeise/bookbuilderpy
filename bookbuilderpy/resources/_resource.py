"""The package for loading text templates and resources."""
import os.path
from importlib import resources  # nosem
from typing import Optional
from bookbuilderpy.path import Path, copy_pure
from bookbuilderpy.strings import enforce_non_empty_str, \
    enforce_non_empty_str_without_ws


def load_resource(name: str, source_dir: str, dest_dir: str) -> \
        Optional[Path]:
    """
    Load a text resource or template for the use with pandoc.

    :param name: the template name
    :param source_dir: the source directory
    :param dest_dir: the destination directory
    :return: the fully qualified path to the resource file if it was created,
        or None if no new file was created
    """
    input_dir = Path.directory(source_dir)
    output_dir = Path.directory(dest_dir)
    input_dir.enforce_neither_contains(output_dir)
    name = enforce_non_empty_str_without_ws(name)

    if name.startswith("http://") or \
            name.startswith("https://") or \
            ("//" in name):
        return None

    output_file = output_dir.resolve_inside(name)
    if os.path.exists(output_file):
        output_file.enforce_file()
        return None

    Path.directory(os.path.dirname(output_file)).ensure_dir_exists()
    input_file = input_dir.resolve_inside(name)
    if os.path.isfile(input_file):
        return copy_pure(input_file, output_file)

    pack = str(__package__)
    if resources.is_resource(package=pack, name=name):
        with resources.open_text(package=pack, resource=name) as stream:
            output_file.write_all(enforce_non_empty_str(stream.read()))
        return output_file

    return None
