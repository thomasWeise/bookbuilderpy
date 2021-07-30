[![make build](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml/badge.svg)](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml)

# bookbuilderpy

A python 3-based environment for the automated compilation of books from markdown.

## 1. Introduction

The goal of this package is to provide you with a pipeline that can:
  - automatically compile books written in [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) to formats such as [pdf](http://thomasweise.github.io/aitoa/aitoa.pdf), stand-alone [html](http://thomasweise.github.io/aitoa/aitoa.html), 
[epub](http://thomasweise.github.io/aitoa/aitoa.epub), and [azw3](http://thomasweise.github.io/aitoa/aitoa.azw3),
  - support a hierarchical file structure for the book sources, i.e., allow you divide the book into chapters in folders which can contain sub-folders with sections and sub-sub-folders with sub-sections,
  - support the automatic download and inclusion of code snippets from git repositories,
  - allow the book to be written in multiple languages, and finally
  - generate a website that lists all produced files so that you can copy everything to a web folder and offer your work for download without any further hassle.

This python package requires that [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) must be installed.
Most likely, this package will only work under Linux - at least I did not test it under Windows.

## 2. Installation

You can easily install this package and its required packages using [`pip`](https://pypi.org/project/pip/) by doing

```
pip install git+https://github.com/thomasWeise/bookbuilderpy.git
```

## 3. Supported Markdown

## 3.1. Basic Commands provided by pandoc

The following basic commands are already available in pandoc's [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) flavor and/or are provided by the existing pandoc plugins that we use:

- Chapters, sections, sub-sections etc. are created by putting their title on a single line preceded by `#`, `##`, or `###`, etc. For example, the line `## This is a section` starts a section with the given title. 
- You can use LaTeX maths as inline formulae such `$\sqrt{5}+4^4$` and as stand-alone equations like `$$x=\frac{5}{6}$$`.


## 3.2. Added Functionality

The following new commands are added:

- `\relative.input{path}` recursively includes and processes the contents of the file identified by `path`. `path` must be in a sub-folder of the current folder. The deepest folder of the new full path will become the current folder for any (recursive) `\relative.input{path}` invocations in the new file.  

## 4. License

The copyright holder of this package is Prof. Dr. Thomas Weise (see Contact).
The package is licensed under the GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.

## 5. Contact

If you have any questions or suggestions, please contact
[Prof. Dr. Thomas Weise](http://iao.hfuu.edu.cn/5) of the
[Institute of Applied Optimization](http://iao.hfuu.edu.cn/) at
[Hefei University](http://www.hfuu.edu.cn) in
Hefei, Anhui, China via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
