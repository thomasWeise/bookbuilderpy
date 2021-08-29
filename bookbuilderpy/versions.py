"""Get the versions of all involved libraries and tools."""

import platform
import subprocess  # nosec
from importlib import import_module
from typing import Final, List

import bookbuilderpy.version as ver
from bookbuilderpy.logger import log


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

    ret = subprocess.run(["uname", "-a"], check=False,  # nosec
                         text=True, capture_output=True,  # nosec
                         timeout=360)  # nosec
    if ret.returncode != 0:
        versions.append("\nlinux: uname failed")
    else:
        lines = [a for a in [f.strip() for f in ret.stdout.split("\n")]
                 if len(a) > 0]
        if len(lines) <= 0:
            versions.append("\nlinux: uname query gives empty result")
        elif len(lines) == 1:
            versions.append(f"\nlinux: {lines[0]}")
        else:
            versions.append(f"\nlinux: {lines[0]}")
            versions.extend(lines[1:])

    for tool in ["pdflatex", "xelatex", "pandoc", "calibre",
                 "gs", "zip", "xz"]:

        ret = subprocess.run([tool, "--version"], check=False,  # nosec
                             text=True, capture_output=True,  # nosec
                             timeout=360)  # nosec
        if ret.returncode != 0:
            versions.append(f"\n{tool}: not installed")
        else:
            lines = [a for a in [f.strip() for f in ret.stdout.split("\n")]
                     if len(a) > 0]
            if len(lines) <= 0:
                versions.append(f"\n{tool}: version query gives empty result")
            elif len(lines) == 1:
                versions.append(f"\n{tool}: {lines[0]}")
            else:
                versions.append(f"\n{tool}: {lines[0]}")
                versions.extend(lines[1:])

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
