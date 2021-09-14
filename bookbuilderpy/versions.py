"""Get the versions of all involved libraries and tools."""

import platform
import subprocess  # nosec
from importlib import import_module
from typing import Final, List, Dict, Tuple, Optional

import bookbuilderpy.version as ver
from bookbuilderpy.logger import log

#: the name of the git executable tool
TOOL_GIT: Final[str] = "git"
#: the name of the calibre executable tool
TOOL_CALIBRE: Final[str] = "calibre"
#: the name of the ghostscript executable tool
TOOL_GHOSTSCRIPT: Final[str] = "gs"
#: the name of the pandoc executable tool
TOOL_PANDOC: Final[str] = "pandoc"
#: the name of the pdflatex executable tool
TOOL_PDFLATEX: Final[str] = "pdflatex"
#: the name of the xelatex executable tool
TOOL_XELATEX: Final[str] = "xelatex"
#: the name of the xz executable tool
TOOL_XZ: Final[str] = "xz"
#: the name of the zip executable tool
TOOL_ZIP: Final[str] = "zip"


def _do_call(tool: str, arg: str) -> Tuple[str, bool]:
    """
    Invoke a sub-process.

    :param str tool: the tool
    :param str arg: the argument
    :return: the output
    :rtype: Tuple[str, bool]
    """
    try:
        ret = subprocess.run([tool, arg], check=False,  # nosec
                             text=True, capture_output=True,  # nosec
                             timeout=360)  # nosec
    except FileNotFoundError:
        return f"{tool} not found", False
    except BaseException as be:
        return f"encountered {type(be)} when invoking {tool}", False

    if ret.returncode != 0:
        return f"failed to invoke {tool}", False

    lines = [a for a in [f.strip() for f in ret.stdout.split("\n")]
             if len(a) > 0]
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

        :param str tool: the tool executable
        :return: `True` if the tool is installed, `False` otherwise.
        :rtype: bool
        """
        if tool in self.__has_tool:
            return self.__has_tool[tool][1]
        self.__has_tool[tool] = h = _do_call(tool, "--version")
        return h[1]

    def get_versions(self) -> str:
        """
        Get the versions of all involved libraries and tools.

        :return: a string with version information of all libraries and tools
        :rtype: str
        """
        if self.__versions:
            return self.__versions

        log("obtaining all version information.")
        versions: Final[List[str]] = \
            [f"python version: {platform.python_version()}",
             f"python build: {platform.python_build()[1]}",
             f"python compiler: {platform.python_compiler()}",
             f"python implementation: {platform.python_implementation()}",
             f"bookbuilderpy: {ver.__version__}"]

        for package in [("markdown",), ("yaml", "pyaml"),
                        ("regex",), ("strip_hints", "strip-hints", "version"),
                        ("urllib3",), ("yapf",)]:
            modname = package[0]
            x = import_module(modname)
            modname = modname if len(package) < 2 \
                else f"{modname}/{package[1]}"
            verattr = "__version__" if len(package) < 3 else package[2]
            versions.append(f"package {modname}: {getattr(x, verattr)}")

        versions.append(f"\nlinux: {_do_call('uname', '-a')[0]}")

        for tool in [TOOL_GIT, TOOL_CALIBRE, TOOL_GHOSTSCRIPT, TOOL_PANDOC,
                     TOOL_PDFLATEX, TOOL_XELATEX, TOOL_XZ, TOOL_ZIP]:
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

    :param str tool: the tool executable
    :return: `True` if the tool is installed, `False` otherwise.
    :rtype: bool
    """
    return __SINGLETON.has_tool(tool)


def get_versions() -> str:
    """
    Get the versions of all involved libraries and tools.

    :return: a string with version information of all libraries and tools
    :rtype: str
    """
    return __SINGLETON.get_versions()
