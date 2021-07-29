"""An internal web server for serving persistent resources."""
import os.path
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from threading import Thread
from typing import Final, Optional
from zipfile import ZipFile

from bookbuilderpy.temp import TempDir, TempFile

#: the katex prefix
_KATEX: Final[str] = "katex"


class _SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """The internal server for obtaining resources."""

    def __init__(self, *args, get_file, **kwargs):
        """
        Initialize the request handler.

        :param get_file: the callback to get files
        """
        self.__get_file = get_file
        super().__init__(*args, **kwargs)

    # noinspection PyPep8Naming
    def do_GET(self) -> None:
        """Get the resource."""
        # noinspection PyUnresolvedReferences
        res = self.__get_file(self.path)
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
                                  partial(_SimpleHTTPRequestHandler,
                                          get_file=self.get_file))
        self.__thread = Thread(target=self.__serve)
        self.__katex = None

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

    def get_katex_server(self) -> str:
        """
        Get the katex server address.

        :return: the katex server address
        :rtype: str
        """
        return f"{self.get_server()}{_KATEX}/"

    def get_file(self, name: str) -> Optional[bytes]:
        """
        Get a katex file.

        :param name: the file name
        :return: the file contents
        :rtype: Optional[bytes]
        """
        if not name:
            return None

        if name[0] == "/":
            name = name[1:]
            if not name:
                return None

        if name.startswith(_KATEX):
            if self.__katex is None:
                self.__katex = TempDir.create()
                with TempFile.create() as tf:
                    with resources.open_binary(package=str(__package__),
                                               resource="katex.zip") as stream:
                        with open(tf, "wb") as fd:
                            fd.write(stream.read())
                    with ZipFile(tf) as zf:
                        zf.extractall(self.__katex)
            f = self.__katex.resolve_inside(name)
            if not os.path.isfile(f):
                return None
            with open(f, "rb") as fd:
                return fd.read()

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

    def __enter__(self):
        """Start the resource server."""
        self.__thread.start()
        return self

    def __exit__(self, *args):
        """Close and exist the server."""
        self.__httpd.shutdown()
        del self.__httpd
        self.__thread.join()
        del self.__thread
        if self.__katex is not None:
            self.__katex.__exit__(*args)
        return self
