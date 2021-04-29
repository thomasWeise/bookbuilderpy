"""Regular-expression based command generation and invocation."""

from typing import Callable

import regex as reg  # type: ignore


def __create_command_re(prefix: str, n: int = 1,
                        strip_white_space: bool = False) -> reg.Regex:
    r"""
    Create a Regular Expression for a LaTeX-Style Command.

    :param str prefix: the prefix of the command
    :param int n: the number of parameters
    :param bool strip_white_space: should the white space around
        the command be stripped
    :return: a regular expression representing the command
    :rtype: re.Regex

    >>> cmd = __create_command_re("x", 2, False)
    >>> s = 'blabla\\x{1}{2}xaxa \\x{3}{4} zhdfg'
    >>> reg.sub(cmd, lambda g: g[1], s)
    'blabla{1}xaxa {3} zhdfg'
    >>> reg.sub(cmd, lambda g: g[2], s)
    'blabla{2}xaxa {4} zhdfg'
    >>> s = 'blabla\\x{\\x{1}{2}}{3} \\x{3}{4}.'
    >>> reg.sub(cmd, lambda g: g[1], s)
    'blabla{\\x{1}{2}} {3}.'
    >>> reg.sub(cmd, lambda g: g[2], reg.sub(cmd, lambda g: g[1], s))
    'blabla{{2}} {3}.'
    >>> cmd = __create_command_re("y", 0, True)
    >>> reg.sub(cmd, "Z", "hello\n\\y  df")
    'helloZdf'
    >>> cmd = __create_command_re("z", 3, True)
    >>> reg.sub(cmd, lambda g: g[1]+g[3], "hello\n\\z{A x}{b k}{z}  df")
    'hello{A x}{z}df'
    >>> reg.sub(cmd, lambda g: g[1]+g[3], "hello\n\\z{{A x}}{b k}{z}  df")
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
    regexpr: str = reg.escape(f"\\{prefix}")

    # Add the parameter groups.
    if n > 0:
        regexpr += "".join(
            ["".join([r"(\{(?>[^\{\}]|(?",
                      str(i + 1), r"))*+\})"])
             for i in range(n)])

    # Add potential whitespace strippers.
    if strip_white_space:
        regexpr = "\\s*" + regexpr + "\\s*"

    return reg.compile(regexpr, flags=reg.V1)


def __strip_group(s: str) -> str:
    """
    Strip a possible surrounding '{}' pair and any inner white space.

    :param str s: the input string
    :return: the sanitized string
    :rtype: str

    >>> __strip_group("{ f}")
    'f'
    >>> __strip_group("  x ")
    'x'
    >>> __strip_group(" {x }")
    '{x }'
    """
    if not isinstance(s, str):
        raise TypeError(f"s should be str, but is {type(s)}.")
    if len(s) >= 1:
        if (s[0] == '{') and (s[-1] == '}'):
            s = s[1:-1]
    return s.strip()


def create_preprocessor(name: str,
                        func: Callable,
                        n: int = 1,
                        strip_white_space: bool = False) -> Callable:
    r"""
    Create a preprocessor command.

    :param str name: the command name
    :param Callable func: the function to call
    :param int n: the number of arguments to pass to func
    :param bool strip_white_space: should surrounding white space be stripped?
    :return: a function that can be invoked on a string and which replaces
        all the occurences of the command with the results of corresponding
        `func` invocations
    :rtype: Callable

    >>> f = lambda a, b: a + "-" + b
    >>> cmd = create_preprocessor("sub", f, 2)
    >>> cmd("x \sub{7}{3} y \sub{\sub{8}{5}}{\sub{4}{3}}")
    'x 7-3 y 8-5-4-3'
    """
    if not callable(func):
        raise TypeError(f"func must be callable, but is {type(func)}.")

    def __func(args, inner_n=n, inner_func=func) -> str:
        groups = args.groups()
        if len(groups) != inner_n:
            raise ValueError(f"Expected {inner_n} groups, got {len(groups)}.")
        ret = inner_func(*[__strip_group(g) for g in groups])
        if not isinstance(ret, str):
            raise TypeError(f"return value must be str, but is {type(ret)}.")
        return ret

    def __cmd(s: str,
              regex=__create_command_re(
                  prefix=name, n=n, strip_white_space=strip_white_space),
              inner_func=__func) -> str:
        old = s
        while True:
            s = reg.sub(regex, inner_func, s)
            if s == old:
                return s
            old = s

    return __cmd
