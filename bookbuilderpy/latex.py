"""A routine for invoking LaTeX via pandoc."""

from typing import Optional, Callable

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File
from bookbuilderpy.pandoc import pandoc
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws


def latex(source_file: str,
          dest_file: str,
          lang: Optional[str] = None,
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
    Invoke pandoc.

    :param str source_file: the source file
    :param str dest_file: the destination file
    :param Optional[str] lang: a language id code
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
    input_file = Path.file(source_file)

    args = list()
    if lang is not None:
        if (lang == "zh") or (lang.startswith("zh-")):
            args.append("--pdf-engine=xelatex")
    top_level_division = enforce_non_empty_str_without_ws(top_level_division)
    args.append(f"--top-level-division={top_level_division}")
    if use_listings:
        args.append("--listings")

    return pandoc(source_file=input_file,
                  dest_file=dest_file,
                  format_in=bc.PANDOC_FORMAT_MARKDOWN,
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
                  resolve_resources=resolve_resources,
                  args=args)
