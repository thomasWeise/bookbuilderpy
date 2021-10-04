"""The tool for invoking shell commands."""

import subprocess  # nosec
from typing import Union, Iterable, Optional

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path


def shell(command: Union[str, Iterable[str]],
          timeout: int = 3600,
          cwd: Optional[str] = None,
          wants_stdout: bool = False) -> Optional[str]:
    """
    Execute a text-based command on the shell.

    The command is executed and its stdout and stderr and return code are
    captured. If the command had a non-zero exit code, an exception is
    thrown. The command itself, as well as the parameters are logged via
    the logger. If wants_stdout is True, the command's stdout is returned.
    Otherwise, None is returned.

    :param Union[str, Iterable[str]] command: the command to execute
    :param int timeout: the timeout
    :param Optional[str] cwd: the directory to run inside
    :param bool wants_stdout: if True, the stdout is returned,
        if False, None is returned
    """
    if timeout < 0:
        raise ValueError(f"Timeout must be positive, but is {timeout}.")
    if not command:
        raise ValueError(f"Empty command '{command}'!")
    cmd = [s.strip() for s in list(command)]
    cmd = [s for s in cmd if s]
    if not cmd:
        raise ValueError(f"Empty stripped command '{cmd}'!")
    execstr = "' '".join(cmd)

    if cwd:
        wd = Path.directory(cwd)
        execstr = f"'{execstr}' in '{wd}'"
        log(f"executing {execstr}.")
        ret = subprocess.run(cmd, check=False, text=True,  # nosec
                             timeout=timeout,  # nosec
                             stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE,  # nosec
                             cwd=wd)  # nosec
    else:
        execstr = f"'{execstr}'"
        log(f"executing {execstr}.")
        ret = subprocess.run(cmd, check=False, text=True,  # nosec
                             timeout=timeout,  # nosec
                             stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE)  # nosec

    logging = [f"finished executing {execstr}.",
               f"obtained return value {ret.returncode}."]

    stdout = ret.stdout
    if stdout:
        stdout = stdout.strip()
        if stdout:
            logging.append(f"\nstdout:\n{stdout}")
    else:
        stdout = ""

    stderr = ret.stderr
    if stderr:
        stderr = stderr.strip()
        if stderr:
            logging.append(f"\nstderr:\n{stderr}")
    log("\n".join(logging))

    if ret.returncode != 0:
        raise ValueError(
            f"Error {ret.returncode} when executing {execstr} compressor.")

    return stdout if wants_stdout else None
