"""Post-process HTML files."""
import base64
import os
from os.path import exists
from typing import Final, List, Tuple, Dict
import string

import bs4  # type: ignore
import minify_html  # type: ignore
import regex as reg  # type: ignore
from selenium import webdriver  # type: ignore

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path, UTF8, move_pure
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.temp import TempDir
from bookbuilderpy.versions import TOOL_FIREFOX, TOOL_FIREFOX_DRIVER, has_tool

#: the regexes for java script
__REGEXES_URI_JAVASCRIPT: Final[Tuple[reg.Regex, ...]] = tuple(
    [reg.compile(
        f'<script src=\"data:application/{x}(;\\s*charset=utf-8)?;base64,'
        '((?:[A-Za-z0-9+\\/]{4})*(?:[A-Za-z0-9+\\/]{4}|[A-Za-z0-9+\\/]{3}='
        '|[A-Za-z0-9+\\/]{2}={2}))\"(\\s+type="text/javascript")?'
        f'{y}',
        flags=reg.V1 | reg.MULTILINE)
        for x in ["octet-stream", "javascript"]
        for y in ["\\s*/>", ">\\s*</script>"]]
)

#: the regexes for css
__REGEXES_URI_CSS: Final[Tuple[reg.Regex, ...]] = tuple(
    [reg.compile(
        f'<link rel=\"stylesheet\" href=\"data:application/{x}(;'
        '\\s*charset=utf-8)?;base64,((?:[A-Za-z0-9+\\/]{4})*(?:[A-Za-z'
        '0-9+\\/]{4}|[A-Za-z0-9+\\/]{3}=|[A-Za-z0-9+\\/]{2}={2}))\"'
        '(\\s+type="text/css")?'
        f'{y}',
        flags=reg.V1 | reg.MULTILINE)
        for x in ["octet-stream"]
        for y in ["\\s*/>", ">\\s*</link>"]]
)


def __base64_unpacker(args, start: str, end: str) -> str:
    """
    Convert the base64 encoded text to normal text.

    :param args: the arguments
    :param str start: the start tag
    :param str end: the end tag
    :return: the text
    :rtype: str
    """
    decoded = base64.b64decode(str(args.groups()[1]).strip()).decode(UTF8)
    res = f'{start}{decoded.strip()}{end}'
    if len(res) <= (args.end() - args.start()):
        return res
    return str(args).strip()


def __base64_unpacker_js(args) -> str:
    """
    Convert the base64 encoded javascript to normal text.

    :param args: the arguments
    :return: the text
    :rtype: str
    """
    return __base64_unpacker(args, '<script type="text/javascript">',
                             '</script>')


def __base64_unpacker_css(args) -> str:
    """
    Convert the base64 encoded css to normal text.

    :param args: the arguments
    :return: the text
    :rtype: str
    """
    return __base64_unpacker(args, '<style type="text/css">', '</style>')


def __unpack_data_uris(text: str) -> str:
    """
    Unpack all javascript data urls.

    :param str text: the original html text
    :return: the text with all scripts expanded
    :rtype: str
    """
    for regex in __REGEXES_URI_JAVASCRIPT:
        text = reg.sub(regex, __base64_unpacker_js, text)
    for regex in __REGEXES_URI_CSS:
        text = reg.sub(regex, __base64_unpacker_css, text)
    return text


#: the regular expressions for purging java scripts
__REGEXES_JAVASCRIPT: Tuple[reg.Regex, reg.Regex, reg.Regex] = \
    reg.compile("<script\\s+.*?>.*?</script>",
                flags=reg.V1 | reg.MULTILINE | reg.IGNORECASE), \
    reg.compile("<script\\s*>.*?</script>",
                flags=reg.V1 | reg.MULTILINE | reg.IGNORECASE), \
    reg.compile("<script\\s+.*?\\s*/>",
                flags=reg.V1 | reg.MULTILINE | reg.IGNORECASE)


