"""Regular-expression based command generation and invocation."""

from typing import Callable

import regex as reg  # type: ignore


def __create_command_re(name: str, n: int = 1,
                        strip_white_space: bool = False) -> reg.Regex:
    r"""
    Create a Regular Expression for a LaTeX-Style Command.

    A LaTeX-style command can be defined as an (recursive) regular expression.
    The start of the command is indicated by `\name`. It then has `n`
    arguments with `n>=0`. Each argument is wrapped into a `{` and a `}`.
    Example: `\sub{1}{2}`.

    Here we create a regular expression `cmd` that can match such a command.
    It can be applied to a string `s` using
    `sub(cmd, lambda g: g[1]+"-"+g[2], s)`, which would then return `{1}-{2}`
    for `s="\sub{1}{2}"`.

    Note that the expression will pass the curly braces of the arguments to
    the command which later need to be stripped away if necessary.

    :param str name: the name of the command
    :param int n: the number of parameters
    :param bool strip_white_space: should the white space around
        the command be stripped
    :return: a regular expression representing the command
    :rtype: re.Regex

    >>> cmd = __create_command_re("y", 2, False)
    >>> s = 'blabla\\y{1}{2}xaxa \\y{3}{4} zhdfg'
    >>> reg.sub(cmd, lambda g: g[1], s)
    'blabla{1}xaxa {3} zhdfg'
    >>> reg.sub(cmd, lambda g: g[2], s)
    'blabla{2}xaxa {4} zhdfg'
    >>> s = 'blabla\\y{\\y{1}{2}}{3} \\y{3}{4}.'
    >>> reg.sub(cmd, lambda g: g[1], s)
    'blabla{\\y{1}{2}} {3}.'
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
    >>> cmd = __create_command_re("sub", 2, True)
    >>> reg.sub(cmd, lambda g: g[1]+"-"+g[2], "a \sub{1}{2} b")
    'a{1}-{2}b'
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be string but is {type(name)}.")
    if len(name) <= 0:
        raise ValueError(f"name cannot be '{name}'.")
    if name in ("n", "r", "t", "x", "u"):
        raise ValueError(f"invalid command name: '{name}'.")
    if not isinstance(n, int):
        raise TypeError(f"n must be int, but is {type(n)}.")
    if n < 0:
        raise ValueError(f"n cannot be '{n}'.")
    if not isinstance(strip_white_space, bool):
        raise TypeError("strip_white_space must be int, "
                        f"but is {type(strip_white_space)}.")

    # First, we build the regular expression, which makes sure that braces
    # numbers match.

    # Create the command the name.
    regexpr: str = reg.escape(f"\\{name}")

    # Add the parameter groups.
    if n > 0:
        regexpr += "".join(
            ["".join([r"(\{(?>[^\{\}]|(?",
                      str(i + 1), r"))*+\})"])
             for i in range(n)])

    # Add potential whitespace strippers.
    if strip_white_space:
        regexpr = "\\s*" + regexpr + "\\s*"

    return reg.compile(regexpr, flags=reg.V1 | reg.MULTILINE)


def __strip_group(s: str) -> str:
    """
    Strip a possible surrounding `{}` pair and any inner white space.

    This is needed because the regular expressions returned by
    :meth:`__create_command_re` cannot strip the surrounding `{}` from the
    arguments. After the leading `{` and the trailing `}` are removed, the
    remaining string will be stripped of leading and trailing white space.

    :param str s: the input string
    :return: the sanitized string
    :rtype: str

    >>> __strip_group("{ f}")
    'f'
    >>> __strip_group("{x }")
    'x'
    """
    if not isinstance(s, str):
        raise TypeError(f"s should be str, but is {type(s)}.")
    if (len(s) <= 1) or (s[0] != '{') or (s[-1] != '}'):
        raise ValueError(f"invalid argument '{s}'.")
    return s[1:-1].strip()


def create_preprocessor(name: str,
                        func: Callable,
                        n: int = 1,
                        strip_white_space: bool = False) -> Callable:
    r"""
    Create a preprocessor command.

    A LaTeX-style command can be defined as an (recursive) regular expression.
    The start of the command is indicated by `\name`. It then has `n`
    arguments with `n>=0`. Each argument is wrapped into a `{` and a `}`.
    Example: `\sub{1}{2}`.

    This function returns a function `f` which can be applied an arbitrary
    string `s`. The function `f` will iteratively process all invocations
    of `name` that appear in `s`, pass the extracted parameter values to
    `func`, and replace the whole matched string with the return value of
    `func`.

    The command can appear nested in its arguments. In this case, the
    preprocessor `f` will resolve the inner-most occurences first.

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
    >>> cmd = create_preprocessor("mm", lambda: "Z", 0, True)
    >>> cmd("a\mm\mm\mmb")
    'aZZZb'
    >>> cmd = create_preprocessor("swp", lambda a, b: "("+b+","+a+")", 2)
    >>> cmd("\swp{1}{2}")
    '(2,1)'
    >>> cmd("\swp{\swp{1}{2}}{3}")
    '(3,(2,1))'
    >>> cmd("\swp{\swp{\swp{1}{2}}{3}}{\swp{4}{5}}")
    '((5,4),(3,(2,1)))'
    >>> cmd = create_preprocessor("y", lambda x: str(int(x)*2), 1)
    >>> cmd("12\y{3}4")
    '1264'
    """
    if not callable(func):
        raise TypeError(f"func must be callable, but is {type(func)}.")

    # Create the inner function that sanitizes the arguments and passes them on
    # to func.
    def __func(args, inner_n=n, inner_func=func) -> str:
        if inner_n == 0:
            ret = inner_func()
        else:
            groups = args.groups()
            if len(groups) != inner_n:
                raise ValueError(
                    f"Expected {inner_n} groups, got {len(groups)}.")
            ret = inner_func(*[__strip_group(g) for g in groups])
        if not isinstance(ret, str):
            raise TypeError(f"return value must be str, but is {type(ret)}.")
        return ret

    # Create the actual command function that can be invoked and that
    # recursively resolves all instances of the command name.
    def __cmd(s: str,
              regex=__create_command_re(
                  name=name, n=n, strip_white_space=strip_white_space),
              inner_func=__func) -> str:
        old = s
        while True:
            s = reg.sub(regex, inner_func, s)
            if s == old:
                return s
            old = s

    return __cmd
