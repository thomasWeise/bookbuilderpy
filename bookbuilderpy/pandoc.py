"""A routine for invoking pandoc."""

import os.path
import subprocess  # nosec
from shutil import which
from typing import Optional, Final, List, Callable

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import File
from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.strings import enforce_non_empty_str_without_ws

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
                             "--fail-if-warnings"]

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
        cmd.extend([enforce_non_empty_str_without_ws(a).strip()
                    for a in args])
    cmd.append(input_file)

    ret = subprocess.run(cmd, check=True, text=True, timeout=360,  # nosec
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
