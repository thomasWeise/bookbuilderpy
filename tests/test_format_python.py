"""Test the interaction with the file system."""

from typing import Tuple

from bookbuilderpy.format_python import format_python


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
