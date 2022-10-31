"""In this file, we put some shared tools for rendering source codes."""

import sys
from typing import Optional, List, Iterable, Set, Callable

from bookbuilderpy.types import type_error


def select_lines(code: Iterable[str],
                 lines: Optional[Iterable[int]] = None,
                 labels: Optional[Iterable[str]] = None,
                 line_comment_start: str = "#",
                 max_consecutive_empty_lines: int = 1) -> List[str]:
    r"""
    Select lines of source code based on labels and line indices.

    First, we select all lines of the code we want to keep.
    If labels are defined, then lines are kept as ranges or as single lines
    for all pre-defined labels. Ranges may overlap and/or intersect.
    Otherwise, all lines are selected in this step.

    Then, if line numbers are provided, we selected the lines based on the
    line numbers from the lines we have preserved.

    Finally, leading and trailing empty lines as well as superfluous empty
    lines are removed.

    :param code: the code loaded from a file
    :param lines: the lines to keep, or `None` if we keep all
    :param labels: a list of labels marking start and
        end of code snippets to include
    :param line_comment_start: the string marking the line comment start
    :param max_consecutive_empty_lines: the maximum number of permitted
        consecutive empty lines
    :return: the list of selected lines

    >>> select_lines(["def a():", "    b=c", "    return x"])
    ['def a():', '    b=c', '    return x']
    >>> pc = ["# start x", "def a():", " b=c # -x", "    return x", "# end x"]
    >>> select_lines(pc, labels={"x"})
    ['def a():', '    return x']
    """
    if not isinstance(code, Iterable):
        raise type_error(code, "code", Iterable)
    if not isinstance(max_consecutive_empty_lines, int):
        raise type_error(
            max_consecutive_empty_lines, "max_consecutive_empty_lines", int)
    if max_consecutive_empty_lines < 0:
        raise ValueError("max_consecutive_empty_lines must be >= 0, but is "
                         f"{max_consecutive_empty_lines}.")
    if not isinstance(line_comment_start, str):
        raise type_error(line_comment_start, "line_comment_start", str)
    if not line_comment_start:
        raise ValueError("line_comment_start cannot be "
                         f"'{line_comment_start}'.")

    keep_lines: List[str]

    # make sure that labels are unique and non-empty
    label_str: Optional[List[str]] = None
    if labels is not None:
        if not isinstance(labels, Iterable):
            raise type_error(labels, "labels", Iterable)
        label_lst = list(labels)
        label_lst.sort()
        label_str = list({label.strip() for label in label_lst})
        label_str.sort()
        if label_lst != label_str:
            raise ValueError(
                f"Invalid label spec {label_lst} of length {len(label_lst)},"
                f" leading to unique label set {label_str} of length "
                f"{len(label_str)}.")
        del label_lst
        if label_str and not (label_str[0]):
            raise ValueError(f"Empty label in {labels}.")

    # process all labels, if any are specified
    if label_str:
        keep_lines = []

        start_labels = [f"{line_comment_start} start {label}"
                        for label in label_str]
        end_labels = [f"{line_comment_start} end {label}"
                      for label in label_str]
        add_labels = [f"{line_comment_start} +{label}" for label in label_str]
        del_labels = [f"{line_comment_start} -{label}" for label in label_str]
        all_labels = set(start_labels + end_labels + add_labels + del_labels)
        if len(all_labels) != (4 * len(label_str)):
            raise ValueError("label clash? impossible?")
        del all_labels

        active_labels: Set[int] = set()  # the active label ranges
        current_line_labels: Set[int] = set()  # labels of the current line
        done_labels: Set[int] = set()  # the labes for which text as retained

        for line, cl in enumerate(code):  # iterate over all code lines
            cl = cl.rstrip()

            # first, we need to update the state
            current_line_labels.clear()
            current_line_labels.update(active_labels)
            found_mark: bool = True
            while found_mark:
                found_mark = False

                # check all potential range starts
                for i, lbl in enumerate(start_labels):
                    if cl.endswith(lbl):
                        cl = cl[:len(cl) - len(lbl)].rstrip()
                        if i in active_labels:
                            raise ValueError(
                                f"Label '{label_str[i]}' already active in "
                                f"line {line} with text '{cl}', cannot "
                                "start.")
                        active_labels.add(i)
                        found_mark = True

                # check all potential range end
                for i, lbl in enumerate(end_labels):
                    if cl.endswith(lbl):
                        cl = cl[:len(cl) - len(lbl)].rstrip()
                        if i not in active_labels:
                            raise ValueError(
                                f"Label '{label_str[i]}' not active in "
                                f"line {line} with text '{cl}', cannot "
                                "end.")
                        active_labels.remove(i)
                        current_line_labels.remove(i)
                        found_mark = True

                # check all potential line add labels
                for i, lbl in enumerate(add_labels):
                    if cl.endswith(lbl):
                        cl = cl[:len(cl) - len(lbl)].rstrip()
                        if i in current_line_labels:
                            raise ValueError(
                                f"Label '{label_str[i]}' already active in "
                                f"line {line} with text '{cl}', cannot "
                                "add.")
                        current_line_labels.add(i)
                        found_mark = True

                # check all potential line deletion markers
                for i, lbl in enumerate(del_labels):
                    if cl.endswith(lbl):
                        cl = cl[:len(cl) - len(lbl)].rstrip()
                        if i not in current_line_labels:
                            raise ValueError(
                                f"Label '{label_str[i]}' already active in "
                                f"line {line} with text '{cl}', cannot "
                                "delete.")
                        current_line_labels.remove(i)
                        found_mark = True
                        break
                if found_mark:
                    continue

            if current_line_labels:
                keep_lines.append(cl)
                done_labels.update(current_line_labels)

        if not keep_lines:
            raise ValueError(
                f"Nothing is left over after applying labels {labels}.")
        if len(done_labels) < len(label_str):
            raise ValueError(
                "Never had any text for labels "
                f"{set(label_str).difference(done_labels)}.")
    else:
        keep_lines = [cl.rstrip() for cl in code]

    if lines is not None:  # select the lines we want to keep
        if not isinstance(lines, Iterable):
            raise type_error(lines, "lines", Iterable)
        lines_ints = list(set(lines))
        if not lines_ints:
            raise ValueError(f"Empty lines provided: {lines}.")
        lines_ints.sort()
        keep_lines = [keep_lines[i] for i in lines_ints]

    # remove leading empty lines
    while keep_lines:
        if not keep_lines[0]:
            del keep_lines[0]
        else:
            break

    # remove trailing empty lines
    while keep_lines:
        if not keep_lines[-1]:
            del keep_lines[-1]
        else:
            break

    # remove superfluous empty lines
    empty_lines = 0
    current = len(keep_lines)
    while current > 0:
        current -= 1
        if keep_lines[current]:
            empty_lines = 0
        else:
            if empty_lines >= max_consecutive_empty_lines:
                del keep_lines[current]
            else:
                empty_lines += 1

    if not keep_lines:
        raise ValueError(f"Empty code resulting from {code} after applying "
                         f"labels {labels} and lines {lines}.?")

    return keep_lines


