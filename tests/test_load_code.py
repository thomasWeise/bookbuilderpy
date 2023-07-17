"""Test the interaction with the file system."""
from os.path import dirname

from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_code import load_code
from bookbuilderpy.temp import TempFile


# start test
def test_load_code_1() -> None:
    """Test load code 1."""
    result = load_code(__file__, "1-3,6", "test", "doc,comments,hints")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: list[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) >= 5  # the original length is 5
    assert len(res) <= 6  # but a line break may be inserted
    assert res[0] == "def test_load_code_1() -> None:"
    assert res[-1] == ""
    assert res[-2] == '    nl = "\\n"'


# end test

# start test2
def test_load_code_2() -> None:
    """Test load code 2."""
    result = load_code(__file__, "1-3,6", "test2", "doc,comments")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: list[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) >= 5  # the original length is 5
    assert len(res) <= 6  # but a line break may be inserted
    assert res[0] == "def test_load_code_2():"
    assert res[-1] == ""
    assert res[-2] == '    nl = "\\n"'


# end test2

# start test3
def test_load_code_3() -> None:
    """Here we test the code."""
    result = load_code(__file__, "1-4,7", "test3", "comments")
    assert isinstance(result, str)
    assert len(result) > 0
    nl = "\n"
    res: list[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) >= 5  # the original length is 5
    assert len(res) <= 6  # but a line break may be inserted
    assert res[0] == "def test_load_code_3():"
    assert res[-1] == ""
    assert res[-2] == \
           "    res = [s.rstrip() for s in result.split(nl)]"


# end test3

# start test4
def test_load_code_4() -> None:  # this is a comment
    """Here we test the code."""
    result = load_code(__file__, "1-4,7", "test4", "")
    assert isinstance(result, str)  # this is removed
    assert len(result) > 0
    nl = "\n"
    res: list[str] = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 5
    assert res[0] == "def test_load_code_4():"
    assert res[2] == "    assert isinstance(result, str)"
    assert res[-1] == ""
    assert res[-2] == \
           "    res = [s.rstrip() for s in result.split(nl)]"
# end test4


# start test5
def test_load_code_56() -> None:  # this is a comment
    """Here we test the code."""
    result = load_code(__file__, "", "test5", "")
# end test5
# start test6
    assert isinstance(result, str)  # this is removed
    assert len(result) > 0
# end test6
    # start test5
    nl = "\n"
    res: list[str] = [s.rstrip() for s in result.split(nl)]
    # end test5
    assert len(res) == 5
    assert res[0] == "def test_load_code_56():"
    assert res[1] == '    result = load_code(__file__, "", "test5", "")'
    assert res[2] == '    nl = "\\n"'
    assert res[3] == "    res = [s.rstrip() for s in result.split(nl)]"
    assert res[4] == ""
    result = load_code(__file__, "", "test6", "")
    assert isinstance(result, str)  # this is removed
    assert len(result) > 0
    res = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 3
    assert res[0] == "assert isinstance(result, str)"
    assert res[1] == "assert len(result) > 0"
    assert res[2] == ""
    result = load_code(__file__, "", "test5,test6", "")
    assert isinstance(result, str)  # this is removed
    assert len(result) > 0
    res = [s.rstrip() for s in result.split(nl)]
    assert len(res) == 7
    assert res[0] == "def test_load_code_56():"
    assert res[1] == '    result = load_code(__file__, "", "test5", "")'
    assert res[2] == "    assert isinstance(result, str)"
    assert res[3] == "    assert len(result) > 0"
    assert res[4] == '    nl = "\\n"'
    assert res[5] == "    res = [s.rstrip() for s in result.split(nl)]"
    assert res[6] == ""


def test_load_from_text() -> None:
    """Load code from a text file."""
    source = Path.directory(dirname(__file__)).resolve_inside(
        "__code_load_example_ea.txt")
    text = source.read_all_str()
    assert isinstance(text, str)
    assert len(text) > 0

    with TempFile.create(suffix=".py") as tf:
        tf.write_all(text)

        result = load_code(tf, "", "nobinary", "")
        assert isinstance(result, str)
        assert len(result) > 0
        nl = "\n"
        res: list[str] = [s.rstrip() for s in result.split(nl)]
        lines_nb: int = len(res)
        assert lines_nb > 0

        result = load_code(tf, "", "binary", "")
        assert isinstance(result, str)
        assert len(result) > 0
        nl = "\n"
        res: list[str] = [s.rstrip() for s in result.split(nl)]
        lines_b: int = len(res)
        assert 0 < lines_b < lines_nb

        result = load_code(tf, "", "binary,nobinary", "")
        assert isinstance(result, str)
        assert len(result) > 0
        nl = "\n"
        res: list[str] = [s.rstrip() for s in result.split(nl)]
        lines_all: int = len(res)
        assert 0 < (lines_b + lines_nb - 1) <= lines_all \
               <= (lines_b + lines_nb + 1)

        result2 = load_code(tf, "", "nobinary,binary", "")
        assert result2 == result
