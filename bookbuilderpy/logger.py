"""The `logger` routine for writing a log string to stdout."""
import datetime
from typing import Callable, Final

#: the "now" function
__DTN: Final[Callable[[], datetime.datetime]] = datetime.datetime.now


def logger(message: str) -> None:
    """
    Write a message to the log.

    :param message: the message
    """
    print(f"{__DTN()}: {message}", flush=True)  # noqa
