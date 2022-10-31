"""Loading of data from urls."""

from typing import Final
from typing import Tuple

import certifi
import urllib3  # type: ignore

from bookbuilderpy.path import UTF8
from bookbuilderpy.strings import enforce_non_empty_str, \
    enforce_non_empty_str_without_ws

#: The shared HTTP pool
__HTTP: Final[urllib3.PoolManager] = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())


def __name(request: urllib3.HTTPResponse) -> str:
    """
    Extract the file name from a request.

    :param request: the request
    :return: the file name
    """
    content_disp: str = "Content-Disposition"
    if content_disp in request.headers.keys():
        content_disp = request.headers[content_disp]
        i: int = content_disp.find("filename")
        if i >= 0:
            i = content_disp.find("=", i + 1)
            if i > 0:
                k = content_disp.find('"', i + 1)
                if k > 0:
                    k += 1
                    j = content_disp.find('"', k)
                    if j > k:
                        return enforce_non_empty_str_without_ws(
                            content_disp[k:j])
                else:
                    k = content_disp.find("'", i + 1)
                    if k > 0:
                        k += 1
                        j = content_disp.find("'", k)
                        if j > k:
                            return enforce_non_empty_str_without_ws(
                                content_disp[k:j])
                    else:
                        return enforce_non_empty_str_without_ws(
                            content_disp[i + 1:])
    _url = enforce_non_empty_str(request.geturl())
    url = _url
    last = url.rfind("#")
    if last > 0:
        url = url[:last]
    last = url.rfind("?")
    if last > 0:
        url = url[:last]
    first = url.rfind("/")
    if first < 0:
        raise ValueError(f"Invalid URL '{_url}'.")
    return enforce_non_empty_str_without_ws(url[first + 1:])


def load_binary_from_url(url: str) -> Tuple[str, bytes]:
    """
    Load all the binary data from one url.

    :param url: the url
    :return: a tuple of the file name and the binary data that was loaded
    """
    request: urllib3.HTTPResponse = __HTTP.request("GET", url)
    if request.status != 200:
        raise ValueError(
            f"Error '{request.status}' when downloading url '{url}'.")
    data = request.data
    name = __name(request)
    request.close()
    return name, data


def load_text_from_url(url: str) -> Tuple[str, str]:
    """
    Load all the text from one url.

    :param url: the url
    :return: a tuple of the file name and the text that was loaded
    """
    name, data = load_binary_from_url(url)
    return name, data.decode(UTF8)
