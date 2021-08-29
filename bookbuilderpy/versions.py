"""Get the versions of all involved libraries and tools."""

import platform
import subprocess  # nosec
from importlib import import_module
from typing import Final, List

import bookbuilderpy.version as ver
from bookbuilderpy.logger import log


def __do_call(args: List[str]) -> str:
    """
    Invoke a sub-process.

    :param List[str] args: the arguments
    :return: the output
    :rtype: str
    """
    try:
        ret = subprocess.run(args, check=False,  # nosec
                             text=True, capture_output=True,  # nosec
                             timeout=360)  # nosec
    except FileNotFoundError:
        return f"{args[0]} not found"
    except BaseException as be:
        return f"encountered {type(be)} when invoking {args[0]}"

    if ret.returncode != 0:
        return f"failed to invoke {args[0]}"

    lines = [a for a in [f.strip() for f in ret.stdout.split("\n")]
             if len(a) > 0]
    if len(lines) <= 0:
        return f"{args[0]} query gives empty result"
    return "\n".join(lines)


def __get_versions() -> str:
    """
    Get the versions of all involved libraries and tools.

    :return: a string with version information of all libraries and tools
    :rtype: str
    """
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
        modname = modname if len(package) < 2 else f"{modname}/{package[1]}"
        verattr = "__version__" if len(package) < 3 else package[2]
        versions.append(f"package {modname}: {getattr(x, verattr)}")

    versions.append(f"\nlinux: {__do_call(['uname', '-a'])}")

    for tool in ["pdflatex", "xelatex", "pandoc", "calibre",
                 "gs", "zip", "xz"]:
        versions.append(f"\n{tool}: {__do_call([tool, '--version'])}")

    return "\n".join(versions)


def get_versions() -> str:
    """
    Get the versions of all involved libraries and tools.

    :return: a string with version information of all libraries and tools
    :rtype: str
    """
    if not hasattr(get_versions, "__VERSIONS"):
        log("obtaining version information from all packages and tools.")
        setattr(get_versions, "__VERSIONS", __get_versions())
    return getattr(get_versions, "__VERSIONS")
