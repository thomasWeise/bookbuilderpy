"""A routine for invoking pandoc."""

import os.path
import re
import subprocess  # nosec
from shutil import which
from typing import Optional, Final, List, Callable

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File
from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.resources import ResourceServer
from bookbuilderpy.strings import enforce_non_empty_str, \
    enforce_non_empty_str_without_ws

#: The pandoc executable.
__PANDOC_EXEC: Final[Optional[Path]] = [None if (t is None) else Path.file(t)
                                        for t in [which("pandoc")]][0]


def has_pandoc() -> bool:
    """
    Check if pandoc is installed.

    :return: True if pandoc is installed, False otherwise.
    :rtype: bool
    """
    return __PANDOC_EXEC is not None


def pandoc(source_file: str,
           dest_file: str,
           format_in: str = bc.PANDOC_FORMAT_MARKDOWN,
           format_out: str = bc.PANDOC_FORMAT_LATEX,
           locale: Optional[str] = None,
           standalone: bool = True,
           tabstops: Optional[int] = 2,
           toc_print: bool = True,
           toc_depth: int = 3,
           crossref: bool = True,
           bibliography: bool = True,
           template: Optional[str] = None,
           csl: Optional[str] = None,
           number_sections: bool = True,
           args: Optional[List[str]] = None,
           resolve_resources: Callable = lambda x: None) -> File:
    """
    Invoke pandoc.

    :param str source_file: the source file
    :param str dest_file: the destination file
    :param str format_in: the input format
    :param str format_out: the output format
    :param bool standalone: should we produce a stand-alone document?
    :param Optional[int] tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param bool toc_print: should we print the table of contents
    :param bool toc_depth: the depth of the table of contents
    :param bool crossref: should we use crossref
    :param bool bibliography: should we use a bibliography
    :param Optional[str] template: which template should we use, if any?
    :param Optional[str] csl: which csl file should we use, if any?
    :param bool number_sections: should sections be numbered?
    :param Optional[str] locale: the language to be used for compiling
    :param args: any additional arguments
    :param Callable resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    :rtype: File
    """
    if __PANDOC_EXEC is None:
        raise ValueError("Pandoc is not installed.")

    output_file = Path.path(dest_file)
    if os.path.exists(output_file):
        raise ValueError(f"Output file '{output_file}' already exists.")
    input_file = Path.file(source_file)
    if input_file == output_file:
        raise ValueError(
            f"Input '{input_file}' must differ from output '{output_file}'.")
    output_dir = Path.path(os.path.dirname(output_file))
    output_dir.ensure_dir_exists()
    input_dir = Path.directory(os.path.dirname(input_file))

    log(f"Applying pandoc to generate output file '{output_file}' "
        f"from '{input_file}'.")

    format_in = enforce_non_empty_str_without_ws(format_in)
    format_out = enforce_non_empty_str_without_ws(format_out)

    if format_in.startswith("markdown"):
        format_in = "+".join([format_in,
                              "definition_lists",
                              "smart",
                              "fenced_code_blocks",
                              "fenced_code_attributes",
                              "line_blocks",
                              "inline_code_attributes",
                              "latex_macros",
                              "implicit_figures",
                              "pipe_tables",
                              "raw_attribute"])
    cmd: Final[List[str]] = [__PANDOC_EXEC,
                             f"--from={format_in}",
                             f"--write={format_out}",
                             f"--output={output_file}",
                             "--fail-if-warnings",
                             "--strip-comments"]

    if tabstops is not None:
        if tabstops <= 0:
            raise ValueError(f"tabstops cannot be {tabstops}.")
        cmd.append(f"--tab-stop={tabstops}")

    if standalone:
        cmd.append("--standalone")

    if number_sections:
        cmd.append("--number-sections")

    if toc_print:
        cmd.append("--table-of-contents")
        if toc_depth is not None:
            if toc_depth <= 0:
                raise ValueError(f"toc_depth cannot be {toc_depth}.")
            cmd.append(f"--toc-depth={toc_depth}")

    template_file: Optional[Path] = None
    if template is not None:
        template = enforce_non_empty_str_without_ws(template)
        template_file = resolve_resources(template, input_dir)
        if template_file is not None:
            template_file.enforce_file()
            template = template_file
        cmd.append(f"--template={template}")

    if crossref:
        cmd.append("--filter=pandoc-crossref")

    csl_file: Optional[Path] = None
    if bibliography:
        cmd.append("--citeproc")
        if csl is not None:
            csl = enforce_non_empty_str_without_ws(csl)
            csl_file = resolve_resources(csl, input_dir)
            if csl_file is not None:
                csl_file.enforce_file()
                csl = csl_file
            cmd.append(f"--csl={csl}")

    if args is not None:
        cmd.extend([enforce_non_empty_str(a).strip()
                    for a in args])
    cmd.append(input_file)

    if locale is not None:
        locale = enforce_non_empty_str_without_ws(locale)
        cmd.append(f"-V lang={locale.replace('_', '-')}")

    ret = subprocess.run(cmd, check=True, text=True, timeout=600,  # nosec
                         cwd=input_dir)  # nosec
    if ret.returncode != 0:
        raise ValueError(
            f"Error when executing pandoc command '{cmd}'.")

    if template_file:
        os.remove(template_file)
    if csl_file:
        os.remove(csl_file)

    res = File(output_file)

    log(f"Finished applying pandoc call '{cmd}', got output file "
        f"'{res.path}' of size '{res.size}'.")
    return res


