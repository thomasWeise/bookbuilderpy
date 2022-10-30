"""Post-process HTML files."""
import base64
import os
import string
from os.path import exists
from re import compile as _compile, MULTILINE
from typing import Final, List, Tuple, Dict, Pattern

import bs4  # type: ignore
import minify_html  # type: ignore
import regex as reg  # type: ignore
from selenium import webdriver  # type: ignore

from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path, UTF8, move_pure
from bookbuilderpy.strings import enforce_non_empty_str, regex_sub
from bookbuilderpy.temp import TempDir
from bookbuilderpy.versions import TOOL_FIREFOX, TOOL_FIREFOX_DRIVER, has_tool

#: the regexes for java script
__REGEXES_URI_JAVASCRIPT: Final[Tuple[reg.Regex, ...]] = tuple(
    [reg.compile(  # nosemgrep
        f'<script src=\"data:application/{x}'  # nosemgrep
        '(;\\s*charset=utf-8)?;base64,'  # nosemgrep
        '((?:[A-Za-z0-9+\\/]{4})*(?:[A-Za-z0-9+\\/]'  # nosemgrep
        '{4}|[A-Za-z0-9+\\/]{3}='  # nosemgrep
        '|[A-Za-z0-9+\\/]{2}={2}))'  # nosemgrep
        '\"(\\s+type="text/javascript")?'  # nosemgrep
        f'{y}',  # nosemgrep
        flags=reg.V1 | reg.MULTILINE)  # pylint: disable=E1101
        for x in ["octet-stream", "javascript"]
        for y in ["\\s*/>", ">\\s*</script>"]]
)

#: the regexes for css
__REGEXES_URI_CSS: Final[Tuple[reg.Regex, ...]] = tuple(
    [reg.compile(  # nosemgrep
        '<link rel=\"stylesheet\" '  # nosemgrep
        f'href=\"data:application/{x}(;'  # nosemgrep
        '\\s*charset=utf-8)?;base64,((?:[A-Za-z0-9'  # nosemgrep
        '+\\/]{4})*(?:[A-Za-z'  # nosemgrep
        '0-9+\\/]{4}|[A-Za-z0-9+\\/]{3}=|'  # nosemgrep
        '[A-Za-z0-9+\\/]{2}={2}))\"'  # nosemgrep
        '(\\s+type="text/css")?'  # nosemgrep
        f'{y}',  # nosemgrep
        flags=reg.V1 | reg.MULTILINE)  # pylint: disable=E1101
        for x in ["octet-stream"]
        for y in ["\\s*/>", ">\\s*</link>"]]
)


def __base64_unpacker(args, start: str, end: str) -> str:
    """
    Convert the base64 encoded text to normal text.

    :param args: the arguments
    :param start: the start tag
    :param end: the end tag
    :return: the text
    """
    decoded = base64.b64decode(str(args.groups()[1]).strip()).decode(UTF8)
    res = f'{start}{decoded.strip()}{end}'
    if len(res) <= (args.end() - args.start()):
        return res
    return str(args).strip()


def __base64_unpacker_js(args) -> str:
    """
    Convert the base64 encoded javascript to normal text.

    This does not seem to work?

    :param args: the arguments
    :return: the text
    """
    return __base64_unpacker(args, '<script type="text/javascript">',
                             '</script>')


def __base64_unpacker_css(args) -> str:
    """
    Convert the base64 encoded css to normal text.

    This does not seem to work?

    :param args: the arguments
    :return: the text
    """
    return __base64_unpacker(args, '<style type="text/css">', '</style>')


def __unpack_data_uris(text: str) -> str:
    """
    Unpack all javascript data urls.

    :param text: the original html text
    :return: the text with all scripts expanded
    """
    for regex in __REGEXES_URI_JAVASCRIPT:
        while True:
            tn = reg.sub(regex, __base64_unpacker_js, text)
            if tn is text:
                break
            text = tn
    for regex in __REGEXES_URI_CSS:
        while True:
            tn = reg.sub(regex, __base64_unpacker_css, text)
            if tn is text:
                break
            text = tn
    return text


