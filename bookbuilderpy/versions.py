"""Get the versions of all involved libraries and tools."""

import importlib.metadata as ilm
import platform
import subprocess  # nosec
from typing import Final, List, Dict, Tuple, Optional

import bookbuilderpy.version as ver
from bookbuilderpy.logger import logger

#: the name of the calibre executable tool
TOOL_CALIBRE: Final[str] = "calibre"
#: the name of the firefox driver tool
TOOL_FIREFOX_DRIVER: Final[str] = "geckodriver"
#: the name of the firefox browser executable tool
TOOL_FIREFOX: Final[str] = "firefox"
#: the name of the ghostscript executable tool
TOOL_GHOSTSCRIPT: Final[str] = "gs"
#: the name of the git executable tool
TOOL_GIT: Final[str] = "git"
#: the name of the pandoc executable tool
TOOL_PANDOC: Final[str] = "pandoc"
#: the name of the pdflatex executable tool
TOOL_PDFLATEX: Final[str] = "pdflatex"
#: the name of the rsvg-convert executable tool
TOOL_RSVG_CONVERT: Final[str] = "rsvg-convert"
#: the name of the tar executable tool
TOOL_TAR: Final[str] = "tar"
#: the name of the xelatex executable tool
TOOL_XELATEX: Final[str] = "xelatex"
#: the name of the xz executable tool
TOOL_XZ: Final[str] = "xz"
#: the name of the zip executable tool
TOOL_ZIP: Final[str] = "zip"


def __chkstr(n: str,
             purge_starts: Tuple[str, ...] =
             ("copyright", "there is no", "covered by",
              "the lesser gnu g", "the gnu gen", "for more info",
              "named copying", "primary author", "currently maintaine",
              "the author", "latest sourc", "as of above",
              "encryption notice", "the encryption", "put in the", "and, to",
              "in both s", "the usa", "administration regulat",
              "this is free", "warranty", "the source ", "testing/gecko",
              "this program", "license", "you can obt", "written by",
              "no lsb mod", "(see the b", "bzip2 code ")) -> Optional[str]:
    """
    Check whether we should keep a version string.

    :param n: the original string
    :param purge_starts: the strings to purge at the start
    :return: the string, or `None` if it can be purged
    """
    n = n.strip()
    if len(n) <= 0:
        return None
    n = n.replace("\t", " ")
    nlen = len(n)
    while True:
        n = n.replace("  ", " ")
        nlen2 = len(n)
        if nlen2 >= nlen:
            break
        nlen = nlen2
    nl: Final[str] = n.lower()
    if any(nl.startswith(d) for d in purge_starts):
        return None
    return n


def _do_call(tool: str, arg: str) -> Tuple[str, bool]:
    """
    Invoke a sub-process.

    :param tool: the tool
    :param arg: the argument
    :return: the output
    """
    try:
        # nosemgrep
        ret = subprocess.run([tool, arg], check=False,  # nosec
                             text=True, capture_output=True,  # nosec
                             timeout=360)  # nosec
    except FileNotFoundError:
        return f"{tool} not found", False
    except BaseException as be:
        return f"encountered {type(be)} when invoking {tool}", False

    if ret.returncode != 0:
        return f"failed to invoke {tool}", False

    lines = [a for a in [__chkstr(f) for f in ret.stdout.split("\n")]
             if a]
    if len(lines) <= 0:
        return f"{tool} query gives empty result", False
    return "\n".join(lines), True


class __Versions:
    """The internal singleton with the versions."""

    def __init__(self):
        """Initialize."""
        #: the set of tool information
        self.__has_tool: Final[Dict[str, Tuple[str, bool]]] = {}
        #: the version string
        self.__versions: Optional[str] = None

    def has_tool(self, tool: str) -> bool:
        """
        Check if the given tool is installed.

        :param tool: the tool executable
        :return: `True` if the tool is installed, `False` otherwise.
        """
        if tool in self.__has_tool:
            return self.__has_tool[tool][1]
        self.__has_tool[tool] = h = _do_call(tool, "--version")
        return h[1]

    def get_versions(self) -> str:
        """
        Get the versions of all involved libraries and tools.

        :return: a string with version information of all libraries and tools
        """
        if self.__versions:
            return self.__versions

        logger("obtaining all version information.")
        versions: Final[List[str]] = \
            [f"python version: {platform.python_version()}",
             f"python build: {platform.python_build()[1]}",
             f"python compiler: {platform.python_compiler()}",
             f"python implementation: {platform.python_implementation()}",
             f"bookbuilderpy: {ver.__version__}"]

        for package in ["beautifulsoup4", "markdown", "minify_html", "pyyaml",
                        "regex", "strip-hints", "urllib3", "yapf"]:
            version = ilm.version(package).strip()
            versions.append(f"package {package}: {version}")

        versions.append(f"\nlinux: {_do_call('uname', '-a')[0]}")
        versions.append(_do_call("lsb_release", "-a")[0])

        for tool in [TOOL_CALIBRE, TOOL_FIREFOX, TOOL_FIREFOX_DRIVER,
                     TOOL_GHOSTSCRIPT, TOOL_GIT, TOOL_PANDOC,
                     TOOL_PDFLATEX, TOOL_RSVG_CONVERT, TOOL_TAR,
                     TOOL_XELATEX, TOOL_XZ, TOOL_ZIP]:
            has: Tuple[str, bool]
            if tool in self.__has_tool:
                has = self.__has_tool[tool]
            else:
                self.__has_tool[tool] = has = _do_call(tool, '--version')
            versions.append(f"\n{tool}: {has[0]}")

        self.__versions = "\n".join(versions)
        return self.__versions


#: The shared internal singleton
__SINGLETON: Final[__Versions] = __Versions()


def has_tool(tool: str) -> bool:
    """
    Check if the given tool is installed.

    :param tool: the tool executable
    :return: `True` if the tool is installed, `False` otherwise.
    """
    return __SINGLETON.has_tool(tool)


def get_versions() -> str:
    """
    Get the versions of all involved libraries and tools.

    :return: a string with version information of all libraries and tools
    """
    return __SINGLETON.get_versions()