def format_empty_lines(lines: Iterable[str],
                       empty_before: Callable = lambda line: False,
                       no_empty_after: Callable = lambda line: False,
                       force_no_empty_after: Callable = lambda line: False,
                       max_consecutive_empty_lines: int = 1) -> List[str]:
    """
    Obtain a generator that strips any consecutive empty lines.

    :param lines: the original line iterable
    :param empty_before: a function checking whether an empty line
        is required before a certain string
    :param no_empty_after: a function checking whether an empty line
        is prohibited after a string
    :param force_no_empty_after: a function checking whether an empty
        line is prohibited after a string
    :param max_consecutive_empty_lines: the maximum number of permitted
        consecutive empty lines
    :return: the generation

    >>> code = ["", "a", "", "b", "", "", "c", "", "", "", "d", "e", ""]
    >>> format_empty_lines(code, max_consecutive_empty_lines=3)
    ['a', '', 'b', '', '', 'c', '', '', '', 'd', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=2)
    ['a', '', 'b', '', '', 'c', '', '', 'd', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=1)
    ['a', '', 'b', '', 'c', '', 'd', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=0)
    ['a', 'b', 'c', 'd', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=2,
    ...                    no_empty_after=lambda s: s == "b")
    ['a', '', 'b', 'c', '', '', 'd', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=2,
    ...                    no_empty_after=lambda s: s == "b",
    ...                    empty_before=lambda s: s == "e")
    ['a', '', 'b', 'c', '', '', 'd', '', 'e']
    >>> format_empty_lines(code, max_consecutive_empty_lines=2,
    ...                    no_empty_after=lambda s: s == "b",
    ...                    empty_before=lambda s: s == "e",
    ...                    force_no_empty_after=lambda s: s == "d")
    ['a', '', 'b', 'c', '', '', 'd', 'e']
    """
    if not isinstance(max_consecutive_empty_lines, int):
        raise type_error(
            max_consecutive_empty_lines, "max_consecutive_empty_lines", int)
    if max_consecutive_empty_lines < 0:
        raise ValueError("max_consecutive_empty_lines must be >= 0, but is "
                         f"{max_consecutive_empty_lines}.")
    if not callable(empty_before):
        raise type_error(empty_before, "empty_before", call=True)
    if not callable(no_empty_after):
        raise type_error(no_empty_after, "no_empty_after", call=True)
    if not callable(force_no_empty_after):
        raise type_error(
            force_no_empty_after, "force_no_empty_after", call=True)

    result: List[str] = []
    print_empty: int = 0
    no_empty = True
    force_no_empty = True
    for line in lines:
        line = line.rstrip()
        ltr = line.lstrip()

        if line:
            if (not force_no_empty) \
                    and (empty_before(ltr)
                         or ((print_empty > 0)
                             and (max_consecutive_empty_lines > 0))):
                result.extend([""] * max(1, min(print_empty,
                                                max_consecutive_empty_lines)))
            no_empty = no_empty_after(ltr)
            force_no_empty = force_no_empty_after(ltr)
            result.append(line)
            print_empty = 0
            continue

        if force_no_empty or no_empty:
            continue

        print_empty += 1

    if not result:
        raise ValueError("No lines of text found.")
    return result


def strip_common_whitespace_prefix(lines: Iterable[str]) -> List[str]:
    r"""
    Strip a common whitespace prefix from a list of strings and merge them.

    :param lines: the lines
    :return: the code with the white space prefix stripped

    >>> strip_common_whitespace_prefix([" a", "  b"])
    ['a', ' b']
    >>> strip_common_whitespace_prefix([" a", " b"])
    ['a', 'b']
    >>> strip_common_whitespace_prefix(["  a", "  b"])
    ['a', 'b']
    >>> strip_common_whitespace_prefix(["  a", "  b", "c"])
    ['  a', '  b', 'c']
    >>> strip_common_whitespace_prefix([" a", "  b", "c"])
    [' a', '  b', 'c']
    >>> strip_common_whitespace_prefix(["  a", "  b", "    c"])
    ['a', 'b', '  c']
    """
    prefix_len = sys.maxsize
    for line in lines:
        ll = len(line)
        if ll <= 0:
            continue
        for k in range(min(ll, prefix_len)):
            if line[k] != " ":
                prefix_len = k
                break
    if prefix_len > 0:
        return [line[prefix_len:] for line in lines]
    return list(lines)