def html_postprocess(in_file: str,
                     out_file: str,
                     flatten_data_uris: bool = True,
                     fully_evaluate_html: bool = False,
                     purge_scripts: bool = False,
                     minify: bool = True,
                     canonicalize_ids: bool = True,
                     overwrite: bool = False) -> Path:
    """
    Post-process a html file.

    :param str in_file: the input file
    :param str out_file: the output file
    :param bool flatten_data_uris: should we flatten data URIs?
    :param bool fully_evaluate_html: should we use selenium to fully evaluate
        all html and javascript?
    :param bool purge_scripts: should we purge all javascripts from the file?
    :param bool minify: should we minify the HTML output?
    :param bool canonicalize_ids: should we canonicalize the IDs?
    :param bool overwrite: should the output file be overwritten if it exists?
    :return: the output file
    :rtype: Path
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    log(f"post-processing HTML file from '{source}' to '{output}'.")
    if (not overwrite) and exists(output):
        raise ValueError(f"Output file '{output}' already exists.")
    if source == output:
        raise ValueError(f"Input and output file is the same: '{source}'.")

    current_file: Path = source
    needs_file_out: bool = False
    text: str = enforce_non_empty_str(source.read_all_str().strip())

    with TempDir.create() as temp:
        if flatten_data_uris:  # flatten data uris
            text_n = enforce_non_empty_str(__unpack_data_uris(text))
            if text_n != text:
                text = text_n
                needs_file_out = True
                log("flattening the data uris changed the HTML content.")
            else:
                log("flattening the data uris did not change the "
                    "HTML content.")
            del text_n

        if fully_evaluate_html:  # flatten scripts and html
            if has_tool(TOOL_FIREFOX_DRIVER) and has_tool(TOOL_FIREFOX):
                # options = webdriver.ChromeOptions()
                options = webdriver.FirefoxOptions()
                options.headless = True
                options.add_argument("--enable-javascript")
                browser = webdriver.Firefox(options=options,
                                            service_log_path=os.path.devnull)
                # .Chrome(options=options)
                if needs_file_out:
                    current_file = temp.resolve_inside("1.html")
                    current_file.write_all(text)
                    needs_file_out = False
                current_file.enforce_file()
                log(f"invoking '{TOOL_FIREFOX_DRIVER}' via selenium on "
                    f"'{current_file}' to evaluate HTML.")
                browser.get('file:///' + current_file)
                browser.implicitly_wait(1)
                html = browser.page_source
                browser.quit()
                html = html.strip()
                if not html.startswith("<!"):
                    html = "<!DOCTYPE HTML>" + html
                if html != text:
                    needs_file_out = True
                    text = html
                    log("html evaluation did change something.")
                else:
                    log("html evaluation changed nothing.")
                del html
            else:
                log(f"cannot use HTML evaluation, '{TOOL_FIREFOX}' or '"
                    f"{TOOL_FIREFOX_DRIVER}' not present.")

        if purge_scripts:  # purge java script
            ntext = text
            for regex in __REGEXES_JAVASCRIPT:
                ntext = reg.sub(regex, "", ntext)
            if ntext != text:
                needs_file_out = True
                text = ntext
                log("javascript purging changed HTML content.")
            else:
                log("no javascript found to remove.")
            del ntext

        if minify:  # minify output
            ntext = enforce_non_empty_str(__html_crusher(
                text, canonicalize_ids=canonicalize_ids))
            if ntext != text:
                needs_file_out = True
                text = ntext
                log("html minification has changed the content.")
            else:
                log("html minification had no impact")
            del ntext

        if needs_file_out:
            log(f"writing post-processing result to '{output}'.")
            output.write_all(text)
        elif current_file == source:
            log(f"copying HTML from '{source}' to '{output}'.")
            Path.copy_file(source, output)
        else:
            log(f"moving HTML from '{current_file}' to '{output}'.")
            move_pure(current_file, output)

    output.enforce_file()
    return output


def __html_crusher(text: str,
                   canonicalize_ids: bool = True) -> str:
    """
    Crush the html content.

    :param str text: the text coming in
    :param bool canonicalize_ids: should we canonicalize the IDs?
    :return: the crushed html text
    :rtype: str
    """
    if canonicalize_ids:
        parsed: bs4.BeautifulSoup = bs4.BeautifulSoup(text, "html.parser")

        # first, we try to minify the element IDs
        id_counts: Dict[str, int] = {}
        # find all IDs
        for ref in ["id", "name"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                if (tag.name.lower() == "meta") and (ref == "name"):
                    continue
                id_counts[tag.attrs[ref]] = 0
        # count the references to them
        for ref in ["href", "xlink:href"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                a = tag.attrs[ref]
                if a.startswith("#"):
                    id_counts[a[1:]] += 1

        # purge all unreferenced ids
        id_list = [(tid, count) for (tid, count) in id_counts.items()
                   if count > 0]
        del id_counts

        # create smaller IDs
        id_list.sort(key=lambda x: x[1])
        ids: Dict[str, str] = {}
        cnt: int = 0
        for idx in id_list:
            ids[idx[0]] = __int2str(cnt)
            cnt += 1
        del id_list, cnt

        # write back the ids
        for ref in ["id", "name"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                if (tag.name.lower() == "meta") and (ref == "name"):
                    continue
                tid = tag.attrs[ref]
                if tid in ids:
                    tag.attrs[ref] = ids[tid]
                else:
                    del tag.attrs[ref]

        # re-link the references
        for ref in ["href", "xlink:href"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                a = tag.attrs[ref]
                if a.startswith("#"):
                    tag.attrs[ref] = f"#{ids[a[1:]]}"

        ntext = parsed.__unicode__()
        if len(ntext) < len(text):
            text = ntext

    ntext = enforce_non_empty_str(minify_html.minify(
        text, do_not_minify_doctype=True,
        ensure_spec_compliant_unquoted_attribute_values=True,
        remove_bangs=True,
        remove_processing_instructions=True,
        # keep_closing_tags=True,
        keep_html_and_head_opening_tags=True,
        keep_spaces_between_attributes=True,
        minify_css=True,
        minify_js=True).strip())
    return ntext if len(ntext) < len(text) else text


#: the internal start digits that can be used for it to string conversation
__DIGITS_START = string.ascii_letters
#: the internal digits that can be used for it to string conversation
__DIGITS = string.digits + __DIGITS_START + "-_"


def __int2str(x: int) -> str:
    """
    Convert an integer to a string.

    :param int x: the integer
    :return: the compact string
    :rtype: str
    """
    if x == 0:
        return __DIGITS_START[0]
    digits: List[str] = []
    use_digits = __DIGITS_START
    while x:
        base = len(use_digits)
        digits.append(__DIGITS[x % base])
        x = x // base
        use_digits = __DIGITS
    digits.reverse()
    return ''.join(digits)
