"""The base class with the information of a build."""

import datetime


def log(message: str) -> None:
    """
    Write a message to the log.

    :param str message: the message
    """
    print(f"{datetime.datetime.now()}: {message}")
