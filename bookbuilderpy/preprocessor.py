"""The preprocessor commands to be applied once the text has been loaded."""
from typing import Callable, Optional, Final

import bookbuilderpy.constants as bc
from bookbuilderpy.git import Repo
from bookbuilderpy.path import Path
from bookbuilderpy.preprocessor_code import get_programming_language, \
    load_code
from bookbuilderpy.preprocessor_commands import create_preprocessor
from bookbuilderpy.strings import enforce_non_empty_str


def preprocess(text: str,
               input_dir: str,
               get_meta: Callable,
               get_repo: Callable,
               repo: Optional[Repo],
               output_dir: str) -> str:
    """
    Apply all the preprocessor commands to the given text.

    :param str text: the text of the book to be preprocessed.
    :param str input_dir: the input director
    :param Callable get_meta: a command for obtaining meta information.
    :param Callable get_repo: a command for obtaining a repository
    :param Optional[Repo] repo: the root repository of the project
    :param str output_dir: the output directory
    """
    src = Path.directory(input_dir)
    dst = Path.directory(output_dir)
    src.enforce_neither_contains(dst)

    # flatten all meta-data commands
    text = (create_preprocessor(name=bc.CMD_GET_META,
                                func=get_meta,
                                n=1,
                                strip_white_space=False))(text)

    # create all figures
    def __make_absolute_figure(label: str,
                               caption: str,
                               path: str,
                               args: str,
                               _src: Path = src,
                               _dst: Path = dst) -> str:
        new_path = Path.copy_resource(_src, path, _dst)
        caption = enforce_non_empty_str(caption.strip())
        use_path = enforce_non_empty_str(new_path.relative_to(_dst).strip())
        cmd = enforce_non_empty_str(" ".join([enforce_non_empty_str(
            label.strip()), args.strip()]).strip())
        return f"![{caption}]({use_path}){{#fig:{cmd}}}"

    text = (create_preprocessor(name=bc.CMD_ABSOLUTE_FIGURE,
                                func=__make_absolute_figure,
                                n=4, strip_white_space=True,
                                wrap_in_newlines=2))(text)

    # make a code section
    def __make_code(label: str, caption: str, code: str, file: Path,
                    userepo: Optional[Repo]) -> str:
        code = enforce_non_empty_str(code.strip())
        label = enforce_non_empty_str(label.strip())
        code = enforce_non_empty_str(code.strip())
        plang: Optional[str] = get_programming_language(file)
        plang = "" if plang is None else f" .{plang}"

        caption = enforce_non_empty_str(caption.strip())
        if caption[len(caption) - 1] not in [".", "!", "?"]:
            caption = f"{caption}."
        if userepo is not None:
            userepo.path.enforce_contains(file)
            url = userepo.make_url(file.relative_to(userepo.path))
            caption = f"{caption} ([src]({url}))"

        return f"Listing: {caption}\n\n" \
               f"```{{#lst:{label}{plang} .numberLines}}\n{code}\n```"

    # create all local code
    def __make_absolute_code(label: str, caption: str, path: str, lines: str,
                             labels: str, args: str, _src: Path = src) -> str:
        file: Final[Path] = Path.file(path)
        _src.enforce_contains(file)
        code = load_code(file, lines=lines, labels=labels, args=args)
        return __make_code(label=label, caption=caption,
                           code=code, file=file, userepo=repo)

    text = (create_preprocessor(name=bc.CMD_ABSOLUTE_CODE,
                                func=__make_absolute_code,
                                n=6, strip_white_space=True,
                                wrap_in_newlines=2))(text)

    # create all git code
    def __make_git_code(repoid: str, label: str, caption: str, path: str,
                        lines: str, labels: str, args: str) -> str:
        userepo: Final[Repo] = get_repo(repoid)
        file: Final[Path] = userepo.path.resolve_inside(path)
        file.enforce_file()
        userepo.path.enforce_contains(file)
        code = load_code(file, lines=lines, labels=labels, args=args)
        return __make_code(label=label, caption=caption,
                           code=code, file=file, userepo=userepo)

    text = (create_preprocessor(name=bc.CMD_GIT_CODE,
                                func=__make_git_code,
                                n=7, strip_white_space=True,
                                wrap_in_newlines=2))(text)
    return text
