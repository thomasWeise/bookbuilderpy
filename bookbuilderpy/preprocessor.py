"""The preprocessor commands to be applied once the text has been loaded."""
from typing import Callable, Optional, Final, Dict

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

    :param text: the text of the book to be preprocessed.
    :param input_dir: the input director
    :param get_meta: a command for obtaining meta information.
    :param get_repo: a command for obtaining a repository
    :param repo: the root repository of the project
    :param output_dir: the output directory
    """
    src = Path.directory(input_dir)
    dst = Path.directory(output_dir)
    src.enforce_neither_contains(dst)

    # execute all meta-data commands
    text = (create_preprocessor(name=bc.CMD_GET_META,
                                func=get_meta,
                                n=1,
                                strip_white_space=False))(text)

    def __get_repo(repo_id, info_id) -> str:
        gitrepo: Final[Repo] = get_repo(repo_id)
        if info_id == bc.META_REPO_INFO_URL:
            return gitrepo.get_base_url()
        if info_id == bc.META_REPO_INFO_DATE:
            return gitrepo.date_time
        if info_id == bc.META_REPO_INFO_COMMIT:
            return gitrepo.commit
        if info_id == bc.META_REPO_INFO_NAME:
            return gitrepo.get_name()
        raise ValueError(
            f"Invalid repo query '{info_id}' for repo '{repo_id}'.")

    # execute all repo-info commands
    text = (create_preprocessor(name=bc.CMD_GET_REPO,
                                func=__get_repo,
                                n=2,
                                strip_white_space=False))(text)

    # make the definitions
    def_map: Dict[str, str] = {}
    def_count: Dict[str, int] = {}

    def __make_def(deftype: str,
                   label: str,
                   body: str) -> str:
        nonlocal def_map
        nonlocal def_count
        prefix = enforce_non_empty_str(get_meta(f"{deftype}Title").strip())
        count: int = def_count.get(deftype, 0) + 1
        def_count[deftype] = count
        anchor = f"{prefix}&nbsp;{count}"
        enforce_non_empty_str(label)
        if label in def_map:
            raise ValueError(
                f"Redefined label '{label}' of type '{deftype}'.")
        label_name = f"_def:{count}:{label}"
        def_map[label] = f"[{anchor}](#{label_name})"
        enforce_non_empty_str(body)
        return f"<div id=\"{label_name}\">**{anchor}.**&nbsp;{body}</div>"

    text = (create_preprocessor(name=bc.CMD_DEFINITION,
                                func=__make_def,
                                n=3,
                                strip_white_space=True,
                                wrap_in_newlines=3))(text)
    del def_count, __make_def

    text = (create_preprocessor(name=bc.CMD_DEF_REF,
                                func=def_map.__getitem__,
                                n=1,
                                strip_white_space=False))(text)
    del def_map

    # create all figures
    def __make_absolute_figure(label: str,
                               caption: str,
                               path: str,
                               args: str) -> str:
        nonlocal src
        nonlocal dst
        new_path = Path.copy_resource(src, path, dst)
        caption = enforce_non_empty_str(caption.strip())
        use_path = enforce_non_empty_str(new_path.relative_to(dst).strip())
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
        spacer = " "
        end = caption[len(caption) - 1]
        # Below, we check first whether the text ends in a Chinese punctuation
        # mark and if it does not, if it ends in a Western one.
        if end in "\u3001\u3002\u3003\u3009\u300b\u300d\u3011\u3015\u3017" \
                  "\u3019\u301b\u301e\ufe16\ufe57\uff01\uff1f\uff61\uff64":
            spacer = ""
        elif end not in ".;!?)]}\"'\u00a1\u00b7\u00bf\u037e\u0387":
            caption = f"{caption}."
        if userepo:
            userepo.path.enforce_contains(file)
            url = userepo.make_url(file.relative_to(userepo.path))
            caption = f"{caption}{spacer}([src]({url}))"

        return f"Listing: {caption}\n\n" \
               f"```{{#lst:{label}{plang} .numberLines}}\n{code}\n```"

    # create all local code
    def __make_absolute_code(label: str, caption: str, path: str, lines: str,
                             labels: str, args: str) -> str:
        nonlocal src
        file: Final[Path] = Path.file(path)
        src.enforce_contains(file)
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
