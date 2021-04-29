"""Regular-expression based command generation and invocation."""
from typing import Final

import regex as re  # type: ignore

#: the base number
__BASE_LETTER_ORD: Final[int] = ord("a")


def __letter(a: int) -> str:
    """
    Convert a number to a string.

    :param int a: the number
    :return: the string
    :rtype: str

    >>> __letter(0)
    'a'
    >>> __letter(1)
    'b'
    >>> __letter(26)
    'aa'
    >>> __letter(27)
    'ab'
    """
    s = ""
    while a >= 0:
        ofs = a % 26
        a = (a // 26) - 1
        s = f"{chr(__BASE_LETTER_ORD + ofs)}{s}"
    return s


def create_command_re(prefix: str, n: int = 1,
                      strip_white_space: bool = False) -> re.Regex:
    r"""
    Create a Regular Expression for a LaTeX-Style Command.

    :param str prefix: the prefix of the command
    :param int n: the number of parameters
    :param bool strip_white_space: should the white space around
        the command be stripped
    :return: a regular expression representing the command
    :rtype: re.Regex

    >>> cmd = create_command_re("x", 2, False)
    >>> s = 'blabla\\x{1}{2}xaxa \\x{3}{4} zhdfg'
    >>> re.sub(cmd, lambda g: g[1], s)
    'blabla{1}xaxa {3} zhdfg'
    >>> re.sub(cmd, lambda g: g[2], s)
    'blabla{2}xaxa {4} zhdfg'
    >>> s = 'blabla\\x{\\x{1}{2}}{3} \\x{3}{4}.'
    >>> re.sub(cmd, lambda g: g[1], s)
    'blabla{\\x{1}{2}} {3}.'
    >>> re.sub(cmd, lambda g: g[2], re.sub(cmd, lambda g: g[1], s))
    'blabla{{2}} {3}.'
    >>> cmd = create_command_re("y", 0, True)
    >>> re.sub(cmd, "Z", "hello\n\\y  df")
    'helloZdf'
    >>> cmd = create_command_re("z", 3, True)
    >>> re.sub(cmd, lambda g: g[1]+g[3], "hello\n\\z{A x}{b k}{z}  df")
    'hello{A x}{z}df'
    >>> re.sub(cmd, lambda g: g[1]+g[3], "hello\n\\z{{A x}}{b k}{z}  df")
    'hello{{A x}}{z}df'
    """
    if not isinstance(prefix, str):
        raise TypeError(f"prefix must be string but is {type(prefix)}.")
    if len(prefix) <= 0:
        raise ValueError(f"prefix cannot be '{prefix}'.")
    if not isinstance(n, int):
        raise TypeError(f"n must be int, but is {type(n)}.")
    if n < 0:
        raise ValueError(f"n cannot be '{n}'.")
    if not isinstance(strip_white_space, bool):
        raise TypeError("strip_white_space must be int, "
                        f"but is {type(strip_white_space)}.")

    # First, we build the regular expression, which makes sure that braces
    # numbers match.

    # Create the command the prefix.
    regexpr: str = re.escape(f"\\{prefix}")

    # Add the parameter groups.
    if n > 0:
        regexpr += "".join(
            ["".join([r"(\{(?>[^\{\}]|(?",
                      str(i + 1), r"))*+\})"])
             for i in range(n)])

    # Add potential whitespace strippers.
    if strip_white_space:
        regexpr = "\\s*" + regexpr + "\\s*"

    return re.compile(regexpr, flags=re.V1)