def latex(source_file: str,
          dest_file: str,
          format_in: str = bc.PANDOC_FORMAT_MARKDOWN,
          locale: Optional[str] = None,
          standalone: bool = True,
          tabstops: Optional[int] = 2,
          toc_print: bool = True,
          toc_depth: int = 3,
          crossref: bool = True,
          bibliography: bool = True,
          number_sections: bool = True,
          top_level_division: str = "chapter",
          use_listings: bool = False,
          get_meta: Callable = lambda x: None,
          resolve_resources: Callable = lambda x: None) -> File:
    """
    Invoke pandoc to build LaTeX and then PDF output.

    :param str source_file: the source file
    :param str dest_file: the destination file
    :param str format_in: the input format
    :param Optional[str] locale: the language to be used for compiling
    :param bool standalone: should we produce a stand-alone document?
    :param Optional[int] tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param bool toc_print: should we print the table of contents
    :param bool toc_depth: the depth of the table of contents
    :param bool crossref: should we use crossref
    :param bool bibliography: should we use a bibliography
    :param bool number_sections: should sections be numbered?
    :param str top_level_division: the top-level division
    :param bool use_listings: should the listings package be used?
    :param Callable get_meta: a function to access meta-data
    :param Callable resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    :rtype: File
    """
    args = list()
    if locale is not None:
        locale = enforce_non_empty_str_without_ws(locale)
        if (locale == "zh") or (locale.startswith("zh-")) or \
                (locale.startswith("zh_")):
            args.append("--pdf-engine=xelatex")
    top_level_division = enforce_non_empty_str_without_ws(top_level_division)
    args.append(f"--top-level-division={top_level_division}")
    if use_listings:
        args.append("--listings")

    return pandoc(source_file=source_file,
                  dest_file=dest_file,
                  format_in=format_in,
                  format_out=bc.PANDOC_FORMAT_LATEX,
                  standalone=standalone,
                  tabstops=tabstops,
                  toc_print=toc_print,
                  toc_depth=toc_depth,
                  crossref=crossref,
                  bibliography=bibliography,
                  template=get_meta(bc.PANDOC_TEMPLATE_LATEX),
                  csl=get_meta(bc.PANDOC_CSL),
                  number_sections=number_sections,
                  locale=locale,
                  resolve_resources=resolve_resources,
                  args=args)


