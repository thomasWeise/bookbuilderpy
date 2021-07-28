"""Test the interaction with the build system with random data."""
import os
import os.path
import pathlib
import random
import shutil
import struct
import zlib
from tempfile import mkstemp
from typing import Final, Tuple, List, Optional, cast, Set

import bookbuilderpy.constants as bc
from bookbuilderpy.build import Build
from bookbuilderpy.git import Repo
from bookbuilderpy.temp import Path
from bookbuilderpy.temp import TempDir

#: the list of repositories to use for testing
REPO_LIST: Final[Tuple[Tuple[str, str], ...]] = (
    ("bb", "https://github.com/thomasWeise/bookbuilderpy.git"),
    ("mp", "https://github.com/thomasWeise/moptipy.git"))

#: the list of languages
LANG_LIST: Final[Tuple[Tuple[str, str], ...]] = (
    ("en", "English"),
    ("zh", "Chinese"))

#: the meta data file name
META_NAME: Final[str] = "metadata.yaml"

#: the bibliography data file name
BIBLIOGRAPHY_NAME: Final[str] = "bibliography.bib"

#: the root name
ROOT_NAME: Final[str] = "book.md"


def create_metadata(dest: Path,
                    bib_file: Optional[Path] = None,
                    with_git: bool = True) -> Path:
    """
    Create the metadata of the build.

    :param Path dest: the directory
    :param Optional[Path] bib_file: the bibliography file
    :param bool with_git: should github repositories be used?
    :return: the path to the metadata file
    :rtype: Path
    """
    f: Final[Path] = dest.resolve_inside(META_NAME)
    txt: List[str] = ["---",
                      "title: The Great Book of Many Things",
                      "author: Thomas Weise"]
    if with_git:
        txt.append("repos:")
        for repo in REPO_LIST:
            txt.append(f"  - id: {repo[0]}")
            txt.append(f"    url: {repo[1]}")
    txt.append("langs:")
    for lang in LANG_LIST:
        txt.append(f"  - id: {lang[0]}")
        txt.append(f"    name: {lang[1]}")
    txt.append(f"{bc.PANDOC_TEMPLATE_LATEX}: eisvogel.tex")
    txt.append(f"{bc.PANDOC_TEMPLATE_HTML5}: GitHub.html5")
    if bib_file:
        dest.enforce_contains(bib_file)
        txt.append(f"{bc.PANDOC_CSL}: association-for-computing-machinery.csl")
        txt.append(f"bibliography: {bib_file.relative_to(dest)}")
    txt.append("...")
    f.write_all(txt)
    f.enforce_file()
    dest.enforce_contains(f)
    return f


def create_bibliography(dest: Path) -> Tuple[Path, Tuple[str, ...]]:
    """
    Generate a bibliography into the given folder.

    :param Path dest: the destination folder
    :return: a tuple with the path to the bibliography and a tuple of the
        available bibliographic keys
    :rtype: Tuple[Path, Tuple[str, ...]]
    """
    f: Final[Path] = dest.resolve_inside(BIBLIOGRAPHY_NAME)
    with open(f, "wt") as fd:
        fd.write("@incollection{A,\n  title = {The Query Complexity of "
                 "Finding a Hidden Permutation},\n  author = {Peyman "
                 "Afshani and Manindra Agrawal and Benjamin Doerr and "
                 "Kasper Green Larsen and Kurt Mehlhorn and Carola "
                 "Winzen},\n  booktitle = {Space-Efficient Data Structures, "
                 "Streams, and Algorithms},\n  pages = {1--11},\n  publisher "
                 "= {Springer},\n  year = {2013},\n  chapter = {1},\n}"
                 "\n\n@inproceedings{B,\n  author = {Denis Antipov and "
                 "Benjamin Doerr},\n  title = {Precise Runtime Analysis "
                 "for Plateaus},\n  booktitle = {15th Intl. Conf. on "
                 "Parallel Problem Solving from Nature {{PPSN}~{XV}}, "
                 "{Part~II}},\n  pages = {117--128},\n  year = {2018},"
                 "\n  publisher = {Springer},\n}\n\n@article{C,\n  "
                 "author = {Antoine Cully and Yiannis Demiris},\n  title "
                 "= {Quality and Diversity Optimization: {A} Unifying "
                 "Modular Framework},\n  journal = {{IEEE} Transactions "
                 "on Evolutionary Computation},\n  volume = {22},\n  "
                 "number = {2},\n  pages = {245--259},\n  year = {2018},"
                 "\n}\n \n\n@misc{D,\n  title = {Towards a More Practice-"
                 "Aware Runtime Analysis of Evolutionary Algorithms},\n  "
                 "author = {Eduardo {Carvalho Pinto} and Carola Doerr},\n  "
                 "year = {2017},\n  note = {arXiv:1812.00493v1 [cs.NE] 3~Dec~"
                 "2018},\n  url = {http://arxiv.org/pdf/1812.00493.pdf},\n}"
                 "\n\n@inproceedings{E,\n  author = {Benjamin Doerr and "
                 "Carola Doerr},\n  title = {Optimal Parameter Choices "
                 "Through Self-Adjustment: Applying the 1/5-th Rule in "
                 "Discrete Settings},\n  booktitle = {Genetic and "
                 "Evolutionary Computation Conf. ({GECCO'15})}},\n  pages = "
                 "{1335--1342},\n  publisher = {{ACM}},\n  year = {2015},\n  "
                 "doi = {10.1145/2739480.2754684},\n  note = {See also "
                 "arXiv:1504.03212v1 [cs.NE] 13 Apr 2015}\n}\n\n\n@book{G,\n"
                 "  author = {Richard Ernest Bellman},\n  title = {Dynamic "
                 "Programming},\n  publisher = {Princeton University Press},"
                 "\n  address = {Princeton, NJ, USA},\n  series = dbom,\n  "
                 "year = {1957},\n  isbn = {0486428095}\n}")
    return f, ("A", "B", "C", "D", "E", )


