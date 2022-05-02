"""An internal web server for serving persistent resources."""
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources  # nosem
from threading import Thread
from typing import Optional


def _get_file(name: str) -> Optional[bytes]:
    """
    Get a file from the resource server.

    :param name: the file name
    :return: the file contents
    """
    if not name:
        return None

    while name[0] == "/":
        name = name[1:]
        if not name:
            return None

    i = name.rfind("?")
    if i >= 0:
        name = name[:i]
    i = name.rfind("#")
    if i >= 0:
        name = name[:i]
    i = name.rfind("/")
    if i >= 0:
        name = name[i + 1:]
    fn = name.strip()
    if not name:
        return None

    pack = str(__package__)
    if resources.is_resource(package=pack, name=fn):
        with resources.open_binary(package=pack,
                                   resource=fn) as stream:
            return stream.read()

    return None


class _SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """The internal server for obtaining resources."""

    # noinspection PyPep8Naming
    def do_GET(self) -> None:
        """Get the resource."""
        # noinspection PyUnresolvedReferences
        res = _get_file(self.path)
        if res:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(res)
        else:
            self.send_response(404)
            self.end_headers()


class ResourceServer:
    """The resource server."""

    def __init__(self):
        """Initialize the server."""
        self.__httpd = HTTPServer(('localhost', 0),
                                  _SimpleHTTPRequestHandler)
        self.__thread = Thread(target=self.__serve)

    def __serve(self):
        """Start the server and serve."""
        self.__httpd.serve_forever()

    def get_server(self) -> str:
        """
        Get the server address.

        :return: the server address
        :rtype: str
        """
        return f"http://localhost:{self.__httpd.socket.getsockname()[1]}/"

    def get_mathjax_url(self) -> str:
        """
        Get the mathjax url.

        :return: the mathjax url
        :rtype: str
        """
        return f"{self.get_server()}mathjax.js"

    def __enter__(self):
        """Start the resource server."""
        self.__thread.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> bool:
        """
        Close and exist the server.

        :param exception_type: ignored
        :param exception_value: ignored
        :param traceback: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it
        """
        self.__httpd.shutdown()
        del self.__httpd
        self.__thread.join()
        del self.__thread
        return exception_type is None
