"""A routine for invoking pandoc."""

import os.path
from typing import Optional, Final, List, Callable, Dict

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File
from bookbuilderpy.html import html_postprocess
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.pdf import pdf_postprocess
from bookbuilderpy.resources import ResourceServer
from bookbuilderpy.shell import shell
from bookbuilderpy.strings import enforce_non_empty_str, \
    enforce_non_empty_str_without_ws, regex_sub
from bookbuilderpy.temp import TempFile
from bookbuilderpy.versions import TOOL_PANDOC, has_tool


#: The meanings of the pandoc exit codes.
__EXIT_CODES: Dict[int, str] = {
    3: "PandocFailOnWarningError",
    4: "PandocAppError",
    5: "PandocTemplateError",
    6: "PandocOptionError",
    21: "PandocUnknownReaderError",
    22: "PandocUnknownWriterError",
    23: "PandocUnsupportedExtensionError",
    24: "PandocCiteprocError",
    31: "PandocEpubSubdirectoryError",
    43: "PandocPDFError",
    44: "PandocXMLError",
    47: "PandocPDFProgramNotFoundError",
    61: "PandocHttpError",
    62: "PandocShouldNeverHappenError",
    63: "PandocSomeError",
    64: "PandocParseError",
    65: "PandocParsecError",
    66: "PandocMakePDFError",
    67: "PandocSyntaxMapError",
    83: "PandocFilterError",
    91: "PandocMacroLoop",
    92: "PandocUTF8DecodingError",
    93: "PandocIpynbDecodingError",
    94: "PandocUnsupportedCharsetError",
    97: "PandocCouldNotFindDataFileError",
    99: "PandocResourceNotFound"
}