# noinspection PyBroadException
def html_postprocess(in_file: str,
                     out_file: str,
                     flatten_data_uris: bool = True,
                     fully_evaluate_html: bool = False,
                     purge_scripts: bool = False,
                     minify: bool = True,
                     purge_mathjax: bool = True,
                     canonicalize_ids: bool = True,
                     overwrite: bool = False) -> Path:
    """
    Post-process a html file.

    :param in_file: the input file
    :param out_file: the output file
    :param flatten_data_uris: should we flatten data URIs?
    :param fully_evaluate_html: should we use selenium to fully evaluate
        all html and javascript?
    :param purge_scripts: should we purge all javascripts from the file?
    :param minify: should we minify the HTML output?
    :param purge_mathjax: purge all mathjax stuff?
    :param canonicalize_ids: should we canonicalize the IDs?
    :param overwrite: should the output file be overwritten if it exists?
    :return: the output file
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    logger(f"post-processing HTML file from '{source}' to '{output}'.")
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
                logger("flattening the data uris changed the HTML content.")
            else:
                logger("flattening the data uris did not change the "
                       "HTML content.")
            del text_n

        if fully_evaluate_html:  # flatten scripts and html
            if has_tool(TOOL_FIREFOX_DRIVER) and has_tool(TOOL_FIREFOX):
                options = webdriver.FirefoxOptions()
                options.headless = True
                options.add_argument("--enable-javascript")
                try:
                    browser = webdriver.Firefox(
                        options=options, service_log_path=os.path.devnull)
                except BaseException:
                    browser = webdriver.Firefox(
                        options=options, firefox_binary=TOOL_FIREFOX,
                        service_log_path=os.path.devnull)

                if needs_file_out:
                    current_file = temp.resolve_inside("1.html")
                    current_file.write_all(text)
                    needs_file_out = False
                current_file.enforce_file()
                logger(f"invoking '{TOOL_FIREFOX_DRIVER}' via selenium on "
                       f"'{current_file}' to evaluate HTML.")
                browser.get('file:///' + current_file)
                browser.implicitly_wait(1)
                html = browser.page_source
                browser.quit()
                html = html.strip()
                if not html:
                    raise ValueError("Browser returned empty html.")
                if not html.startswith("<!"):
                    html = "<!DOCTYPE HTML>" + html
                if html != text:
                    needs_file_out = True
                    text = html
                    logger("html evaluation did change something.")
                else:
                    logger("html evaluation changed nothing.")
                del html
            else:
                logger(f"cannot use HTML evaluation, '{TOOL_FIREFOX}' or '"
                       f"{TOOL_FIREFOX_DRIVER}' not present.")

        if minify or canonicalize_ids or purge_scripts:  # minify output
            ntext = enforce_non_empty_str(__html_crusher(
                text, canonicalize_ids=canonicalize_ids,
                purge_mathjax=purge_mathjax,
                minify=minify,
                purge_scripts=purge_scripts))
            if ntext != text:
                needs_file_out = True
                text = ntext
                logger("html minification has changed the content.")
            else:
                logger("html minification had no impact")
            del ntext

        if needs_file_out:
            logger(f"writing post-processing result to '{output}'.")
            output.write_all(text)
        elif current_file == source:
            logger(f"copying HTML from '{source}' to '{output}'.")
            Path.copy_file(source, output)
        else:
            logger(f"moving HTML from '{current_file}' to '{output}'.")
            move_pure(current_file, output)

    output.enforce_file()
    return output


def __inner_minify(parsed: bs4.BeautifulSoup) -> None:
    """
    Execute the inner HTML minification routine.

    This routine can be applied before and after ID normalization.

    :param bs4.BeautifulSoup parsed: the tags to process
    """
    # try to discover and purge useless references
    for tag in parsed("span"):
        if "id" in tag.attrs:
            tagid = tag.attrs["id"]
            if tag.contents:
                child = tag.contents[0]
                if child.name == "a":
                    if "href" in child.attrs:
                        ref = child.attrs["href"]
                        if ref.startswith("#") and (ref[1:] == tagid):
                            if not (child.contents or child.string):
                                del child.attrs["href"]

    # replace tags with their children if they have no attributes
    # or other contents
    for name in ["span", "div", "g"]:
        for tag in reversed(list(parsed(name))):
            if tag.contents and (len(tag.contents) == 1) and \
                    (not tag.string):
                child = tag.contents[0]
                if child.name == name:
                    if not tag.attrs:
                        tag.replace_with(child)
                        continue
                    if not child.attrs:
                        child.attrs = tag.attrs
                        tag.replace_with(child)
                        continue
                    if (list(tag.attrs.keys()) == ["id"]) \
                            ^ (list(child.attrs.keys()) == ["id"]):
                        child.attrs.update(tag.attrs)
                        tag.replace_with(child)
                        continue


#: the useless spans pattern
__USELESS_SPANS: Final[Pattern] = _compile(
    r"<span>([a-zA-Z0-9 \t\n,;.:-_#'+~*^°!\"§$%&/()[]{}=?\\?`@|>]*?)</span>",
    MULTILINE)


def __html_crusher(text: str,
                   canonicalize_ids: bool = True,
                   purge_mathjax: bool = True,
                   minify: bool = True,
                   purge_scripts: bool = False) -> str:
    """
    Crush the html content.

    :param text: the text coming in
    :param canonicalize_ids: should we canonicalize the IDs?
    :param purge_mathjax: purge all mathjax stuff?
    :param minify: should we minify the HTML output?
    :param purge_scripts: should we purge all javascripts?
    :return: the crushed html text
    """
    parsed: bs4.BeautifulSoup = bs4.BeautifulSoup(text, "html.parser")

    # remove the useless mathjax content
    if purge_mathjax:
        # delete useless mathml content
        for tag in parsed("mjx-assistive-mml"):
            tag.decompose()

        # delete useless components of tags
        for tag in parsed("use"):
            if "data-c" in tag.attrs:
                del tag.attrs["data-c"]
        for tag in parsed("g"):
            if "data-mml-node" in tag.attrs:
                del tag.attrs["data-mml-node"]
            if "data-mjx-texclass" in tag.attrs:
                del tag.attrs["data-mjx-texclass"]
        for tag in parsed("mjx-container"):
            if "class" in tag.attrs:
                clz = " ".join(tag.attrs["class"])
                clzn = clz.replace(" CtxtMenu_Attached_0", "") \
                    .replace("CtxtMenu_Attached_0 ", "") \
                    .replace("  ", " ").strip()
                if clzn != clz:
                    tag.attrs["class"] = clzn
            if "ctxtmenu_counter" in tag.attrs:
                del tag.attrs["ctxtmenu_counter"]
            if "tabindex" in tag.attrs:
                del tag.attrs["tabindex"]

        # purge useless context menu styles
        for tag in parsed("style"):
            tagtext = tag.string
            if ".CtxtMenu_" in tagtext:
                tag.decompose()
                continue
            found = False
            while True:
                idx1 = tagtext.find("mjx-assistive-mml")
                if idx1 < 0:
                    break
                idx2 = tagtext.find("{", idx1)
                if idx2 <= idx1:
                    break
                idx3 = tagtext.find("}", idx2)
                if idx3 <= idx2:
                    break
                tagtext = tagtext[:idx1].strip() + \
                    tagtext[(idx3 + 1):].strip()
                found = True
            if found:
                tag.string = tagtext

    # purge all scripts
    if purge_scripts:
        for tag in parsed("script"):
            tag.decompose()

    if minify:
        # merge all styles
        styles = parsed("style")
        if len(styles) > 1:
            all_styles = "".join(tag.string.strip() for tag in styles)
            for tag in styles[1:]:
                tag.decompose()
            styles[0].string = all_styles
        # remove the generator meta data, as it is not needed
        for tag in parsed("meta"):
            if "name" in tag.attrs:
                if tag.attrs["name"] == "generator":
                    tag.decompose()

        __inner_minify(parsed)

    # replace all ids with shorter ids
    if canonicalize_ids:
        # first, we try to minify the element IDs
        id_counts: Dict[str, int] = {}
        # find all IDs
        for ref in ["id", "name"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                a = tag.attrs[ref]
                if len(a) <= 0:
                    del tag.attrs[ref]
                    continue
                if (tag.name.lower() == "meta") and (ref == "name"):
                    continue
                if a in id_counts:
                    raise ValueError(
                        f"id '{a}' in '{ref}' of tag '{tag}' appears twice!")
                id_counts[a] = 0
        # count the references to them
        for ref in ["href", "xlink:href"]:
            for tag in parsed.findAll(lambda tg, rr=ref: rr in tg.attrs):
                a = tag.attrs[ref]
                if a.startswith("#"):
                    a = a[1:].strip()
                    if a not in id_counts:
                        raise ValueError("Found reference to undefined id "
                                         f"'{a}' of tag '{tag}'.")
                    id_counts[a] += 1

        # purge all unreferenced ids
        id_list = [(tid, count) for (tid, count) in id_counts.items()
                   if count > 0]
        del id_counts

        # create smaller IDs
        id_list.sort(key=lambda x: -x[1])
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
                    a = a[1:].strip()
                    if a not in ids:
                        raise ValueError(
                            f"Found reference to deleted id '{a}'.")
                    tag.attrs[ref] = f"#{ids[a]}"

        # Since we have minified IDs, we may have purged useless IDs.
        # Thus, maybe we can now purge additional tags.
        if minify:
            __inner_minify(parsed)

    # convert the parsed html back to text and check if it is smaller
    ntext = parsed.__unicode__()
    if len(ntext) < len(text):
        text = ntext

    # apply the final minification step
    if minify:
        ntext = enforce_non_empty_str(
            minify_html.minify(  # pylint: disable=E1101
                text, do_not_minify_doctype=True,
                ensure_spec_compliant_unquoted_attribute_values=True,
                remove_bangs=True,
                remove_processing_instructions=True,
                # keep_closing_tags=True,
                keep_html_and_head_opening_tags=True,
                keep_spaces_between_attributes=True,
                minify_css=True,
                minify_js=True).strip())
        if len(ntext) < len(text):
            text = ntext
        text = regex_sub(__USELESS_SPANS, "\\1", text)

    return text


#: the internal start digits that can be used for it to string conversation
__DIGITS_START = string.ascii_letters
#: the internal digits that can be used for it to string conversation
__DIGITS = __DIGITS_START + string.digits + "-_"


def __int2str(x: int) -> str:
    """
    Convert an integer to a string.

    :param x: the integer
    :return: the compact string
    """
    if x == 0:
        return __DIGITS_START[0]
    digits: List[str] = []
    use_digits = __DIGITS_START
    while x:
        base = len(use_digits)
        digits.append(use_digits[x % base])
        x = x // base
        use_digits = __DIGITS
    return ''.join(digits)
