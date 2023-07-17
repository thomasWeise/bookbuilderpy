"""Test the interaction with the file system."""

from bookbuilderpy.source_tools import format_empty_lines, select_lines


def test_select_lines_1() -> None:
    """Test other tools."""
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


def test_select_lines_2() -> None:
    """Test other tools."""
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


def test_select_lines_3() -> None:
    """Test other tools."""
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


def test_select_lines_4() -> None:
    """Test other tools."""
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


def test_select_lines_5() -> None:
    """Test other tools."""
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


def test_format_empty_lines() -> None:
    """Test other tools."""
    code = ["", "a", "", "b", "", "", "c", "", "", "", "d", "e", ""]
    assert format_empty_lines(code, max_consecutive_empty_lines=3) == \
           ["a", "", "b", "", "", "c", "", "", "", "d", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=2) == \
           ["a", "", "b", "", "", "c", "", "", "d", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=1) == \
           ["a", "", "b", "", "c", "", "d", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=0) == \
           ["a", "b", "c", "d", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=2,
                              no_empty_after=lambda s: s == "b") == \
           ["a", "", "b", "c", "", "", "d", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=2,
                              no_empty_after=lambda s: s == "b",
                              empty_before=lambda s: s == "e") == \
           ["a", "", "b", "c", "", "", "d", "", "e"]
    assert format_empty_lines(code, max_consecutive_empty_lines=2,
                              no_empty_after=lambda s: s == "b",
                              empty_before=lambda s: s == "e",
                              force_no_empty_after=lambda s: s == "d") == \
           ["a", "", "b", "c", "", "", "d", "e"]


be = """
\"\"\"Here we provide a representation for JSSP instances.\"\"\"
from importlib import resources
from typing import Final, List, Tuple, Optional

# start book
class Instance(Component):
    \"\"\"An instance of the Job Shop Scheduling Problem.\"\"\"

    def __init__(self, name: str, machines: int, jobs: int,
                 matrix: np.ndarray,
                 makespan_lower_bound: Optional[int] = None) -> None:
        \"\"\"
        Create an instance of the Job Shop Scheduling Problem.

        :param str name: the name of the instance
        \"\"\"
        #: The name of this JSSP instance.
        self.name: Final[str] = logging.sanitize_name(name)
        # end book

        if name != self.name:
            raise ValueError(f"Name '{name}' is not a valid name.")

        self.machines: Final[int] = machines  # +book

        #: The number of jobs in this JSSP instance.
        self.jobs: Final[int] = jobs  # +book

        #: consecutive sequence, i.e., 2*machine numbers.
        self.matrix: Final[np.ndarray] = matrix  # +book

        #: The lower bound of the makespan for the JSSP instance.
        self.makespan_lower_bound: Final[int] = makespan_lower_bound  # +book
"""

bex = """
class Instance(Component):
    \"\"\"An instance of the Job Shop Scheduling Problem.\"\"\"

    def __init__(self, name: str, machines: int, jobs: int,
                 matrix: np.ndarray,
                 makespan_lower_bound: Optional[int] = None) -> None:
        \"\"\"
        Create an instance of the Job Shop Scheduling Problem.

        :param str name: the name of the instance
        \"\"\"
        #: The name of this JSSP instance.
        self.name: Final[str] = logging.sanitize_name(name)
        self.machines: Final[int] = machines
        self.jobs: Final[int] = jobs
        self.matrix: Final[np.ndarray] = matrix
        self.makespan_lower_bound: Final[int] = makespan_lower_bound
"""


def test_select_lines_6() -> None:
    """Test other tools."""
    code = be.splitlines()
    result = select_lines(code, labels=["book"])
    exp = bex.strip().splitlines()
    assert result == exp
