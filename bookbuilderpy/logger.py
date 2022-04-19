"""The logger function."""

import datetime


def log(message: str) -> None:
    """
    Write a message to the log.

    :param message: the message
    """
    print(f"{datetime.datetime.now()}: {message}", flush=True)