def html(source_file: str,
         dest_file: str,
         format_in: str = bc.PANDOC_FORMAT_MARKDOWN,
         locale: Optional[str] = None,
         standalone: bool = True,
         tabstops: Optional[int] = 2,
         toc_print: bool = True,
         toc_depth: int = 3,
         crossref: bool = True,
         bibliography: bool = True,
         number_sections: bool = True,
         get_meta: Callable = lambda x: None,
         resolve_resources: Callable = lambda x: None) -> File:
    """
    Invoke pandoc to build HTML output.

    :param str source_file: the source file
    :param str dest_file: the destination file
    :param str format_in: the input format
    :param Optional[str] locale: the language to be used for compiling
    :param bool standalone: should we produce a stand-alone document?
    :param Optional[int] tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param bool toc_print: should we print the table of contents
    :param bool toc_depth: the depth of the table of contents
    :param bool crossref: should we use crossref
    :param bool bibliography: should we use a bibliography
    :param bool number_sections: should sections be numbered?
    :param Callable get_meta: a function to access meta-data
    :param Callable resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    :rtype: File
    """
    f: File
    with ResourceServer() as serv:
        f = pandoc(source_file=source_file,
                   dest_file=dest_file,
                   format_in=format_in,
                   format_out=bc.PANDOC_FORMAT_HTML5,
                   locale=locale,
                   standalone=standalone,
                   tabstops=tabstops,
                   toc_print=toc_print,
                   toc_depth=toc_depth,
                   crossref=crossref,
                   bibliography=bibliography,
                   template=get_meta(bc.PANDOC_TEMPLATE_HTML5),
                   csl=get_meta(bc.PANDOC_CSL),
                   number_sections=number_sections,
                   resolve_resources=resolve_resources,
                   args=[f"--katex={serv.get_katex_server()}",
                         "--ascii", "--html-q-tags",
                         "--self-contained"])
    if not bibliography:
        return f

    # For some reason, the id and the text of each bibliography
    # item are each put into separate divs of classes for which
    # no styles are given. Therefore, we convert these divs to
    # spans and add some vertical spacing.
    text = enforce_non_empty_str(f.path.read_all_str().strip())
    end = text.rfind("<div id=\"refs\"")
    if end <= 0:
        return f
    text_1 = text[:end]
    text_2 = text[end:]
    del text

    text_2 = re.sub('<div class="csl-left-margin">(.*?)</div>',
                    '<span class="csl-left-margin">\\1</span>',
                    text_2, re.MULTILINE)
    text_2 = re.sub('<div class="csl-right-inline">(.*?)</div>',
                    '<span class="csl-right-inline">\\1</span>',
                    text_2, re.MULTILINE)
    text_2 = text_2.replace(
        ' class="csl-entry" role="doc-biblioentry">',
        ' class="csl-entry" role="doc-biblioentry" style="margin-top:0.33em">')

    f.path.write_all([text_1, text_2])
    return File(f.path)


def epub(source_file: str,
         dest_file: str,
         format_in: str = bc.PANDOC_FORMAT_MARKDOWN,
         locale: Optional[str] = None,
         standalone: bool = True,
         tabstops: Optional[int] = 2,
         toc_print: bool = True,
         toc_depth: int = 3,
         crossref: bool = True,
         bibliography: bool = True,
         number_sections: bool = True,
         get_meta: Callable = lambda x: None,
         resolve_resources: Callable = lambda x: None) -> File:
    """
    Invoke pandoc to build epub output.

    :param str source_file: the source file
    :param str dest_file: the destination file
    :param str format_in: the input format
    :param Optional[str] locale: the language to be used for compiling
    :param bool standalone: should we produce a stand-alone document?
    :param Optional[int] tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param bool toc_print: should we print the table of contents
    :param bool toc_depth: the depth of the table of contents
    :param bool crossref: should we use crossref
    :param bool bibliography: should we use a bibliography
    :param bool number_sections: should sections be numbered?
    :param Callable get_meta: a function to access meta-data
    :param Callable resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    :rtype: File
    """
    return pandoc(source_file=source_file,
                  dest_file=dest_file,
                  format_in=format_in,
                  format_out=bc.PANDOC_FORMAT_EPUB,
                  locale=locale,
                  standalone=standalone,
                  tabstops=tabstops,
                  toc_print=toc_print,
                  toc_depth=toc_depth,
                  crossref=crossref,
                  bibliography=bibliography,
                  template=get_meta(bc.PANDOC_TEMPLATE_EPUB),
                  csl=get_meta(bc.PANDOC_CSL),
                  number_sections=number_sections,
                  resolve_resources=resolve_resources,
                  args=["--mathml", "--ascii", "--html-q-tags",
                        "--self-contained"])


def azw3(epub_file: str) -> File:
    """
    Convert an epub book into an azw3 one.

    :param str epub_file: the epub file
    :return: the azw3 file
    :rtype: File
    """
    input_file = Path.file(epub_file)
    input_dir = Path.directory(os.path.dirname(input_file))
    filename, _ = Path.split_prefix_suffix(os.path.basename(input_file))
    dest_file = Path.resolve_inside(input_dir, f"{filename}.azw3")
    cmd = ["ebook-convert", input_file, dest_file, "--embed-all-fonts"]
    ret = subprocess.run(cmd, check=True, text=True, timeout=360,  # nosec
                         cwd=input_dir)  # nosec
    if ret.returncode != 0:
        raise ValueError(
            f"Error when executing calibre command '{cmd}'.")

    return File(dest_file)
