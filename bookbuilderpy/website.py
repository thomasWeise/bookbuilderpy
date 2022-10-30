"""The routine for building the website for the book."""
import os.path
from typing import Dict
from typing import Iterable, Final, Callable, Optional

import markdown  # type: ignore

import bookbuilderpy.constants as bc
from bookbuilderpy.build_result import LangResult, File
from bookbuilderpy.html import html_postprocess
from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_commands import create_preprocessor
from bookbuilderpy.strings import file_size, enforce_non_empty_str, \
    lang_to_locale
from bookbuilderpy.temp import TempFile

#: Explanations of file suffixes.
__SUFFIXES: Final[Dict[str, Dict[str, str]]] = \
    {"en": {
        "pdf": 'The &quot;portable document format&quot; (<code>'
               '<a href="https://www.iso.org/standard/75839.html">pdf</a>'
               '</code>) is most suitable for reading on a PC and for '
               'printing documents.',
        "html": 'A stand-alone web page (<code><a href="https://www.w3.org/'
                'TR/html5/">html</a></code>) can be viewed well both on '
                'mobile phones as well as on PCs.',
        "epub": 'The electronic book format (<code><a href="https://www.w3'
                '.org/publishing/epub32/">epub</a></code>) is convenient for '
                'many e-book readers as well as mobile phones.',
        "azw3": 'The Amazon Kindle e-book format (<code><a href="http://'
                'kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.'
                'pdf">azw3</a></code>) is a proprietary format suitable for '
                'reading on a Kindle device.',
        "zip": 'A <code><a href="https://www.loc.gov/preservation/digital/'
               'formats/fdd/fdd000354.shtml">zip</a></code> archive '
               'containing the book in all the formats mentioned above for '
               'convenient download.',
        "tar.xz": 'A <code><a href="https://www.gnu.org/software/tar/manual/'
                  'html_node/Standard.html">tar</a>.<a href="https://tukaani.'
                  'org/xz/format.html">xz</a></code> archive containing the '
                  'book in all the formats mentioned above for convenient '
                  'download.'
    }, "de": {
        "pdf": 'Das &quot;portable document format&quot; (<code><a href='
               '"https://www.iso.org/standard/75839.html">pdf</a></code>) ist'
               ' f&uuml;r das Lesen am PC oder das Ausdrucken geeignet.',
        "html": 'Eine stand-alone Webseite (<code><a href="https://www.w3.org/'
                'TR/html5/">html</a></code>) kann sowohl auf dem Mobiltelefon'
                ' als auch auf dem PC gut gelesen werden.',
        "epub": 'Das Format f&uuml;r E-Book (<code><a href="https://www.w3'
                '.org/publishing/epub32/">epub</a></code>) ist g&uuml;nstig '
                'f&uuml;r E-Book Leseger&auml;te, Tablets, und '
                'Mobiltelefone.',
        "azw3": 'Das Amazon Kindle E-Book Format (<code><a href="http://'
                'kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.'
                'pdf">azw3</a></code>) ist propriet&auml;r und f&uuml;r '
                'Kindles gedacht.',
        "zip": 'Ein <code><a href="https://www.loc.gov/preservation/digital/'
               'formats/fdd/fdd000354.shtml">zip</a></code> Archiv mit allen '
               'oben genannten Formaten des Buchs.',
        "tar.xz": 'Ein <code><a href="https://www.gnu.org/software/tar/manual/'
                  'html_node/Standard.html">tar</a>.<a href="https://tukaani.'
                  'org/xz/format.html">xz</a></code> Archiv mit allen '
                  'oben genannten Formaten des Buchs.',
    }, "zh": {
        "pdf": '便携式文档格式（<code><a href="https://www.iso.org/standard/'
               '75839.html">pdf</a></code>）最适合在PC上阅读和打印文档。',
        "html": '无论是在手机上还是在PC上，都可以很好地查看独立的网页（<code>'
                '<a href="https://www.w3.org/TR/html5/">html</a></code>）。',
        "epub": '电子书格式（<code><a href="https://www.w3.org/publishing/epub32/">'
                'epub</a></code>）为许多电子书阅读器和手机提供了便利。',
        "azw3": '亚马逊Kindle电子书格式（<code><a href="http://'
                'kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.'
                'pdf">azw3</a></code>）是一种适合在Kindle设备上阅读的专有格式。',
        "zip": '一个<code><a href="https://www.loc.gov/preservation/digital/'
               'formats/fdd/fdd000354.shtml">zip</a></code>存档，包含上述所有格式的书籍，'
               '便于下载。',
        "tar.xz": '一个<code><a href="https://www.gnu.org/software/tar/manual/'
                  'html_node/Standard.html">tar</a>.<a href="https://tukaani.'
                  'org/xz/format.html">xz</a></code>存档，包含上述所有格式的书籍，便于下载。',
    }}


def build_website(docs: Iterable[LangResult],
                  outer_file: str,
                  body_file: Optional[str],
                  dest_dir: str,
                  input_dir: str,
                  get_meta: Callable) -> File:
    """
    Build a website linking to all the generated documents.

    :param docs: the per-language results
    :param outer_file: the wrapper file
    :param body_file: the body file
    :param dest_dir: the destination directory
    :param input_dir: the base input directory
    :param get_meta: a callable used to get the results
    :return: the file record to the generated website
    """
    if docs is None:
        raise ValueError("docs cannot be None.")
    out_dir: Final[Path] = Path.directory(dest_dir)
    in_dir = Path.directory(input_dir)

    # load the html template
    out_file = out_dir.resolve_inside("index.html")
    if os.path.exists(out_file):
        raise ValueError(f"File '{out_file}' already exists.")

    logger(f"beginning to build website '{out_file}'.")

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

        ldocs = list(docs)
        has_lang_ul = len(ldocs) > 1
        if has_lang_ul:
            data.append(f'<ul{bc.WEBSITE_LANGS_UL_ARG}>')

        for lang in ldocs:
            if has_lang_ul:
                enforce_non_empty_str(lang.lang_name)
                data.append(
                    f'<li{bc.WEBSITE_LANGS_LI_ARG}>'
                    f'<span{bc.WEBSITE_LANGS_NAME_SPAN_ARG}>'
                    f'{lang.lang_name}</span>')
            data.append(f'<ul{bc.WEBSITE_DOWNLOAD_UL_ARG}>')
            locale = "en" if not lang.lang else \
                lang_to_locale(lang.lang).split("_")[0]
            suffixes = __SUFFIXES[locale] if locale in __SUFFIXES else None

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

                if suffixes and (res.suffix in suffixes.keys()):
                    desc = suffixes[res.suffix]
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
    with TempFile.create(suffix=".html") as temp:
        temp.write_all(html.strip())
        out_file = html_postprocess(in_file=temp,
                                    out_file=out_file,
                                    flatten_data_uris=True,
                                    fully_evaluate_html=False,
                                    purge_scripts=False,
                                    minify=True,
                                    canonicalize_ids=True,
                                    purge_mathjax=False,
                                    overwrite=False)

    res = File(out_file)
    logger(f"finished building website '{res.path}', size is {res.size}.")
    return res
