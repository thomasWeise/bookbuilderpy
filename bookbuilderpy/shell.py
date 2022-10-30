"""The tool for invoking shell commands."""

import subprocess  # nosec
from typing import Union, Iterable, Optional, Dict, Callable

from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path


def shell(command: Union[str, Iterable[str]],
          timeout: int = 3600,
          cwd: Optional[str] = None,
          wants_stdout: bool = False,
          exit_code_to_str: Optional[Dict[int, str]] = None,
          check_stderr: Callable[[str], Optional[BaseException]]
          = lambda x: None) -> Optional[str]:
    """
    Execute a text-based command on the shell.

    The command is executed and its stdout and stderr and return code are
    captured. If the command had a non-zero exit code, an exception is
    thrown. The command itself, as well as the parameters are logged via
    the logger. If wants_stdout is True, the command's stdout is returned.
    Otherwise, None is returned.

    :param command: the command to execute
    :param timeout: the timeout
    :param cwd: the directory to run inside
    :param wants_stdout: if `True`, the stdout is returned, if `False`,
        `None` is returned
    :param exit_code_to_str: an optional map
        converting erroneous exit codes to strings
    :param check_stderr: an optional callable that is applied to the std_err
        string and may raise an exception if need be
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
        logger(f"executing {execstr}.")
        # nosemgrep
        ret = subprocess.run(cmd, check=False, text=True,  # nosec
                             timeout=timeout,  # nosec
                             stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE,  # nosec
                             cwd=wd)  # nosec
    else:
        execstr = f"'{execstr}'"
        logger(f"executing {execstr}.")
        # nosemgrep
        ret = subprocess.run(cmd, check=False, text=True,  # nosec
                             timeout=timeout,  # nosec
                             stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE)  # nosec

    logging = [f"finished executing {execstr}.",
               f"obtained return value {ret.returncode}."]

    if (ret.returncode != 0) and exit_code_to_str:
        ec: Optional[str] = exit_code_to_str.get(ret.returncode, None)
        if ec:
            logging.append(f"meaning of return value: {ec}")

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
    logger("\n".join(logging))

    if ret.returncode != 0:
        raise ValueError(
            f"Error {ret.returncode} when executing {execstr} compressor.")

    if stderr:
        exception = check_stderr(stderr)
        if exception is not None:
            raise exception

    return stdout if wants_stdout else None
