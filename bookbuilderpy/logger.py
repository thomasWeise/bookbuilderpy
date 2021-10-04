"""The logger function."""

import datetime


def log(message: str) -> None:
    """
    Write a message to the log.

    :param str message: the message
    """
    print(f"{datetime.datetime.now()}: {message}", flush=True)