def __pandoc_check_stderr(stderr: str) -> Optional[BaseException]:
    """
    Check the standard error output of pandoc.

    :param stderr: the standard error string
    """
    if stderr is None:
        return None
    if "Undefined cross-reference" in stderr:
        return ValueError("Undefined cross-reference!")
    if "[WARNING] Citeproc" in stderr:
        return ValueError("Undefined citation!")
    return None


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
           resolve_resources: Callable = lambda x: None,
           overwrite: bool = False) -> File:
    """
    Invoke pandoc.

    :param source_file: the source file
    :param dest_file: the destination file
    :param format_in: the input format
    :param format_out: the output format
    :param standalone: should we produce a stand-alone document?
    :param tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param toc_print: should we print the table of contents
    :param toc_depth: the depth of the table of contents
    :param crossref: should we use crossref
    :param bibliography: should we use a bibliography
    :param template: which template should we use, if any?
    :param csl: which csl file should we use, if any?
    :param number_sections: should sections be numbered?
    :param locale: the language to be used for compiling
    :param args: any additional arguments
    :param resolve_resources: a function to resolve resources
    :param overwrite: should the output file be overwritten if it exists?
    :return: the Path to the generated output file and it size
    """
    if not has_tool(TOOL_PANDOC):
        raise ValueError("Pandoc is not installed.")

    output_file = Path.path(dest_file)
    if (not overwrite) and os.path.exists(output_file):
        raise ValueError(f"Output file '{output_file}' already exists.")
    input_file = Path.file(source_file)
    if input_file == output_file:
        raise ValueError(
            f"Input '{input_file}' must differ from output '{output_file}'.")
    output_dir = Path.path(os.path.dirname(output_file))
    output_dir.ensure_dir_exists()
    input_dir = Path.directory(os.path.dirname(input_file))

    logger(f"applying pandoc to generate output file '{output_file}' "
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
    cmd: Final[List[str]] = [TOOL_PANDOC,
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

    try:
        shell(cmd, timeout=600, cwd=input_dir, exit_code_to_str=__EXIT_CODES,
              check_stderr=__pandoc_check_stderr)
    finally:
        if template_file:
            os.remove(template_file)
        if csl_file:
            os.remove(csl_file)

    res = File(output_file)

    logger(f"finished applying pandoc, got output file "
           f"'{res.path}' of size {res.size} bytes.")
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

    :param source_file: the source file
    :param dest_file: the destination file
    :param format_in: the input format
    :param locale: the language to be used for compiling
    :param standalone: should we produce a stand-alone document?
    :param tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param toc_print: should we print the table of contents
    :param toc_depth: the depth of the table of contents
    :param crossref: should we use crossref
    :param bibliography: should we use a bibliography
    :param number_sections: should sections be numbered?
    :param top_level_division: the top-level division
    :param use_listings: should the listings package be used?
    :param get_meta: a function to access meta-data
    :param resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    """
    args = []
    if locale is not None:
        locale = enforce_non_empty_str_without_ws(locale)
        if (locale == "zh") or (locale.startswith("zh-")) or \
                (locale.startswith("zh_")):
            args.append("--pdf-engine=xelatex")
    top_level_division = enforce_non_empty_str_without_ws(top_level_division)
    args.append(f"--top-level-division={top_level_division}")
    if use_listings:
        args.append("--listings")

    with TempFile.create(suffix=".pdf") as tf:
        res = pandoc(source_file=source_file,
                     dest_file=tf,
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
                     args=args,
                     overwrite=True).path
        res = pdf_postprocess(in_file=res,
                              out_file=dest_file)
    return File(res)


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

    :param source_file: the source file
    :param dest_file: the destination file
    :param format_in: the input format
    :param locale: the language to be used for compiling
    :param standalone: should we produce a stand-alone document?
    :param tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param toc_print: should we print the table of contents
    :param toc_depth: the depth of the table of contents
    :param crossref: should we use crossref
    :param bibliography: should we use a bibliography
    :param number_sections: should sections be numbered?
    :param get_meta: a function to access meta-data
    :param resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
    :rtype: File
    """
    endresult: Optional[Path] = None  # nosem  # type: ignore  # nolint
    try:
        with TempFile.create(suffix=".html") as tmp:
            # noinspection PyUnusedLocal
            inner_file: Optional[Path] = None  # nosem  # type: ignore
            try:
                with ResourceServer() as serv:
                    inner_file = pandoc(
                        source_file=source_file,
                        dest_file=tmp,
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
                        overwrite=True,
                        args=[f"--mathjax={serv.get_mathjax_url()}",
                              "--ascii", "--html-q-tags",
                              # eventually replace --self-contained with
                              # "--embed-resources"
                              "--self-contained"]).path
                    if inner_file is not None:
                        inner_file.enforce_file()
            except BaseException as ve:
                raise ve if isinstance(ve, ValueError) else ValueError(ve)

            if inner_file is None:
                raise ValueError("Huh? pandoc did not return a file?")

            if bibliography:
                # For some reason, the id and the text of each bibliography
                # item are each put into separate divs of classes for which
                # no styles are given. Therefore, we convert these divs to
                # spans and add some vertical spacing.
                text = enforce_non_empty_str(
                    inner_file.read_all_str().strip())
                end = text.rfind("<div id=\"refs\"")
                if end > 0:
                    text_1 = text[:end]
                    text_2 = text[end:]
                    del text

                    text_2 = regex_sub(
                        '\\s*<div\\s+class="\\s*csl-left-margin\\s*"\\s*>'
                        '\\s*(.*?)\\s*</div>\\s*',
                        '<span class="csl-left-margin">\\1</span>&nbsp;',
                        text_2)

                    text_2 = regex_sub(
                        '\\s*<div\\s+class="\\s*csl-right-inline\\s*"\\s*>'
                        '\\s*(.*?)\\s*</div>\\s*',
                        '<span class="csl-right-inline">\\1</span>',
                        text_2)

                    text_2 = text_2.replace(
                        ' class="csl-entry" role="doc-biblioentry">',
                        ' class="csl-entry" role="doc-biblioentry" '
                        'style="margin-top:0.33em">')

                    inner_file.write_all([text_1, text_2])
            endresult = html_postprocess(in_file=inner_file,
                                         out_file=dest_file,
                                         flatten_data_uris=True,
                                         fully_evaluate_html=True,
                                         purge_scripts=True,
                                         minify=True,
                                         purge_mathjax=True,
                                         canonicalize_ids=True,
                                         overwrite=False)
    except BaseException as be:
        raise be if isinstance(be, ValueError) else ValueError(be)

    if endresult is None:
        raise ValueError("end result is still None?")
    return File(endresult)


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

    :param source_file: the source file
    :param dest_file: the destination file
    :param format_in: the input format
    :param locale: the language to be used for compiling
    :param standalone: should we produce a stand-alone document?
    :param tabstops: the number of spaces with which we replace
        a tab character, or None to not replace
    :param toc_print: should we print the table of contents
    :param toc_depth: the depth of the table of contents
    :param crossref: should we use crossref
    :param bibliography: should we use a bibliography
    :param number_sections: should sections be numbered?
    :param get_meta: a function to access meta-data
    :param resolve_resources: a function to resolve resources
    :return: the Path to the generated output file and it size
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

    :param epub_file: the epub file
    :return: the azw3 file
    """
    input_file = Path.file(epub_file)
    input_dir = Path.directory(os.path.dirname(input_file))
    filename, _ = Path.split_prefix_suffix(os.path.basename(input_file))
    dest_file = Path.resolve_inside(input_dir, f"{filename}.azw3")
    cmd = ["ebook-convert", input_file, dest_file, "--embed-all-fonts"]
    shell(cmd, timeout=360, cwd=input_dir)

    return File(dest_file)
