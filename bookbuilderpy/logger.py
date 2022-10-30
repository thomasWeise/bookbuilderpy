"""The logger function."""

import datetime


def logger(message: str) -> None:
    """
    Write a message to the logger.

    :param message: the message
    """
    print(f"{datetime.datetime.now()}: {message}", flush=True)