def find_local_files() -> Tuple[str, ...]:
    """
    Find proper files that can be used as external references.
    :return: the list of paths
    :rtype: Tuple[Path, ...]
    """
    tests = Path.file(__file__)

    package: Final[Path] = Path.directory(os.path.dirname(os.path.dirname(
        tests))).resolve_inside("bookbuilderpy")
    package.enforce_dir()
    result: List[Path] = list()
    for file in os.listdir(package):
        if file.endswith(".py") and ("_" not in file):
            full = os.path.join(package, file)
            if os.path.isfile(full):
                result.append(Path.file(full))
    assert len(result) > 0
    return tuple(result)


def find_repo_files(repo: Tuple[str, str]) -> Tuple[str, ...]:
    """
    Find files in a repo.
    :return: the list of paths
    :rtype: Tuple[Path, ...]
    """
    with TempDir.create() as td:
        r: Final[Repo] = Repo.download(repo[1], td)
        res = list(pathlib.Path(r.path).rglob("*.py"))
        if len(res) <= 0:
            raise ValueError(f"Repo {repo} is empty.")
        result: List[str] = list()
        for f in [Path.file(str(f)).relative_to(r.path) for f in res]:
            if ("_" not in f) and ("/" in f):
                result.append(f)
        assert len(result) > 0
        return tuple(result)


#: The possible code files to include
def get_possible_code_files(with_git: bool) -> \
        Tuple[Tuple[Optional[str], Tuple[str, ...]], ...]:
    """
    Find the possible code files.
    :param bool with_git: should github repositories be used?
    """
    if with_git:
        res = cast(Tuple[Tuple[Optional[str], Tuple[str, ...]], ...], tuple(
            f for g in
            [[tuple([None, find_local_files()])],
             [tuple([r[0], find_repo_files(r)]) for r in REPO_LIST]] for f in g
        ))
        assert isinstance(res, tuple)
        assert len(res) == (len(REPO_LIST) + 1)
    else:
        res = tuple([tuple([None, find_local_files()])])

    for i in range(len(res)):
        f = res[i]
        assert len(f) == 2
        if i > 0:
            assert isinstance(f[0], str)
        else:
            assert f[0] is None
        assert isinstance(f[1], tuple)
        assert len(f[1]) > 0
        for k in f[1]:
            assert isinstance(k, str)
            assert len(k) > 0
    return res


def make_gray_png(data) -> bytes:
    """
    Make a gray coded png file.

    :param data: the pixel data
    :return: the png data
    :rtype: bytes
    """

    def i1(value):
        return struct.pack("!B", value & (2 ** 8 - 1))

    def i4(value):
        return struct.pack("!I", value & (2 ** 32 - 1))

    # compute width&height from data if not explicit
    height = len(data)  # rows
    width = len(data[0])
    # generate these chunks depending on image type
    make_ihdr = True
    make_idat = True
    make_iend = True
    png = b"\x89" + "PNG\r\n\x1A\n".encode('ascii')
    if make_ihdr:
        colortype = 0  # true gray image (no palette)
        bitdepth = 8  # with one byte per pixel (0..255)
        compression = 0  # zlib (no choice here)
        filtertype = 0  # adaptive (each scanline seperately)
        interlaced = 0  # no
        ihdr = i4(width) + i4(height) + i1(bitdepth)
        ihdr += i1(colortype) + i1(compression)
        ihdr += i1(filtertype) + i1(interlaced)
        block = "IHDR".encode('ascii') + ihdr
        png += i4(len(ihdr)) + block + i4(zlib.crc32(block))
    if make_idat:
        raw = b""
        for y in range(height):
            raw += b"\0"  # no filter for this scanline
            for x in range(width):
                c = b"\0"  # default black pixel
                if y < len(data) and x < len(data[y]):
                    c = i1(data[y][x])
                raw += c
        compressor = zlib.compressobj()
        compressed = compressor.compress(raw)
        compressed += compressor.flush()  # !!
        block = "IDAT".encode('ascii') + compressed
        png += i4(len(compressed)) + block + i4(zlib.crc32(block))
    if make_iend:
        block = "IEND".encode('ascii')
        png += i4(0) + block + i4(zlib.crc32(block))
    return png


