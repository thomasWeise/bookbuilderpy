"""Test the interaction with the file system."""

from bookbuilderpy.source_tools import select_lines


# noinspection PyPackageRequirements


def test_select_lines_1():
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


def test_select_lines_2():
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


def test_select_lines_3():
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


def test_select_lines_4():
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


def test_select_lines_5():
    code = ["# +x",
            "a = 5",
            "b = 6  # +x",
            " # start y",
            "c = 7",
            "d = 8  # -y",
            "e = 9",
            "# end y",
            "f = 10"]
    expected = ["b = 6",
                "c = 7",
                "e = 9"]
    result = select_lines(code, labels=["x", "y"])
    assert result == expected
