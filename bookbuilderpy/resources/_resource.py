"""The package for loading templates and resources."""
import os.path
from importlib import resources

from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.url import load_text_from_url


def load_resource(name: str, source_dir: str, dest_dir: str) -> Path:
    """
    Load a template for the use with pandoc.

    :param str name: the template name
    :param str source_dir: the source directory
    :param str dest_dir: the destination directory
    :return: the fully qualified path to the template file
    :rtype: Path
    """
    input_dir = Path.directory(source_dir)
    output_dir = Path.directory(dest_dir)
    input_dir.enforce_neither_contains(output_dir)

    if name.startswith("http://") or name.startswith("https://"):
        urlname, text = load_text_from_url(name)
        dest_file = output_dir.resolve_inside(urlname)
        dest_file.write_all(text)
        return dest_file

    if not ("//" in name):
        input_file = input_dir.resolve_inside(name)
        if os.path.isfile(input_file):
            return Path.copy_resource(input_dir, input_file, output_dir)

    pack = str(__package__)
    if resources.is_resource(package=pack, name=name):
        file = output_dir.resolve_inside(name)
        with resources.open_text(package=pack, resource=name) as stream:
            file.write_all(enforce_non_empty_str(stream.read()))
        return file

    raise ValueError(f"Could not find resource '{name}'.")
