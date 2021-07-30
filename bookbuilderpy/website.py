"""The routine for building the website for the book."""
import os.path
from typing import Iterable, Final, Callable, Optional, Dict

import markdown  # type: ignore

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import LangResult, File
from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_commands import create_preprocessor
from bookbuilderpy.strings import file_size

#: Explanations of file suffixes.
__SUFFIXES: Final[Dict[str, str]] = {
    "pdf": "portable document format",
    "html": "stand-alone web page",
    "epub": "electronic book",
    "azw3": "Amazon Kindle e-book"
}


def build_website(docs: Iterable[LangResult],
                  outer_file: str,
                  body_file: Optional[str],
                  dest_dir: str,
                  get_meta: Callable) -> File:
    """
    Build a website linking to all the generated documents.

    :param Iterable[LangResult] docs: the per-language results
    :param str outer_file: the wrapper file
    :param Optional[str] body_file: the body file
    :param str dest_dir: the destination directory
    :param Callable get_meta: a callable used to get the results
    :return: the file record to the generated website
    :rtype: File
    """
    if docs is None:
        raise ValueError("docs cannot be None.")
    out_dir: Final[Path] = Path.directory(dest_dir)

    # load the html template
    out_file = out_dir.resolve_inside("index.html")
    if os.path.exists(out_file):
        raise ValueError(f"File '{out_file}' already exists.")
    log(f"Beginning to build website '{out_file}'.")
    html = Path.file(outer_file).read_all_str()

    # should there be a body to be included?
    tag_index = html.find(bc.WEBSITE_OUTER_TAG)
    if tag_index >= 0:
        # yes, so we load the body
        body = Path.file(body_file).read_all_str()
        div_1 = body.find(bc.WEBSITE_BODY_TAG_1)
        # should there be an auto-generated file list in markdown?
        if div_1 >= 0:
            # yes!
            div_2 = body.find(bc.WEBSITE_BODY_TAG_2,
                              div_1 + len(bc.WEBSITE_BODY_TAG_1))
            if div_2 <= div_1:
                raise ValueError(
                    f"Website body '{body}' contains "
                    f"'{bc.WEBSITE_BODY_TAG_1}' but not "
                    f"'{bc.WEBSITE_BODY_TAG_2}'.")
            data = [body[:div_1].strip(), "\n\n",
                    '<table style="border:none;margin-left:3em">']

            lang_tr = "<tr>"
            for lang in docs:
                if lang.lang_name:
                    data.append(
                        f'{lang_tr}<td style="text-align:right">&bull;'
                        f'&nbsp;</td><td colspan="4">{lang.lang_name}'
                        '</td></tr>')
                    lang_tr = '<tr style="padding-top:1em">'
                    prefix = '<tr><td /><td style="text-align:right;' \
                             'padding-left:2em">&ndash;&nbsp;</td><td>'
                else:
                    prefix = '<tr><td style="text-align:right">' \
                             '&ndash;&nbsp;</td><td>'

                for res in lang.results:
                    name = os.path.basename(res.path)
                    if res.suffix in __SUFFIXES.keys():
                        name = f"{__SUFFIXES[res.suffix]}&nbsp;({res.suffix})"
                    link = res.path.relative_to(out_dir)
                    size = file_size(res.size).replace(
                        " ", '</td><td style="padding-left:0;'
                             'margin-left:0">&nbsp;')
                    data.append(
                        f'{prefix}<a href="{link}">{name}</a></td>'
                        '<td style="text-align:right;padding-right:0;'
                        f'margin-right:0;padding-left:2em">{size}</td></tr>'
                    )
            data.append('</table>')
            data.append(body[(div_2 + len(bc.WEBSITE_BODY_TAG_2)):].strip())
            body = "".join(data)
            del data

        # merge the body into the outer text
        html = "\n".join(
            [html[:tag_index].strip(),
             markdown.markdown(text=body.strip(),
                               output_format="html").strip(),
             html[(tag_index + len(bc.WEBSITE_OUTER_TAG)):].strip()])
        del body

    html = (create_preprocessor(name=bc.CMD_GET_META,
                                func=get_meta,
                                n=1,
                                strip_white_space=True))(html)
    out_file.write_all(html.strip())
    res = File(out_file)
    log(f"Finished building website '{res.path}', size is {res.size}.")
    return res
