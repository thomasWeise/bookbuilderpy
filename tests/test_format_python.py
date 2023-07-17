"""Test the interaction with the file system."""


from bookbuilderpy.format_python import format_python, preprocess_python


def test_format_python_1() -> None:
    """Test the python code formatting."""
    s = ["",
         "    def solve(self, process: Process) -> None:",
         '        """',
         "        Apply the hill climber to the given black-box process.",
         "",
         "        :param moptipy.api.Process process: the process object",
         '        """',
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
         '        """',
         "        Get the name of this hill climber.",
         "",
         '        :return: "hc" + any non-standard operator suffixes',
         "        :rtype: str",
         '        """',
         "        name: Final[str] = super().get_name()",
         '        return f"hc_{name}" if (len(name) > 0) else "hc"']
    ret = format_python(s)
    assert isinstance(ret, list)

    t = ["def solve(self, process):",
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
         '    return f"hc_{name}" if (len(name) > 0) else "hc"']
    assert ret == t

    ret2 = preprocess_python(s)
    assert ret2 == ("\n".join(t) + "\n")


def test_preprocess_python_1() -> None:
    """Test python preprocessing 1."""
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


def test_preprocess_python_2() -> None:
    """Test python preprocessing 2."""
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


def test_preprocess_python_3() -> None:
    """Test python preprocessing 3."""
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


def test_preprocess_python_4() -> None:
    """Test python preprocessing 4."""
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


def test_preprocess_python_5() -> None:
    """Test python preprocessing 5."""
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


def test_preprocess_python_6() -> None:
    """Test python preprocessing 6."""
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


def test_preprocess_python_7() -> None:
    """Test python preprocessing 7."""
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


bex1 = """
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


def test_preprocess_python_8() -> None:
    """Test python preprocessing 8."""
    code = be.splitlines()
    result = preprocess_python(code, labels=["book"],
                               args={"comments", "doc", "hints"})
    exp = bex1.strip() + "\n"
    assert result == exp


bex2 = """
class Instance(Component):
    def __init__(self, name: str, machines: int, jobs: int,
                 matrix: np.ndarray,
                 makespan_lower_bound: Optional[int] = None) -> None:
        #: The name of this JSSP instance.
        self.name: Final[str] = logging.sanitize_name(name)
        self.machines: Final[int] = machines
        self.jobs: Final[int] = jobs
        self.matrix: Final[np.ndarray] = matrix
        self.makespan_lower_bound: Final[int] = makespan_lower_bound
"""


def test_preprocess_python_9() -> None:
    """Test python preprocessing 9."""
    code = be.splitlines()
    result = preprocess_python(code, labels=["book"],
                               args={"comments", "hints"})
    exp = bex2.strip() + "\n"
    assert result == exp


bex3 = """
class Instance(Component):
    def __init__(self, name: str, machines: int, jobs: int,
                 matrix: np.ndarray,
                 makespan_lower_bound: Optional[int] = None) -> None:
        self.name: Final[str] = logging.sanitize_name(name)
        self.machines: Final[int] = machines
        self.jobs: Final[int] = jobs
        self.matrix: Final[np.ndarray] = matrix
        self.makespan_lower_bound: Final[int] = makespan_lower_bound
"""


def test_preprocess_python_10() -> None:
    """Test python preprocessing 10."""
    code = be.splitlines()
    result = preprocess_python(code, labels=["book"],
                               args={"hints"})
    exp = bex3.strip() + "\n"
    assert result == exp


bex4 = """
class Instance(Component):
    def __init__(self, name, machines, jobs, matrix,
                 makespan_lower_bound=None):
        #: The name of this JSSP instance.
        self.name = logging.sanitize_name(name)
        self.machines = machines
        self.jobs = jobs
        self.matrix = matrix
        self.makespan_lower_bound = makespan_lower_bound
"""


def test_preprocess_python_11() -> None:
    """Test python preprocessing 11."""
    code = be.splitlines()
    result = preprocess_python(code, labels=["book"],
                               args={"comments"})
    exp = bex4.strip() + "\n"
    assert result == exp


bex5 = """
class Instance(Component):
    def __init__(self, name, machines, jobs, matrix,
                 makespan_lower_bound=None):
        self.name = logging.sanitize_name(name)
        self.machines = machines
        self.jobs = jobs
        self.matrix = matrix
        self.makespan_lower_bound = makespan_lower_bound
"""


def test_preprocess_python_12() -> None:
    """Test python preprocessing 12."""
    code = be.splitlines()
    result = preprocess_python(code, labels=["book"])
    exp = bex5.strip() + "\n"
    assert result == exp