def create_random_png(destdir: Path,
                      name: Optional[str],
                      lang: Optional[str]) -> str:
    """
    Create a random png image
    :param destdir: the destrination directory
    :param name: the optional name
    :param lang: the language
    :return: the path to the image
    :rtype: Path
    """
    destdir.enforce_dir()
    suffix = ".png"
    if (lang is not None) and (random.uniform(0, 1) >= 0.5):
        suffix = f"_{lang}{suffix}"
    if name is None:
        (handle, spath) = mkstemp(suffix=suffix, prefix="t", dir=destdir)
        os.close(handle)
        path = Path.path(spath)
    else:
        path = destdir.resolve_inside(f"{name}{suffix}")
    if not os.path.isfile(path):
        h = int(random.uniform(0, 100)) + 1
        w = int(random.uniform(0, 100)) + 1
        d = list()
        for i in range(h):
            lll = list()
            d.append(lll)
            for j in range(w):
                lll.append(int(random.uniform(0, 256)))
        with open(path, "wb") as f:
            f.write(make_gray_png(d))
    path.enforce_file()
    return path.relative_to(destdir)


def make_name(names: Set[str]) -> str:
    """
    Make a random name.
    :param names:  the set of names
    :return: the name
    :rtype: str
    """
    name = ""
    choices = [[ord("0"), 10],
               [ord("A"), 26],
               [ord("a"), 26]]
    while (len(name) <= 2) or (name in names) or \
            (random.uniform(0, 1) <= 0.6):
        choice = choices[int(random.uniform(0 if (len(name) > 0) else 1,
                                            len(choices)))]
        name += chr(choice[0] + int(random.uniform(0, choice[1])))
    names.add(name)
    return name


def make_structure() -> Tuple[str, Tuple, Tuple[str]]:
    """
    Create a structure for a hierarchical document.

    :return: A tuple of the document name, the list of sub-documents, and a
        tuple of picture names
    :rtype: the tuple
    """

    def __make_structure(names: Set,
                         maxdepth: int) -> Tuple[str, Tuple, Tuple[str]]:
        root = make_name(names)
        sub = list()
        pics = list()
        while (maxdepth > 0) and (random.uniform(0, 1) > 0.5):
            sub.append(__make_structure(names, maxdepth - 1))
        while random.uniform(0, 1) > 0.5:
            pics.append(make_name(names))
        return root, tuple(sub), tuple(pics)

    return __make_structure({META_NAME, ROOT_NAME}, 5)


def make_text(text, dotlinebreaks: bool = True,
              max_sentences: int = 1000) -> None:
    """
    Make a random text.
    :param text: the text destination
    :param dotlinebreaks: add line break after dot?
    :param max_sentences: the maximum number of sentences
    """
    sentences = 0
    uc = ord("A")
    lc = ord("a")
    while (sentences < max_sentences) and \
            ((sentences < 2) or (random.uniform(0, 1) > 0.2)):
        words = 0
        while (words < 3) or (random.uniform(0, 1) > 0.2):
            letters = 0
            if (words > 0) or ((sentences > 0) and (not dotlinebreaks)):
                text.write(" ")
            while (letters < 3) or (random.uniform(0, 1) > 0.3):
                base = uc if ((words <= 0) and (letters <= 0)) else lc
                letters += 1
                text.write(chr(base + int(random.uniform(0, 26))))
            words += 1
        sentences = sentences + 1
        if dotlinebreaks and (random.uniform(0,1) < 0.03):
            text.write("$\\frac{5+\\sqrt{\\ln{7}}}{6}$")
        text.write(".")
        if dotlinebreaks:
            text.write("\n")


