"""This script is there to generate the resources."""
from os.path import dirname
from typing import Final, List

from bookbuilderpy.git import Repo
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.temp import TempDir
from bookbuilderpy.url import load_text_from_url


def load_html_github_template(dest: Path) -> Path:
    """
    Load the HTML 5 template with GitHub look and feel.

    :param dest: the destination directory
    :return: the full path of the template
    """
    logger(f"now loading html github template to '{dest}'.")
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

        # remove the useless alert styles
        remove_start = ".Alert,"
        idx_1 = text.find(remove_start)
        if idx_1 > 0:
            remove_end = ".Warning h6:"
            idx_2 = text.find(remove_end, idx_1)
            if idx_2 > idx_1:
                idx_3 = text.find("}", idx_2)
                if idx_3 > idx_2:
                    text = text[:idx_1].strip() + text[(idx_3 + 1):].strip()

        text = text.replace(',"Apple Color Emoji"', "")
        text = text.replace(',"Segoe UI Emoji"', "")
        text = text.replace(',"Segoe UI Symbol"', "")
        text = text.replace('div.line-block{line-height:0.85;',
                            'div.line-block{')
        start1 = text.find(".markdown-body p,")
        if start1 > 0:
            start2 = text.find("{", start1)
            if start2 > start1:
                end1 = text.find("}", start1)
                if end1 > start2:
                    replacer = "margin-top:0;"
                    found = text.find(replacer, start2)
                    if start2 < found < end1:
                        text = f"{text[:found]}margin-top:16px;" \
                               f"{text[found+len(replacer):]}"

        dst_file = dest.resolve_inside(name)
        dst_file.write_all(text)
        Path.copy_file(repo.path.resolve_inside("LICENSE"),
                       dest.resolve_inside(f"{name}_license"))
        if name != dst_file.relative_to(dest):
            raise ValueError(f"'{name}' should "
                             f"be '{dst_file.relative_to(dest)}'.")
        logger(f"succeeded in loading html github template to '{dst_file}'.")
        return dst_file


def load_latex_eisvogel_template(dest: Path) -> Path:
    """
    Load the LaTeX eisvogel template.

    :param dest: the destination directory
    :return: the full path of the template
    """
    logger(f"now loading latex eisvogel template to '{dest}'.")
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
        logger(
            f"succeeded in loading latex eisvogel template to '{dst_file}'.")
        return dst_file


def load_csl_template(dest: Path) -> List[Path]:
    """
    Load the CSL templates template.

    :param dest: the destination directory
    :return: the full path of the template
    """
    logger(f"now csl template(s) to '{dest}'.")
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
        logger(f"finished loading '{url}' to file '{dst_file}'.")
        paths.append(dst_file)
    return paths


def load_mathjax(dest: Path) -> Path:
    """
    Download a full the math jax installation for svg conversion.

    For the HTML build, we want to convert all the equations to SVGs,
    because they will look the same regardless on which device the
    books are displayed. This also allows us to purge the javascripts
    after the conversion.

    :param dest: the destination
    :return: the paths to the downloaded resources
    """
    logger(f"now loading mathjax svg to '{dest}'.")
    name = "mathjax.js"
    url = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg-full.js"
    _, data = load_text_from_url(url)
    data = enforce_non_empty_str(data.strip())
    dst_file = dest.resolve_inside(name)
    dst_file.write_all(data)

    name = f"{name}_license"
    url = "https://raw.githubusercontent.com/mathjax/MathJax/master/LICENSE"
    _, data = load_text_from_url(url)
    data = enforce_non_empty_str(data.strip())
    dst_file = dest.resolve_inside(name)
    dst_file.write_all(data)

    logger(f"finished loading mathjax svg to file '{dst_file}'.")
    return dst_file


if __name__ == "__main__":
    logger("begin loading resources.")
    current_dir = Path.directory(dirname(__file__))
    logger(f"current dir is '{current_dir}'.")
    load_mathjax(current_dir)
    load_html_github_template(current_dir)
    load_csl_template(current_dir)
    load_latex_eisvogel_template(current_dir)
    logger("done loading resources.")
