"""Post-process HTML files."""

from os.path import exists
from time import sleep

from selenium import webdriver  # type: ignore

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path
from bookbuilderpy.versions import TOOL_SELENIUM, has_tool


def html_postprocess(in_file: str,
                     out_file: str,
                     overwrite: bool = False) -> Path:
    """
    Post-process a html file.

    :param str in_file: the input file
    :param str out_file: the output file
    :param bool overwrite: should the output file be overwritten if it exists?
    :return: the output file
    :rtype: Path
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    if (not overwrite) and exists(output):
        raise ValueError(f"Output file '{output}' already exists.")
    if source == output:
        raise ValueError(f"Input and output file is the same: '{source}'.")

    if has_tool(TOOL_SELENIUM):
        log(f"Post-processing pdf file '{source}' to '{output}' "
            f"by applying selenium tool '{TOOL_SELENIUM}'.")

        profile = webdriver.FirefoxProfile()
        profile.set_preference("javascript.enabled", True)
        options = webdriver.FirefoxOptions()
        options.headless = True
        browser = webdriver.Firefox(firefox_profile=profile,
                                    options=options)
        browser.set_page_load_timeout(1200)
        browser.set_script_timeout(1200)
        browser.get('file:///' + source)
        sleep(1)
        html: str = browser.page_source
        browser.quit()

        html = html.strip()
        if not html.startswith("<!"):
            html = "<!DOCTYPE HTML>" + html

        output.write_all(html)

    else:
        log(f"Selenium tool '{TOOL_SELENIUM}' not installed, "
            "copying files directly.")
        Path.copy_file(source, output)

    output.enforce_file()

    return output
