"""Test the interaction with the file system."""
from typing import List

from bookbuilderpy.preprocessor_code import load_code


# noinspection PyPackageRequirements
# start test
def test_load_code_1():
    result = load_code(__file__, "1-3,6", "test", "doc,comments,hints")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: List[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 5
    assert res[0] == "def test_load_code_1():"
    assert res[-1] == ""
    assert res[-2] == \
           '    res: List[str] = [s.rstrip() for s in result.split(nl)]'


# end test

# start test2
def test_load_code_2():
    result = load_code(__file__, "1-3,6", "test2", "doc,comments")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: List[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 5
    assert res[0] == "def test_load_code_2():"
    assert res[-1] == ""
    assert res[-2] == \
           '    res = [s.rstrip() for s in result.split(nl)]'


# end test2

# start test3
def test_load_code_3():
    """Here we test the code."""
    result = load_code(__file__, "1-4,7", "test3", "comments")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: List[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 5
    assert res[0] == "def test_load_code_3():"
    assert res[-1] == ""
    assert res[-2] == \
           '    res = [s.rstrip() for s in result.split(nl)]'


# end test3

# start test4
def test_load_code_4():  # this is a comment
    """Here we test the code."""
    result = load_code(__file__, "1-4,7", "test4", "")
    assert isinstance(result, str)  # this is removed
    assert len(result) > 0
    nl = "\n"
    res: List[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 5
    assert res[0] == "def test_load_code_4():"
    assert res[2] == "    assert isinstance(result, str)"
    assert res[-1] == ""
    assert res[-2] == \
           '    res = [s.rstrip() for s in result.split(nl)]'
# end test4
