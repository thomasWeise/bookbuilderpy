"""Post-process HTML files."""
import base64
from os.path import exists
from typing import Final, Tuple

import regex as reg  # type: ignore
from selenium import webdriver  # type: ignore

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path, UTF8, move_pure
from bookbuilderpy.strings import enforce_non_empty_str
from bookbuilderpy.temp import TempDir
from bookbuilderpy.versions import TOOL_CHROMIUM, TOOL_CHROME_DRIVER, has_tool

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
    if len(res) < (args.end() - args.start()):
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


def __unpack_data_urls(text: str) -> str:
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
                     overwrite: bool = False) -> Path:
    """
    Post-process a html file.

    :param str in_file: the input file
    :param str out_file: the output file
    :param bool flatten_data_uris: should we flatten data URIs?
    :param bool fully_evaluate_html: should we use selenium to fully evaluate
        all html and javascript?
    :param bool purge_scripts: should we purge all javascripts from the file?
    :param bool overwrite: should the output file be overwritten if it exists?
    :return: the output file
    :rtype: Path
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    log(f"Post-processing HTML file from '{source}' to '{output}'.")
    if (not overwrite) and exists(output):
        raise ValueError(f"Output file '{output}' already exists.")
    if source == output:
        raise ValueError(f"Input and output file is the same: '{source}'.")

    current_file: Path = source
    needs_file_out: bool = False
    text: str = enforce_non_empty_str(source.read_all_str().strip())

    with TempDir.create() as temp:
        if flatten_data_uris:   # flatten data uris
            text_n = enforce_non_empty_str(__unpack_data_urls(text))
            if text_n != text:
                text = text_n
                needs_file_out = True
                log("Flattening the data uris changed the HTML content.")
            else:
                log("Flattening the data uris did not change the "
                    "HTML content.")
            del text_n

        if fully_evaluate_html:  # flatten scripts and html
            if has_tool(TOOL_CHROMIUM) and has_tool(TOOL_CHROME_DRIVER):
                log(f"Invoking '{TOOL_CHROME_DRIVER}' via selenium to "
                    "evaluate HTML.")
                options = webdriver.ChromeOptions()
                options.headless = True
                options.add_argument("--enable-javascript")
                browser = webdriver.Chrome(options=options)
                if needs_file_out:
                    current_file = temp.resolve_inside("1.html")
                    current_file.write_all(text)
                    needs_file_out = False
                current_file.enforce_file()
                browser.get('file:///' + current_file)
                html = browser.page_source
                browser.quit()
                html = html.strip()
                if not html.startswith("<!"):
                    html = "<!DOCTYPE HTML>" + html
                if html != text:
                    needs_file_out = True
                    text = html
                    log("HTML evaluation did change something.")
                else:
                    log("HTML evaluation changed nothing.")
                del html
            else:
                log(f"Cannot use HTML evaluation, '{TOOL_CHROMIUM}' or '"
                    f"{TOOL_CHROME_DRIVER}' not present.")

        if purge_scripts:  # purge java script
            ntext = text
            for regex in __REGEXES_JAVASCRIPT:
                ntext = reg.sub(regex, "", ntext)
            if ntext != text:
                needs_file_out = True
                text = ntext
                log("Javascript purging changed HTML content.")
            else:
                log("No javascript found to remove.")
            del ntext

        if needs_file_out:
            log(f"Writing post-processing result to '{output}'.")
            output.write_all(text)
        elif current_file == source:
            log(f"Copying HTML from '{source}' to '{output}'.")
            Path.copy_file(source, output)
        else:
            log(f"Moving HTML from '{current_file}' to '{output}'.")
            move_pure(current_file, output)

    output.enforce_file()
    return output
