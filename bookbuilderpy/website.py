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
    "pdf": 'The portable document format (<code><a href="https://www.iso.org/'
           'standard/75839.html">pdf</a></code>) is most suitable for reading'
           ' on a PC and for printing documents.',
    "html": 'A stand-alone web page (<code><a href="https://www.w3.org/'
            'TR/html5/">html</a></code>) can be viewed well both on mobile '
            'phones as well as on PCs.',
    "epub": 'The electronic book format (<code><a href="https://www.w3.org/'
            'publishing/epub32/">epub</a></code>) is convenient for many '
            'e-book readers as well as mobile phones.',
    "azw3": 'The Amazon Kindle e-book format (<code><a href="http://'
            'kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.'
            'pdf">azw3</a></code>) is a proprietary format suitable for'
            'reading on a Kindle device.',
    "zip": 'A <code><a href="https://www.loc.gov/preservation/digital/'
           'formats/fdd/fdd000354.shtml">zip</a></code> archive containing '
           'the book in all the formats mentioned above for convenient '
           'download.',
    "tar.xz": 'A <code><a href="https://www.gnu.org/software/tar/manual/'
              'html_node/Standard.html">tar</a>.<a href="https://tukaani.'
              'org/xz/format.html">xz</a></code> archive containing the '
              'book in all the formats mentioned above for convenient '
              'download.'
}


def build_website(docs: Iterable[LangResult],
                  outer_file: str,
                  body_file: Optional[str],
                  dest_dir: str,
                  input_dir: str,
                  get_meta: Callable) -> File:
    """
    Build a website linking to all the generated documents.

    :param Iterable[LangResult] docs: the per-language results
    :param str outer_file: the wrapper file
    :param Optional[str] body_file: the body file
    :param str dest_dir: the destination directory
    :param str input_dir: the base input directory
    :param Callable get_meta: a callable used to get the results
    :return: the file record to the generated website
    :rtype: File
    """
    if docs is None:
        raise ValueError("docs cannot be None.")
    out_dir: Final[Path] = Path.directory(dest_dir)
    in_dir = Path.directory(input_dir)

    # load the html template
    out_file = out_dir.resolve_inside("index.html")
    if os.path.exists(out_file):
        raise ValueError(f"File '{out_file}' already exists.")

    log(f"beginning to build website '{out_file}'.")

    html = in_dir.resolve_inside(outer_file).read_all_str()

    # should there be a body to be included?
    tag_index = html.find(bc.WEBSITE_OUTER_TAG)
    if tag_index >= 0:
        # yes, so we load the body
        body = in_dir.resolve_inside(body_file).read_all_str()
        html = "\n".join(
            [html[:tag_index].strip(),
             markdown.markdown(text=body.strip(),
                               output_format="html").strip(),
             html[(tag_index + len(bc.WEBSITE_OUTER_TAG)):].strip()])
        del body

    div_1 = html.find(bc.WEBSITE_BODY_TAG_1)
    # should there be an auto-generated file list in markdown?
    if div_1 >= 0:
        # yes!
        div_2 = html.find(bc.WEBSITE_BODY_TAG_2,
                          div_1 + len(bc.WEBSITE_BODY_TAG_1))
        if div_2 <= div_1:
            raise ValueError(
                f"Website '{html}' contains "
                f"'{bc.WEBSITE_BODY_TAG_1}' but not "
                f"'{bc.WEBSITE_BODY_TAG_2}'.")
        data = [html[:div_1].strip()]
        has_lang_ul: bool = False

        for lang in docs:
            if lang.lang_name:
                if not has_lang_ul:
                    data.append(f'<ul{bc.WEBSITE_LANGS_UL_ARG}>')
                    has_lang_ul = True
                data.append(
                    f'<li{bc.WEBSITE_LANGS_LI_ARG}>'
                    f'<span{bc.WEBSITE_LANGS_NAME_SPAN_ARG}>'
                    f'{lang.lang_name}</span>')
            data.append(f'<ul{bc.WEBSITE_DOWNLOAD_UL_ARG}>')

            for res in lang.results:
                name = os.path.basename(res.path)
                size = file_size(res.size).replace(" ", "&nbsp;")
                data.append(
                    f'<li{bc.WEBSITE_DOWNLOAD_LI_ARG}>'
                    f'<span{bc.WEBSITE_DOWNLOAD_DOWNLOAD_SPAN_ARG}>'
                    f'<a href="{res.path.relative_to(out_dir)}"'
                    f'{bc.WEBSITE_DOWNLOAD_FILE_A_ARG}>'
                    f'{name}</a>&nbsp;'
                    f'<span{bc.WEBSITE_DOWNLOAD_SIZE_SPAN_ARG}>'
                    f'({size})</span></span>')

                if res.suffix in __SUFFIXES.keys():
                    desc = __SUFFIXES[res.suffix]
                    data.append(
                        f'<br><span{bc.WEBSITE_DOWNLOAD_FILE_DESC_SPAN_ARG}>'
                        f'{desc}</span>')
                data.append('</li>')
            data.append('</ul>')
            if has_lang_ul:
                data.append('</li>')
        if has_lang_ul:
            data.append('</ul>')
        data.append(html[(div_2 + len(bc.WEBSITE_BODY_TAG_2)):].strip())
        html = "".join(data).strip()
        del data

    html = (create_preprocessor(name=bc.CMD_GET_META,
                                func=get_meta,
                                n=1,
                                strip_white_space=False))(html)
    out_file.write_all(html.strip())
    res = File(out_file)
    log(f"finished building website '{res.path}', size is {res.size}.")
    return res
