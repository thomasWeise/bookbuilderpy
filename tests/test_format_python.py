"""Test the interaction with the file system."""

from typing import Tuple

from bookbuilderpy.format_python import format_python, preprocess_python, \
    select_lines


# noinspection PyPackageRequirements

def test_format_python_1():
    s = ["",
         "    def solve(self, process: Process) -> None:",
         "        \"\"\"",
         "        Apply the hill climber to the given black-box process.",
         "",
         "        :param moptipy.api.Process process: the process object",
         "        \"\"\"",
         "        best_x: Final = process.create()",
         "        new_x: Final = process.create()",
         "        random: Final[Generator] = process.get_random()",
         "",
         "        best_f: Union[int, float]",
         "        if process.has_current_best(): # blabla",
         "            process.get_copy_of_current_best_x(best_x)",
         "            best_f = process.get_current_best_f()",
         "        else:",
         "            self.op0.op0(random, best_x)",
         "            best_f = process.evaluate(best_x)",
         "",
         "        while not process.should_terminate():",
         "            self.op1.op1(random, ",
         "            best_x, ",
         "            new_x)",
         "            new_f: Union[int, float] = process.evaluate(new_x)",
         "            if new_f < best_f:",
         "                best_f = new_f",
         "                process.copy(new_x, ",
         "                best_x)",
         "    @staticmethod",
         "    def get_name(self) -> str:",
         "        \"\"\"",
         "        Get the name of this hill climber.",
         "",
         "        :return: \"hc\" + any non-standard operator suffixes",
         "        :rtype: str",
         "        \"\"\"",
         "        name: Final[str] = super().get_name()",
         "        return f\"hc_{name}\" if (len(name) > 0) else \"hc\""]
    ret = format_python(s)
    assert isinstance(ret, Tuple)

    t = ("def solve(self, process):",
         "    best_x = process.create()",
         "    new_x = process.create()",
         "    random = process.get_random()",
         "",
         "    if process.has_current_best():",
         "        process.get_copy_of_current_best_x(best_x)",
         "        best_f = process.get_current_best_f()",
         "    else:",
         "        self.op0.op0(random, best_x)",
         "        best_f = process.evaluate(best_x)",
         "",
         "    while not process.should_terminate():",
         "        self.op1.op1(random, best_x, new_x)",
         "        new_f = process.evaluate(new_x)",
         "        if new_f < best_f:",
         "            best_f = new_f",
         "            process.copy(new_x, best_x)",
         "",
         "@staticmethod",
         "def get_name(self):",
         "    name = super().get_name()",
         "    return f\"hc_{name}\" if (len(name) > 0) else \"hc\"")
    assert ret == t

    ret2 = preprocess_python(s)
    assert ret2 == ("\n".join(t) + "\n")


def test_format_python_2():
    code = ["# start book",
            "def test_func() -> None:",
            "    a = 12",
            "    b = 13 # -book",
            "    # end book",
            "    c = 23",
            "    # start book",
            "    d = 64",
            "    e = 128",
            "    # end book",
            "    f = 11",
            "    g = 23  # +book",
            "    h = 24",
            "    return a + b"]
    expected = ["def test_func():",
                "    a = 12",
                "    d = 64",
                "    e = 128",
                "    g = 23"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["book"])

    assert result == merged


def test_format_python_3():
    code = ["a = 5",
            "# start x",
            "b = 7",
            "# end x",
            "c = 8",
            "# start x",
            "d = 9",
            "# end x",
            "e = 10"]
    expected = ["b = 7",
                "d = 9"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["x"])
    assert result == merged


def test_format_python_4():
    code = ["# start y",
            "def cyber():",
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2"]
    expected = ["def cyber():",
                "    a = 1"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["y"])
    assert result == merged


def test_format_python_5():
    code = ["# start y",
            "def cyber():",
            '    """',
            "    This method does cyber",
            '    """',
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2"]
    expected = ["def cyber():",
                "    a = 1"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["y"])
    assert result == merged


def test_format_python_6():
    code = ["b = 2",
            "# start y",
            "c = 3",
            "# end y",
            "d = 4",
            "# start y",
            "# this is a comment",
            "e = 5",
            "# end y",
            "f = 6"]
    expected = ["c = 3",
                "e = 5"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["y"])
    assert result == merged


def test_format_python_7():
    code = ["# start y",
            "def cyber():",
            '    """',
            "    This method does cyber",
            '    """',
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2",
            "    # start y",
            "    c = 3",
            "    # end y",
            "    d = 4",
            "    # start y",
            "    # this is a comment",
            "    e = 5",
            "    # end y",
            "    f = 6"]
    expected = ["def cyber():",
                "    a = 1",
                "    c = 3",
                "    e = 5"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code, labels=["y"])
    assert result == merged


def test_format_python_8():
    code = ["def cyber():",
            '    """',
            "    This method does cyber",
            '    """',
            "    #: this is a comment",
            "    a = 1",
            "    b = 2"]
    expected = ["def cyber():",
                "    a = 1",
                "    b = 2"]
    merged = "\n".join(expected) + "\n"
    result = preprocess_python(code)
    assert result == merged


def test_select_lines_4():
    code = ["# start y",
            "def cyber():",
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2"]
    expected = ["def cyber():",
                "    #: this is a comment",
                "    a = 1"]
    result = select_lines(code, labels=["y"])
    assert result == expected


def test_select_lines_5():
    code = ["# start y",
            "def cyber():",
            '    """',
            "    This method does cyber",
            '    """',
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2"]
    expected = ["def cyber():",
                '    """',
                "    This method does cyber",
                '    """',
                "    #: this is a comment",
                "    a = 1"]
    result = select_lines(code, labels=["y"])
    assert result == expected


def test_select_lines_6():
    code = ["b = 2",
            "# start y",
            "c = 3",
            "# end y",
            "d = 4",
            "# start y",
            "# this is a comment",
            "e = 5",
            "# end y",
            "f = 6"]
    expected = ["c = 3",
                "# this is a comment",
                "e = 5"]
    result = select_lines(code, labels=["y"])
    assert result == expected


def test_select_lines_7():
    code = ["# start y",
            "def cyber():",
            '    """',
            "    This method does cyber",
            '    """',
            "    #: this is a comment",
            "    a = 1",
            "    # end y",
            "    b = 2",
            "    # start y",
            "    c = 3",
            "    # end y",
            "    d = 4",
            "    # start y",
            "    # this is a comment",
            "    e = 5",
            "    # end y",
            "    f = 6"]
    expected = ["def cyber():",
                '    """',
                "    This method does cyber",
                '    """',
                "    #: this is a comment",
                "    a = 1",
                "    c = 3",
                "    # this is a comment",
                "    e = 5"]
    result = select_lines(code, labels=["y"])
    assert result == expected