def generate_example_lang(
        struc: Tuple[str, Tuple, Tuple[str]],
        lang: str, dest: Path,
        bib_keys: Tuple[str, ...],
        repos: Tuple[Tuple[Optional[str], Tuple[str, ...]], ...]) -> Path:
    """
    Generate an example for a given language
    :param struc: the structure
    :param lang: the language
    :param bib_keys: the available bibliographic keys
    :param repos: the repos
    :param dest: the destination directory
    :return: the path to the root file
    :rtype: Path
    """
    file = dest.resolve_inside(f"{struc[0]}_{lang}.md")
    with open(file, mode="wt") as fd:
        make_text(fd, True)
        done = list()
        done.extend(struc[1])
        done.extend(struc[2])
        done.extend([True for _ in range(int(
            random.uniform(1, 2)))])
        done.extend([False for _ in range(int(
            random.uniform(1, 2)))])
        done.extend([int(random.uniform(1, 5)) for _ in range(int(
            random.uniform(1, 3)))])
        max_inner = 0
        random.shuffle(done)
        for sub in done:
            if isinstance(sub, tuple):
                d = dest.resolve_inside(sub[0])
                d.ensure_dir_exists()
                ff = generate_example_lang(struc=sub,
                                           lang=lang,
                                           bib_keys=bib_keys,
                                           dest=d,
                                           repos=repos)
                ff.enforce_file()
                make_text(fd, True)
                fd.write(f"\n\n\\{bc.CMD_INPUT}"
                         f"{{{sub[0]}/{sub[0]}.md}}\n\n")
                make_text(fd, True)
            elif isinstance(sub, bool):
                make_text(fd, True)
                if sub:
                    repo = repos[int(random.uniform(0, len(repos)))]
                    repofile = repo[1][int(random.uniform(0, len(repo[1])))]
                    if repo[0] is None:
                        (handle, spath) = mkstemp(suffix=".py",
                                                  prefix="t", dir=dest)
                        spath = Path.file(spath)
                        label = spath.replace("/", "_").replace(".", "_")
                        os.close(handle)
                        shutil.copyfile(Path.file(repofile), spath)
                        spath = spath.relative_to(dest)
                        fd.write(f"\n\n\\{bc.CMD_RELATIVE_CODE}{{{label}}}{{")
                        make_text(fd, False, 1)
                        fd.write(f"}}{{{spath}}}{{}}{{}}{{}}\n\n")
                    else:
                        spath = repo[1][int(random.uniform(0, len(repo[1])))]
                        label = spath.replace("/", "_").replace(".", "_")
                        fd.write(f"\n\n\\{bc.CMD_GIT_CODE}"
                                 f"{{{repo[0]}}}{{{label}}}{{")
                        make_text(fd, False, 1)
                        fd.write(f"}}{{{spath}}}{{}}{{}}{{}}\n\n")
                else:
                    if len(bib_keys) > 0:
                        st = set()
                        for i in range(int(random.uniform(1, 5))):
                            st.add(bib_keys[int(
                                random.uniform(0, len(bib_keys)))])
                        make_text(fd, False, 1)
                        before = " ["
                        for key in st:
                            fd.write(before)
                            fd.write("@")
                            fd.write(key)
                            before = ";"
                        fd.write("]")
                        make_text(fd, False, 1)
                make_text(fd, True)
            elif isinstance(sub, int):
                make_text(fd, True)
                fd.write("\n\n")
                sub = min(max_inner + 1, sub)
                for i in range(sub):
                    fd.write("#")
                max_inner = sub
                fd.write(" ")
                make_text(fd, False, 1)
                fd.write("\n\n")
                make_text(fd, True)
            else:
                assert isinstance(sub, str)
                make_text(fd, True)
                path = create_random_png(dest, sub, lang)
                fd.write(f"\n\n\\{bc.CMD_RELATIVE_FIGURE}{{{sub}}}{{")
                make_text(fd, False, 1)
                fd.write(f"}}{{{path}}}{{width=50%}}\n\n")
                make_text(fd, True)
    return file


def generate_example(dest: Path,
                     with_git: bool) -> Path:
    """
    Generate an example directory strucure
    :param dest: the destination directory
    :param bool with_git: should git repos be used?
    :return: the path to the root file
    """
    dest.enforce_dir()
    bib_file, bib_keys = create_bibliography(dest)
    meta: Final[Path] = create_metadata(dest, bib_file=bib_file,
                                        with_git=with_git)
    assert os.path.basename(meta) == META_NAME

    struc = make_structure()

    root: Final[Path] = dest.resolve_inside(ROOT_NAME)
    with open(root, mode="wt") as fd:
        fd.write(f"\\{bc.CMD_INPUT}{{{META_NAME}}}\n")
        fd.write(f"\\{bc.CMD_INPUT}{{{struc[0]}.md}}\n")

    repos = get_possible_code_files(with_git=with_git)
    for lang in LANG_LIST:
        generate_example_lang(struc=struc,
                              lang=lang[0],
                              bib_keys=bib_keys,
                              dest=dest,
                              repos=repos)
    return root


def test_build_examples():
    """
    Test the generation of an example folder structure.
    """
    with TempDir.create() as source:
        root = generate_example(source,
                                with_git=("GITHUB_JOB" in os.environ))
        with TempDir.create() as dest:
            build: Final[Build] = Build(root, dest, False)
            build.build()
