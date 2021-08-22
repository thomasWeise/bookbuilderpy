"""This script is there to generate the resources."""
from os.path import dirname
from typing import Final, List

from bookbuilderpy.git import Repo
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.temp import TempDir
from bookbuilderpy.url import load_text_from_url, load_binary_from_url


def load_html_github_template(dest: Path) -> Path:
    """
    Load the HTML 5 template with GitHub look and feel.

    :param Path dest: the destination directory
    :return: the full path of the template
    :rtype: Path
    """
    with TempDir.create() as temp:
        name = "GitHub.html5"
        repo = Repo.download("https://github.com/tajmone/pandoc-goodies/",
                             temp)
        src_file = repo.path.resolve_inside(f"templates/html5/github/{name}")
        src_file.enforce_file()
        text = enforce_non_empty_str(src_file.read_all_str())
        text = text.replace(
            "div.line-block{white-space:pre-line}",
            "div.line-block{line-height:0.85;white-space:pre-line}")
        dst_file = dest.resolve_inside(name)
        dst_file.write_all(text)
        Path.copy_file(repo.path.resolve_inside("LICENSE"),
                       dest.resolve_inside(f"{name}_license"))
        if name != dst_file.relative_to(dest):
            raise ValueError(f"'{name}' should "
                             f"be '{dst_file.relative_to(dest)}'.")
        return dst_file


def load_latex_eisvogel_template(dest: Path) -> Path:
    """
    Load the LaTeX eisvogel template.

    :param Path dest: the destination directory
    :return: the full path of the template
    :rtype: Path
    """
    with TempDir.create() as temp:
        name = "eisvogel.tex"
        repo = Repo.download(
            "https://github.com/Wandmalfarbe/pandoc-latex-template",
            temp)
        src_file = repo.path.resolve_inside(f"{name}")
        src_file.enforce_file()
        text = enforce_non_empty_str(src_file.read_all_str())
        text = text.replace("scrartcl", "scrbook")
        dst_file = dest.resolve_inside(name)
        dst_file.write_all(text)
        Path.copy_file(repo.path.resolve_inside("LICENSE"),
                       dest.resolve_inside(f"{name}_license"))
        if name != dst_file.relative_to(dest):
            raise ValueError(f"'{name}' should "
                             f"be '{dst_file.relative_to(dest)}'.")
        return dst_file


def load_csl_template(dest: Path) -> List[Path]:
    """
    Load the CSL templates template.

    :param Path dest: the destination directory
    :return: the full path of the template
    :rtype: List[Path]
    """
    paths: Final[List[Path]] = []

    for name in ["association-for-computing-machinery"]:
        url = f"https://www.zotero.org/styles/{name}"
        urlname, text = load_text_from_url(url)
        usename = f"{name}.csl"
        if urlname != usename:
            raise ValueError(f"Name conflict: '{urlname}' vs. '{usename}'.")
        dst_file = dest.resolve_inside(usename)
        dst_file.write_all(text)
        if name != Path.split_prefix_suffix(dst_file.relative_to(dest))[0]:
            raise ValueError(f"'{name}' should "
                             f"be '{dst_file.relative_to(dest)}'.")
        paths.append(dst_file)
    return paths


def load_katex(dest: Path) -> Path:
    """
    Download a full katex installation with all required resources.

    :param Path dest: the destination
    :return: the paths to the downloaded resources
    :rtype: Path
    """
    name = "katex.zip"
    url = "https://github.com/KaTeX/KaTeX/releases/download/" \
          "v0.13.13/katex.zip"
    _, data = load_binary_from_url(url)
    dst_file = dest.resolve_inside(name)
    with open(dst_file, "wb") as fd:
        fd.write(data)

    return dst_file


if __name__ == "__main__":
    current_dir = Path.directory(dirname(__file__))
    load_katex(current_dir)
    load_html_github_template(current_dir)
    load_csl_template(current_dir)
    load_latex_eisvogel_template(current_dir)
