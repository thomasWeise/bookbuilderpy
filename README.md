[![make build](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml/badge.svg)](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml)

# bookbuilderpy: Building Books from Markdown

A [Python&nbsp;3](https://docs.python.org/3)-based environment for the automated compilation of books from markdown.

1. [Introduction](#1-introduction)
2. [Installation and Local Use](#2-installation-and-local-use)
   1. [Local Installation and Use](#21-local-installation-and-use)
   2. [Using the Docker Image](#22-using-the-docker-image)
   3. [Examples](#23-examples)
4. [Provided Functionality](#3-provided-functionality)
    1. [Basic commands provided by `pandoc` and off-the-shelf filters](#31-basic-commands-provided-by-pandoc-and-off-the-shelf-filters)
    2. [`bookbuilderpy`-specific commands](#32-bookbuilderpy-specific-commands)
    3. [Metadata](#33-metadata)
        1. [Language Specification and Resolution](#331-language-specification-and-resolution)
        2. [Git Repositories](#332-git-repositories)
        3. [Website Construction](#333-website-construction)
        4. [Other Metadata](#334-other-metadata)
    4. [Graphics](#34-graphics)
5. [GitHub Pipeline](#4-github-pipeline)
    1. [The Repository](#41-the-repository)
    2. [The GitHub Action](#42-the-github-action)
6. [Related Projects and Components](#5-related-projects-and-components)
    1. [Own Contributed Projects and Components](#51-own-contributed-projects-and-components)
    2. [Related Projects and Components Used](#52-related-projects-and-components-used)
7. [License](#6-license)
    1. [Wandmalfarbe/pandoc-latex-template](#61-wandmalfarbepandoc-latex-template)
    2. [tajmone/pandoc-goodies HTML Template](#62-tajmonepandoc-goodies-html-template)
    3. [MathJax](#63-mathjax)
8. [Contact](#7-contact)

## 1. Introduction

The goal of this package is to provide you with a pipeline that can:
  - automatically compile books written in [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) to formats such as [pdf](https://www.iso.org/standard/75839.html), stand-alone [html](https://www.w3.org/TR/html5/), 
[epub](https://www.w3.org/publishing/epub32/), and [azw3](http://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf),
  - support a hierarchical file structure for the book sources, i.e., allow you divide the book into chapters in folders which can contain sub-folders with sections and sub-sub-folders with sub-sections,
  - support the automatic download and inclusion of code snippets from [git repositories](https://git-scm.com),
  - allow the book to be written in multiple languages, and finally
  - automatically generate a website that lists all produced files so that you can copy everything to a web folder and offer your work for download without any further hassle.

Let us say you are a university or college lecturer or a high school teacher.
You want to write a lecture script or a book as teaching material for your students. 
What do you need to do?

Well, you need to write the book in some form or another, maybe in [LaTeX](https://www.latex-project.org) or with some other [editor](https://www.libreoffice.org/discover/writer).
But usually your students would not want to read it like that, instead need to "compile" it to another format.
OK, so you write the book and compile it to, say, [pdf](https://www.iso.org/standard/75839.html).
Then you need to deliver the book, i.e., upload it to some website so that your students can access it.
Thus, everytime you want to improve or change your book, you have to run the process `change the text -> compile the text -> upload the result`.
The last two steps have nothing to do with actually writing the book, they just eat away your productive time.
With our tool suite, they can be fully automated.

But let us continue.
We said above you want to compile to [pdf](https://www.iso.org/standard/75839.html).
This format is maybe nice for printing, but maybe not so much for reading the book in a browser.
For this, you would want to have [html](https://www.w3.org/TR/html5/).
And if your student use hand-held devices or mobile phones, maybe you want to have your book also in [a format](https://www.w3.org/publishing/epub32/) suitable for that.
This means you have at least three or four compile chains to get the right output and probably will run into problems with the conversations, too.
With our tool suite, all of this can be fully automated.

Especially, in the field of computer science, teaching material may also include [code snippets](#32-bookbuilderpy-specific-commands).
If you just write the code snippets into the book text, you will probably commit errors and produce examples that your students cannot execute.
I am a fan of unit testing of code and of providing examples and software that the students can really look at and use and execute.
What I want is to have one or multiple GitHub repositories with my example codes.
This would allow to have unit testing and full-blown builds for the example codes.
Then, in my book's text, I just want to reference (pieces of) files from these repositories and the book build chain should copy them into the book.
With our tool suite, [this can be done](#332-git-repositories).

Actually, maybe I want to write the whole book on GitHub directly.
The "full" realization of the idea of our tool chain is that also the book text itself would be located in a GitHub repository.
You can write the text there, just as we did in our [examples given later](#23-examples).
Whenever you commit a set of changes, the book will be compiled to the formats mentioned above and automatically uploaded to the book's website.
There, it is ready for download for your students and always in the most up-to-date version.
If you do this, then you could also collaboratively work on a book, i.e., multiple authors could work on the text and commit to the same repository.
Additionally, students could submit an "issue" to the repository if they find that something is unclear or discover an error.

This is the way we want to use our tool chain (although you can also run it just locally on your own computer).
Additionally, our tool chain supports writing the book in [multiple languages](#331-language-specification-and-resolution) in parallel.
But more about this later.


## 2. Installation and Local Use

The following examples are for [Ubuntu](https://ubuntu.com) [Linux](https://www.linux.org).
Under other Linux flavors, they may work differently and different commands may be required.
Execute the examples at your own risk.


### 2.1. Local Installation and Use

#### Installation of the Package

In order to use this package and to, e.g., run the example codes, you need to first install it using [`pip`](https://pypi.org/project/pip/).
You can install the newest version of this library from [PyPi](https://pypi.org/project/bookbuilderpy/) using [`pip`](https://pypi.org/project/pip/) by doing

```shell
pip install bookbuilderpy
```

This will install the latest official release of our package.
If you want to install the latest source code version from GitHub (which may not yet be officially released), you can do

```shell
pip install git+https://github.com/thomasWeise/bookbuilderpy.git
```

If you want to install the latest source code version from GitHub (which may not yet be officially released) and you have set up a private/public key for GitHub, you can also do:

```shell
git clone ssh://git@github.com/thomasWeise/bookbuilderpy
git install bookbuilderpy
```

This may sometimes work better if you are having trouble reaching GitHub via `https` or `http`.
You can also clone the repository and then run a `make` build, which will automatically install all dependencies, run all the tests, and then install the package on your system, too.
If this build completes successful, you can be sure that `bookbuilderpy` will work properly on your machine.


#### Installation of the Tool Chain

If you want the full tool chain, though, you also need [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) must be installed.
Additionally, you should have installed [git](http://en.wikipedia.org/wiki/Git), [Firefox](https://www.mozilla.org/en-US/firefox/new/), the [Firefox geckodriver](https://github.com/mozilla/geckodriver), and [ghostscript](http://ghostscript.com/).
Most likely, this package will only work under [Linux](https://www.linux.org) &ndash; at least I did not test it under Windows.
All commands and examples in the following require [Linux](https://www.linux.org).


### 2.2. Using the Docker Image

So it might be easier to just use the [docker container](http://hub.docker.com/r/thomasweise/docker-bookbuilderpy/) that comes with everything pre-installed.
You can then run it as:

```shell
docker run -v "INPUT_DIR":/input/:ro \
           -v "OUTPUT_DIR":/output/ \
           thomasweise/docker-bookbuilderpy BOOK_ROOT_MD_FILE
```

Under many distributions, you need to run this command as `sudo`.
Here, it is assumed that

- `INPUT_DIR` is the directory where your book sources reside, let's say `/home/my/book/sources/`. (By adding `:ro`, we mount the input directory read-only, just in case.)
- `BOOK_ROOT_MD_FILE` is the root file of your book, say `book.md` (in which case, the full path of `book.md` would be `/home/my/book/sources/book.md`). Notice that you can specify only a single file, but this file can reference other files in sub-directories of `INPUT_DIR` by using commands such as  `\rel.input` (see [below](#32-bookbuilderpy-specific-commands)).
- `OUTPUT_DIR` is the output directory where the compiled files should be placed, e.g., `/home/my/book/compiled/`. This is where the resulting files will be placed.

### 2.3. Examples

If you are a learning-by-doing person, you can clone the "minimal working example" repository [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe).
This repository contains a book template showcasing many of the important commands and features of the system.
It is automatically compiled and published on each commit.
The website, which then is re-generated automatically each time, is <https://thomasweise.github.io/bookbuilderpy-mwe>
You can run the example under [Ubuntu](https://ubuntu.com) Linux by cloning the repository executing the build process on this repository with docker as follows, **but execute the code below at your own risk!**

```shell
mkdir example
cd example
git clone https://github.com/thomasWeise/bookbuilderpy-mwe.git
mkdir result
sudo docker run -v "$(pwd)/bookbuilderpy-mwe":/input/:ro -v "$(pwd)/result":/output/ thomasweise/docker-bookbuilderpy book.md
sudo chown $USER -R result
```

Above, we create a folder called `example`.
We then clone the repository [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe), creating the folder `bookbuilderpy-mwe` containing the example book sources.
Then, directory `result` is created, into which we will build the book.
With `sudo docker run -v bookbuilderpy-mwe:/input/:ro -v result:/output/ thomasweise/docker-bookbuilderpy book.md`, the build process is executed.
Since it runs under `sudo`, the files will be generated with `sudo` permissions/ownership, so we transfer them to the user ownership via `sudo chown $USER -R result`.
You can now peek into the `result` folder.
It will contain a file `index.html`, which is the automatically generated (bare minimum) book website, from which you can access all other generated files.

Notice that you can also automate your whole book building *and publishing* process using our [GitHub Pipeline](#4-github-pipeline) later discussed in [Section&nbsp;4](#4-github-pipeline).
Another example for the use of this pipeline is our book [Optimization Algorithms](https://thomasweise.github.io/oa).
The source code of this book is in the GitHub repository [thomasWeise/oa](https://github.com/thomasWeise/oa).

## 3. Provided Functionality

Our book building pipeline is based on [pandoc flavored markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) and the filters [`pandoc-citeproc`](http://github.com/jgm/pandoc-citeproc), [`pandoc-crossref`](http://github.com/lierdakil/pandoc-crossref), [`latex-formulae-pandoc`](http://github.com/liamoc/latex-formulae), and [`pandoc-citeproc-preamble`](http://github.com/spwhitton/pandoc-citeproc-preamble).
It supports the commands and syntax given there, some of which is summarized below in [Section&nbsp;3.1](#31-basic-commands-provided-by-pandoc-and-off-the-shelf-filters).
However, we add several commands, such as a hierarchical file inclusion structure, a support for multi-language file resolution, a support for including program listings from git repositories, and so on.
These extensions are discussed in [Section&nbsp;3.2](#32-bookbuilderpy-specific-commands).

## 3.1. Basic commands provided by `pandoc` and off-the-shelf filters

The following basic commands are already available in pandoc's [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) flavor and/or are provided by the existing pandoc plugins that we use:

- Chapters, sections, sub-sections etc. are created by putting their title on a single line preceded by `#`, `##`, or `###`, etc.
  For example, the line `## This is a section` (two `#`) starts a section with the given title, `# This is a chapter` (one `#`) starts a chapter. 
  You can add labels to sections, by writing `# Chapter Title {#sec:myChap}` and reference them via `As already discussed in [@sec:myChap], we found...`.
  The prefix `sec:` is required for such labels.
  Sections and chapters etc. are numbered automatically.
  If you want an unnumbered section, write `## Other Section {-}`.
- You can use LaTeX maths as inline formulae such `$\sqrt{5}+4^4$` and as stand-alone equations like `$$x=\frac{5}{6}$$`.
  A line such as `$$ x = y + z $$ {#eq:xyz}` will create an equation that can be referenced using `[@eq:xyz]` in the text.
  Notice: It is best to use `\ldots` instead of `\dots` to avoid problems.
- References to bibliography can be done `[@ABC; @DEF]` where `ABC` and `DEF` would then be keys into your [BibTeX](https://www.bibtex.com/g/bibtex-format/)) file, which, in turn, would be specified in the metadata as `bibliography: bibtexfile.bib`.
- *Emphasized* text is written in between `*`s, e.g., `The word *text* is emphasized.`.
- **Double emphasized** text is written in between double-`*`s, e.g. `The word **text** is very much emphasized.`
- Short verbatim/code text is written in between &grave;s, e.g., *The word &grave;`text`&grave; appears as code.*
- Abbreviations and LaTeX-style commands can be created and called normally, as long as they do not clash with the [`bookbuilderpy`-specific commands](#32-bookbuilderpy-specific-commands).
  For example, you can do:

```
\newcommand{\mathSpace}[1]{\mathbb{#1}}
\newcommand{\realNumbers}{\mathSpace{R}}

Assume that $x\in\realNumbers$ is a value larger than $2$, then $\sqrt{x}>1$ is also true.
```

- Tables can be created as follows:

```
This is some normal text.

|centered column|right-aligned column|left-aligned column|
|:-:|--:|:--|
|bla|r|l|
|blub blub blub|abc|123|

: This is the table caption. {#tbl:mytable}

From [@tbl:mytable], we can see that...
```

- Figures should be included using the [`bookbuilderpy`-specific](#32-bookbuilderpy-specific-commands) `\rel.figure{...}` command.

## 3.2. `bookbuilderpy`-specific commands

The following new commands are added:

- `\rel.input{path}` recursively includes and processes the contents of the file identified by `path`. `path` must be in a sub-folder of the current folder. The deepest folder of the new full path will become the current folder for any (recursive) `\rel.input{path}` invocations in the new file as well as `\rel.code` and `\rel.figure` commands. [Language-specific file resolution](#331-language-specification-and-resolution) will apply.
- `\rel.code{label}{caption}{path}{lines}{labels}{args}` is used to include code (or portions of code) from a source code file located in the current folder (or any `path` beneath it).
  [Language-specific file resolution](#331-language-specification-and-resolution) will apply.
  This command has the following arguments:
  + `label`: the label of the listing, e.g., `something`. Will automatically be prefixed by `lst:` and can then be referenced in the text, e.g., as `The algorithm is specified in [@lst:something].`. 
  + `caption`: the caption of the listing
  + `path`: the relative path fragment to resolve
  + `lines`: the lines of the code to keep in the form `1-3,6`, or empty to keep all
  + `labels`: the labels for selecting code pieces, or empty to keep all. For instance, specifying `a,b` will keep all code between line comments `start a` and `end a` and `start b` and `end b`. By ending a line outside the selected range with line comment `+a` (where `a` is again a label name), it will be included. If it is inside the selected range and ends with line comment `-a`, it is excluded.
  + args: any additional, language-specific arguments to pass to the code renderer, as comma-separated strings.
    - For Python, we automatically strip type hints, docstrings, and comments from the code and also re-format the code. The re-formatting ensures that lines are no longer than 70 characters, which is necessary to make the listings in PDFs to look nicely.
      With `doc` you keep the docstrings, with `comments` you keep the comments, with `hints` you keep the type hints.
      If you specify `format`, then the code is not reformatted at all (which automatically preserves docstrings, type hints, and comments, except for the code selection labels.)
- `\git.code{repo}{label}{caption}{path}{lines}{labels}{args}` works the same as `\relative.code`, but uses code from the specified git repository instead (see [Metadata](#332-git-repositories)).
  [Language-specific file resolution](#331-language-specification-and-resolution) does *not* apply, however, you may specify repositories differently for each language in the metadata.
- `\rel.figure{label}{caption}{path}{args}` includes a figure into the book. [Language-specific file resolution](#331-language-specification-and-resolution) will apply.
  This command has the following arguments:
  + `label`: the label of the figure, e.g., `something`. It will be automatically prefixed by `fig:` can then be referenced in the text, e.g., as `As illustrated in [@fig:something], ...`.
  + `caption`: the caption of the figure
  + `path`: the relative path fragment to resolve
  + `args`: other arguments, e.g., `width=XX%` for making the figure having a width corresponding to `XX%` of the available with.
- `\definition{type}{label}{body}` creates a definition of the given type (where the metadata must somewhere specify `typeTitle`) that can be referenced via `\def.ref{label}` anywhere in the text.
  The body containing the actual definition of the definition is `body`.
  For example `\definition{def}{bla}{A *definition* is a text about something.}` with `defTitle: Definition` in the metadata would generate something like `**Definition 1**: A *definition* is a text about something.` and `\def.ref{bla}` would then become `Definition 1` (but as clickable hyperlink).
- `\meta{key}` any metadata string you specify in your [metadata](#33-metadata), including `title`, `author`, etc., with the following additional keys:
  + `time`: the ISO date and time when the book building process was started,
  + `date`: the ISO date when the book building process was started,
  + `year`: the year when the book building process was started,
  + `lang`: the current [language](#331-language-specification-and-resolution) id, or `en` if none is specified
  + `locale`: the locale inferred from the current language id
  + `lang.name`: the current language name, or `English` if none is specified
  + `repo.name`: if it was detected that the build process is applied to a git repository checkout, then this is the repository name, e.g., `thomasweise/bookbuilderpy`; otherwise querying this property will fail the build process.
  + `repo.url`:  if it was detected that the build process is applied to a git repository check out, then this is the repository url, such as `https://github.com/thomasweise/bookbuilderpy`; otherwise querying this property will fail the build process.
  + `repo.commit`:  if it was detected that the build process is applied to a git repository checkout, then this is the commit id of the checkout; otherwise querying this property will fail the build process.
  + `repo.date`:  if it was detected that the build process is applied to a git repository checkout, then this is the date of the commit that was checked-out; otherwise querying this property will fail the build process.

## 3.3. Metadata

The metadata of your book is a very important portion that specifies not just its title and author, but also all the information for the build process.
It should be located in a file `metadata.yaml` and the very first line of your main book file then must be a `\rel.input` of this metadata file.
In the metadata section of your book, you can define things such as the book title and author etc.
We added the following metadata items:

### 3.3.1. Language Specification and Resolution

You can develop your book in multiple languages in parallel.
These can be specified in the metadata following the pattern below:

```yaml
langs:
  - id: en
    name: English
  - id: de
    name: Deutsch
  - id: zh
    name: 中文
```

The `langs` entry specifies a list, where each item must have an `id` and a `name`.
The `id` will be used to determine the [locale](https://cldr.unicode.org/)  of the text.
You can either use a [locale](https://cldr.unicode.org/) directly, or one of the following shortcuts: `en` for `en_US`, `zh` or `cn` for `zh_CN`, `tw` for `zh_TW`, `de` for `de_DE`, `fr` for `fr_FR`, `it` for `it_IT`, `ja` for `ja_JP`, `ko` for `ko_KR`, `pt` for `pt_BR`, and `es` for `es_ES`.
**Warning&nbsp;1**: Do not specify the `lang` attribute usually used by pandoc, as this causes some trouble.
**Warning&nbsp;2**: If you only specify a single language, the book's main file name cannot be `index.md`.
**Warning&nbsp;3**: If you want to build a book in the Chinese language, you must specify the language Chinese with one of the Chinese-related prefixes above.

The language name will appear in things such as the automatically generate website, etc.
For each language, one book building process will be performed.
In the above example, we will build the book three times, for English, German, and Chinese.
If the book's basic file name was `book.md`, we will get `book_en.pdf`, `book_de.pdf`, and `book_zh.pdf`.
If only one language was specified, we would just get `book.pdf`.

The language `id` has one very important purpose:
It allows for language-specific file resolution.
For instance, let's say you do `\rel.input{folder/README.md}`.
In the `en`-build step, this will first look for a file `folder/README_en.md`.
If it exists, it is included.
Otherwise, the file `folder/README.md` will be included.

The same will be done for `\rel.figure` commands.
This way, you can, e.g., create language-neutral figures that are the same for all versions of the book as well as language-specific figures that contain texts.

It makes sense to split your metadata into language-specific and language-agnostic data.
For example, the style and title page background of your book may be language-agnostic.
The title, definition types, figure titles, table titles, keywords, and even font may be language-specific.
This can be accomplished by using `\rel.input` in the `metadata.yaml` file!
For the very first language (in our example English) create a file `metalang.yaml` and put all the language-specific information for that first language in there.
This will be the default setting for anything else not specified for the other language and also for the website title generation.
Then, for each other language, create one language-specific file, say `metalang_de.yaml` and `metalang_zh.yaml` in our example.
Finally, simply first specify the `langs` list in the `metadata.yaml`, and then `\rel.input{metalang.yaml}` and let the language-specific file resolution do the rest&hellip;

Last but not least, the language id will be used to decide which pdf-engine is used for building the book.
For instance, a language ID like `zh`, indicating Chinese, will lead to the use of `xelatex`, while otherwise `pdflatex` will be used.

### 3.3.2. Git Repositories

It is possible to include code from one or multiple git repositories using the `\git.code` command.
For this purpose, you first need to specify the repositories in the metadata section as follows:

```yaml
repos:
  - id: mp
    url: https://github.com/thomasWeise/moptipy.git
  - id: bb
    url: https://github.com/thomasWeise/bookbuilderpy.git
```

The above list specifies two git repository mnemonics, `mp` and `bp`.
When the book is being built, both repositories are automatically checked out.
The `\git.code{repo}{label}{caption}{path}{lines}{labels}{args}` command with `repo` set to `mp` will then refer to the first repository (`moptipy`) and the `path` argument then is a path relative to the repository root.
`repo=bb` would instead refer to the `bookbuilderpy` repository.

### 3.3.3. Website Construction

It is possible to automatically generate a website during the build process.
You can then upload the website and all of the generated files to your website, offering an easy way to download your book.
The mechanism is very simple:
We can have an "outer" website, i.e., an HTML file with styles and headers and stuff and an "inner" website which can be a portion of markdown code.
The idea is that the "inner" website could be the `README.md` file of the repository where your book is and the outer website allows you to specify a container and proper CSS styles for rendering it.
Both can be specified in the metadata, e.g., as follows:

```yaml
---
# ... other stuff

# the website
website_outer: meta/website.html
website_body: README.md

# ... other stuff
...
```

This mechanism works as follows:
The inner website (in this case, the file ` website.html` in the folder `meta` is loaded as a string.
Inside, all the `\meta{...}` commands accessing meta-data are evaluated (see [`bookbuilderpy` specific commands](#32-bookbuilderpy-specific-commands)).
Here, the first language's metadata attribute values will be used if multiple languages were specified.
The outer website *can* contain the text `{body}` exactly once and this text is then replaced by the rendered markdown of the inner website.
Here, this would be the file `README.md` in the root folder.
The inner website *can* then somewhere contain a div tag `<div id="files"> .... </div>`.
If present, this tag and everything inside will be replaced with an automatically generated list of all the generated files.
If the [`langs` attribute](#331-language-specification-and-resolution) is specified and contains more than one language, there will be one nested list per language.
Otherwise, the list will be flat.
The lists will have the following CSS-classes:

- `langs`: for the main list of multiple languages<sup>*</sup>
- `oneLang`: for the language list item<sup>*</sup>
- `oneLangName`: for the span with the language name<sup>*</sup>
- `downloads`: for the download list per language
- `download`: for the download list entry
- `downloadFile`: for the span containing the file download
- `downloadFileName`: for the span with the file name
- `downloadFileSize`: for the span with the file size
- `downloadFileDesc`: for the description of the file format

<sup>*</sup> if the [`langs` attribute](#331-language-specification-and-resolution) is specified and contains more than one language
The result of this rendering process is then stored in a file `index.html`.
For this reason you should never call your main book file `index.md`.

The idea of this website building process is as follows:
Via the "outer" website, you can specify the structure, header, footer (where you could, e.g., place the build time via a `\meta{date}` command), and CSS styles.
If you develop your book on GitHub, then you would probably write a `README.md` file explaining the book's content anyway.
This file you can then automatically render and insert into the website as "inner" website part.
Inside your `README.md` on GitHub, the tag `<div id="files"> .... </div>` would be invisible, but during the website building, it allows you to have the list of book files included automatically.
This automatic inclusions allows us to specify file sizes.
For course, we could also simply not insert this tag and instead have hard-coded links in the `README.md`, which is fine, too.

### 3.3.4. Other Metadata

- `title`: the book's title
- `keywords`: a list of keywords
- `author`: the book author or a list of authors
- `date`: the date when the book was written (you can set this to `\meta{data}` and the current date of the build process will be used).
- `bibliography`: the path to the [BibTeX](https://www.bibtex.com/g/bibtex-format/) file, e.g., `bibliography.bib`
- `csl`: the [bibliography style](https://citationstyles.org). Set this to `association-for-computing-machinery.csl` to use the default style offered by the package.
  You can find many different bibliography styles at <https://www.zotero.org/styles>.
- `link-citations`: set this to `true` to get clickable bibliography references.
- `template.html`: the template for rendering to HTML. Set this to `GitHub.html5` to use the default style offered by the package.
- `template.latex`: the template for rendering to PDF. Set this to `eisvogel.tex` to use the default style offered by the package.
- If you build a book in a language different from English, you will certainly want to change the default caption prefixes for figures and tables accordingly.
  The following language-specific component titles (below explained-by-example) are supported by pandoc and its filters:

```yaml
figureTitle: Figure
tableTitle: Table
listingTitle: Listing

figPrefix:
  - "Figure"
  - "Figures"
eqnPrefix:
  - "Equation"
  - "Equations"
tblPrefix:
  - "Table"
  - "Tables"
lstPrefix:
  - "Listing"
  - "Listings"
secPrefix:
  - "Section"
  - "Sections"

reference-section-title: References
```
- Please notice that there is an [issue](https://github.com/lierdakil/pandoc-crossref/issues/329) with chapter names in the pdf output.
  You can fix this by setting up the chapter and section names *also* in the LaTeX header includes (see below).

- Any other `xxxTitle` allows you to specify a `type`to be used for a `\definition{type}{label}{body}` command.
- `header-includes`: allows you to insert stuff into the headers of the format.
  For PDF/LaTeX, it is useful to put something like the stuff below, as it will make the result nicer if you have many code listings:

```yaml
# line 1..3: hold floating objects in the same section and sub-section
# line 4..6: prevent ugly broken footnotes
# line 7..9: fix section and chapter names
header-includes:
- |
  ```{=latex}
  \usepackage[section,above,below]{placeins}%               1
  \let\Oldsubsection\subsection%                            2
  \renewcommand{\subsection}{\FloatBarrier\Oldsubsection}%  2
  \addtolength{\topskip}{0pt plus 10pt}%                    4
  \interfootnotelinepenalty=10000%                          5
  \raggedbottom%                                            6
  \usepackage[nameinlink]{cleveref}%                        7
  \crefname{chapter}{Chapter}{Chapters}%                    8
  \crefname{section}{Section}{Sections}%                    9
  ` ` `
```
(without the spaces between the triple-backticks!)
In the two `\crefname` commands at the end, you can put the singular and plural forms of the names for chapters and sections in your language of choice. 

For Chinese versions of your book using our default template ([Wandmalfarben/Eisvogel](#61-wandmalfarbepandoc-latex-template)), you may instead want to use the following `header-includes` in order to work-around the a [minor issue](https://github.com/Wandmalfarbe/pandoc-latex-template/issues/256) with the template.   

```yaml
# line 1..3: hold floating objects in the same section and sub-section
# line 4..6: prevent ugly broken footnotes
# line 7..9: fix section and chapter names
# line 10..12: fix bug https://github.com/Wandmalfarbe/pandoc-latex-template/issues/256
header-includes:
- |
  ```{=latex}
  \usepackage[section,above,below]{placeins}%                 1
  \let\Oldsubsection\subsection%                              2
  \renewcommand{\subsection}{\FloatBarrier\Oldsubsection}%    3
  \addtolength{\topskip}{0pt plus 10pt}%                      4
  \interfootnotelinepenalty=10000%                            5
  \raggedbottom%                                              6
  \AtBeginDocument{%                                        7
  \crefname{chapter}{章}{章}%                                  8
  \crefname{section}{节}{节}%                                 9
  \addto\captionsenglish{\renewcommand{\figurename}{图}}%    10
  \addto\captionsenglish{\renewcommand{\tablename}{表}}%     11
  }%                                                        12
  ` ` `
```
(without the spaces between the triple-backticks!)


- Setup for pandoc's crossref: You may wish to include the following text
```yaml
# pandoc-crossref setup
cref: true
chapters: true
linkReferences: true
nameInLink: true
listings: false
codeBlockCaptions: true
```

### 3.4. Graphics

Generally, we suggest to use only [vector graphics](http://en.wikipedia.org/wiki/Vector_graphics) in your books, as opposed to [raster graphics](http://en.wikipedia.org/wiki/Raster_graphics) like [`jpg`](http://en.wikipedia.org/wiki/JPEG) or [`png`](http://en.wikipedia.org/wiki/Portable_Network_Graphics).
Don't use `jpg` or `png` for anything different from photos.
Vector graphics can scale well and have a higher quality when being printed or when being zoomed in.
Raster graphics often get blurry or even display artifacts.

In my opinion, the best graphics format to use in conjunction with our tool is [`svg`](http://en.wikipedia.org/wiki/Scalable_Vector_Graphics) (and, in particular, its compressed variant `svgz`).
You can create `svg` graphics using the open-source editor [Inkscape](http://en.wikipedia.org/wiki/Inkscape) or software such as [Adobe Illustrator](http://en.wikipedia.org/wiki/Adobe_Illustrator) or [Corel DRAW](http://en.wikipedia.org/wiki/CorelDRAW).

We provide the small tool [ultraSvgz](http://github.com/thomasWeise/ultraSvgz), which runs under Linux and can create very small, minified and compressed `svgz` files from `svg`s.
Our tool suite supports `svgz` fully and such files tend to actually be smaller than [`pdf`](http://en.wikipedia.org/wiki/PDF) or [`eps`](http://en.wikipedia.org/wiki/Encapsulated_PostScript) graphics.

## 4. GitHub Pipeline

As discussed under point [Installation and Local Use](#2-installation-and-local-use), our tool suite is available as [docker container]([docker container](http://hub.docker.com/r/thomasweise/docker-bookbuilderpy/), so you only need a [docker installation](https://docs.docker.com/engine/install/ubuntu/) to run the complete software locally.
However, the bigger goal is to allow you to collaboratively write books, interact with your readers, and automatically publish them online.
With [docker](https://www.docker.com) in combination with [GitHub](http://www.github.com/) and [GitHub Actions](https://github.com/features/actions), this is now easily possible.

You can find a [template book project](https://github.com/thomasWeise/bookbuilderpy-mwe) using the complete automated pipeline discussed here in the repository [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe).
In other words, if you do not want to read the text and explanation below, you can as well just clone this template project and adapt everything to your liking.

You can integrate the whole process with a [version control](http://en.wikipedia.org/wiki/Version_control) software like [Git](http://en.wikipedia.org/wiki/Git) and a [continuous integration](http://en.wikipedia.org/wiki/Continuous_integration) framework.
Then, you can automate the compilation of your book to run every time you change your book sources.
Actually, there are several open source and free environments that you can use to that for you for free &ndash; in exchange for you making your book free for everyone to read.

First, both for writing and hosting the book, we suggest using a [GitHub](http://www.github.com/) repository, very much like the one for the book I just began working on [here](http://github.com/thomasWeise/oa).
The book should be written in [Pandoc's markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) syntax, which allows us to include most of the stuff we need, such as equations and citation references, with the additional comments listed above.
For building the book, we will use [GitHub Actions](https://github.com/features/actions), which are triggered by repository commits.

Every time you push a commit to your book repository, the GitHub Action will check out the repository.
The docker container can automatically build the book and book website.
The result can automatically be deployed to the [GitHub Pages](http://help.github.com/articles/what-is-github-pages/) branch of your repository and which will then be the website of the repository.
Once the repository, website, and Travis build procedure are all set up, we can concentrate on working on our book and whenever some section or text is finished, commit, and enjoy the automatically new versions.

Having your book sources on GitHub brings several additional advantages, for instance:

- Since the book's sources are available as GitHub repository, our readers can file issues to the repository, with change suggestions, discovered typos, or with questions to add clarification.
- They may even file pull requests with content to include.
- You could also write a book collaboratively &ndash; like a software project. This might also be interesting for students who write course notes together.

### 4.1. The Repository

In order to use our workflow, you need to first have an account at [GitHub](http://www.github.com/) and then create an open repository for your book.
GitHub is built around the distributed version control system [git](http://git-scm.com/), for which a variety of [graphical user interfaces](http://git-scm.com/downloads/guis) exist - see, e.g., of [here](http://git-scm.com/downloads/guis).
If you have a Debian-based Linux system, you can install the basic `git` client with command line interface as follows: `sudo apt-get install git` and the gui `git-cola`[https://git-cola.github.io/] which can be installed via `sudo apt-get install git-cola`.
You can use either this client or such a GUI to work with your repository.

You can now fill your repository with your book's source files.
The repository [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe) gives you a bare example how that can look like.

## 4.2. The GitHub Action

Create a folder `.github/workflows` and inside this folder a file `build.yaml`.
The contents of the file should be:

```yaml
name: publish

on:
  push:    
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - uses: docker-practice/actions-setup-docker@master
    - name: build
      run: |
        mkdir -p /tmp/result
        docker run -v $(pwd):/input/:ro -v /tmp/result/:/output/ thomasweise/docker-bookbuilderpy book.md
        touch /tmp/result/.nojekyll

    - name: deploy
      uses: JamesIves/github-pages-deploy-action@4.1.4
      with:
        branch: gh-pages
        folder: /tmp/result
        single-commit: true
```

This will toggle the build whenever you commit to the branch `main`.
It will then first check out the book sources.
Then it will create the temporary folder `/tmp/result` and use the docker container to build the book to this folder.
The `touch /tmp/result/.nojekyll` just adds a file to that folder telling GitHub pages that the files in there do not need to be processed any further and can be served as-is.
After that, the files in this folder will be deployed to the branch `gh-pages`, which will become the website for your book.

Let's say your username was `thomasWeise` and your book repository was `bookbuilderpy-mwe`.
To make this website visible, go to your GitHub project's [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe), click `Settings`, then go to `Pages`, then under `Source` choose `gh-pages` and click `Save`.
A few minutes afterwards, your book's website will appear as <https://thomasweise.github.io/bookbuilderpy-mwe>.
(It may also be that you may need to make one more commit to the repository to trigger this.)
Done.
Whenever you commit to your book sources, the book will be compiled and the website is updated.
Nothing else needed.

## 5. Related Projects and Components

### 5.1. Own Contributed Projects and Components

The following components have been contributed by us to provide this tool chain.
They are all open source and available on GitHub.

- The [Python&nbsp;3](https://docs.python.org/3) package [bookbuilderpy](http://github.com/thomasWeise/bookbuilderpy) providing the commands wrapping around pandoc and extending Markdown to automatically build electronic books.
- [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe), a minimum working example for using the complete bookbuilderpy tool suite.
- A hierarchy of docker containers forms the infrastructure for the automated builds:
  + [docker-bookbuilderpy](http://github.com/thomasWeise/docker-bookbuilderpy) is the docker container that can be used to compile an electronic book based on our tool chain. [Here](http://github.com/thomasWeise/docker-bookbuilderpy) you can find it on GitHub and [here](http://hub.docker.com/r/thomasweise/docker-bookbuilderpy/) on docker hub.
  + [docker-pandoc-calibre](http://github.com/thomasWeise/docker-pandoc-calibre) is the container which is the basis for [docker-bookbuilderpy](http://github.com/thomasWeise/docker-bookbuilderpy). It holds a complete installation of pandoc, [calibre](http://calibre-ebook.com), which is used to convert EPUB3 to AZW3, and TeX Live and its sources are [here](http://github.com/thomasWeise/docker-pandoc-calibre) while it is located [here](http://hub.docker.com/r/thomasweise/docker-pandoc-calibre/).
  + [docker-pandoc](http://github.com/thomasWeise/docker-pandoc) is the container which is the basis for [docker-pandoc-calibre](http://github.com/thomasWeise/docker-pandoc-calibre). It holds a complete installation of pandoc and TeX Live and its sources are [here](http://github.com/thomasWeise/docker-pandoc) while it is located [here](http://hub.docker.com/r/thomasweise/docker-pandoc/).
  + [docker-texlive-thin](http://github.com/thomasWeise/docker-texlive-thin) is the container which is the basis for [docker-pandoc](http://github.com/thomasWeise/docker-pandoc). It holds a complete installation of TeX Live and its sources are [here](http://github.com/thomasWeise/docker-texlive-thin) while it is located [here](http://hub.docker.com/r/thomasweise/docker-texlive-thin/).

### 5.2. Related Projects and Components Used

- [pandoc](http://pandoc.org/), with which we convert markdown to HTML, pdf, and epub, along with several `pandoc` filters, namely
   + [`pandoc-citeproc`](http://github.com/jgm/pandoc-citeproc),
   + [`pandoc-crossref`](http://github.com/lierdakil/pandoc-crossref),
   + [`latex-formulae-pandoc`](http://github.com/liamoc/latex-formulae), and
   + [`pandoc-citeproc-preamble`](http://github.com/spwhitton/pandoc-citeproc-preamble)
and the two `pandoc` templates
   + [Wandmalfarbe/pandoc-latex-template](http://github.com/Wandmalfarbe/pandoc-latex-template/), an excellent `pandoc` template for LaTeX by [Pascal Wagler](http://github.com/Wandmalfarbe)
   + the [GitHub Pandoc HTML5 template](http://github.com/tajmone/pandoc-goodies/tree/master/templates/html5/github) by [Tristano Ajmone](http://github.com/tajmone)
- [TeX Live](http://tug.org/texlive/), a [LaTeX](http://en.wikipedia.org/wiki/LaTeX) installation used by pandoc for generating the pdf output
- [`Python 3`](https://www.python.org/), the programming language in which this package is written
- [`cabal`](http://www.haskell.org/cabal/), the compilation and package management system via which pandoc is obtained,
- [`calibre`](http://calibre-ebook.com), which allows us to convert epub to awz3 files
- [`ghostscript`](http://ghostscript.com/), used to include all fonts into a pdf
- [`git`](https://git-scm.com), used for downloading external code repositories
- [`imagemagick`](http://www.imagemagick.org/) used by `pandoc` for image conversion
- [MathJax](https://www.mathjax.org/) is the basic tool used for converting `LaTeX` formulas in HTML to [SVG](#34-graphics) graphics for display
- [selenium](https://selenium-python.readthedocs.io/), [Firefox](https://www.mozilla.org/en-US/firefox/new/), and [Firefox geckodriver](https://github.com/mozilla/geckodriver) are used to fully evaluate the MathJax javascript to render all the `LaTeX` formulas in the HTML to [SVG](#34-graphics),
- [docker](https://en.wikipedia.org/wiki/Docker_(software)), used to create containers in which all required software is pre-installed,

## 6. License

The copyright holder of this package is Prof. Dr. Thomas Weise (see Contact).
The package is licensed under the GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.
This package also contains third-party components which are under the following licenses;

### 6.1. Wandmalfarbe/pandoc-latex-template

We include the pandoc LaTeX template from [Wandmalfarbe/pandoc-latex-template](http://github.com/Wandmalfarbe/pandoc-latex-template) by Pascal Wagler and John MacFarlane, which is under the [BSD 3 license](http://github.com/Wandmalfarbe/pandoc-latex-template/blob/master/LICENSE). For this, the following terms hold:

```
% Copyright (c) 2018, Pascal Wagler;  
% Copyright (c) 2014--2018, John MacFarlane
% 
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without 
% modification, are permitted provided that the following conditions 
% are met:
% 
% - Redistributions of source code must retain the above copyright 
% notice, this list of conditions and the following disclaimer.
% 
% - Redistributions in binary form must reproduce the above copyright 
% notice, this list of conditions and the following disclaimer in the 
% documentation and/or other materials provided with the distribution.
% 
% - Neither the name of John MacFarlane nor the names of other 
% contributors may be used to endorse or promote products derived 
% from this software without specific prior written permission.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
% "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
% LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
% FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
% COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
% INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
% BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
% LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
% CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
% LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
% ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
% POSSIBILITY OF SUCH DAMAGE.
%%

%%
% For usage information and examples visit the GitHub page of this template:
% http://github.com/Wandmalfarbe/pandoc-latex-template
%%
```
    
### 6.2 tajmone/pandoc-goodies HTML Template

We include the pandoc HTML-5 template from [tajmone/pandoc-goodies](http://github.com/tajmone/pandoc-goodies) by Tristano Ajmone, Sindre Sorhus, and GitHub Inc., which is under the [MIT license](http://raw.githubusercontent.com/tajmone/pandoc-goodies/master/templates/html5/github/LICENSE). For this, the following terms hold:

```
MIT License

Copyright (c) Tristano Ajmone, 2017 (github.com/tajmone/pandoc-goodies)
Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (sindresorhus.com)
Copyright (c) 2017 GitHub Inc.

"GitHub Pandoc HTML5 Template" is Copyright (c) Tristano Ajmone, 2017, released
under the MIT License (MIT); it contains readaptations of substantial portions
of the following third party softwares:

(1) "GitHub Markdown CSS", Copyright (c) Sindre Sorhus, MIT License (MIT).
(2) "Primer CSS", Copyright (c) 2016 GitHub Inc., MIT License (MIT).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 6.3. MathJax

[MathJax](https://www.mathjax.org/) is under the [Apache License, Version 2.0.](https://github.com/mathjax/MathJax/blob/master/LICENSE).

```
Apache License
                       Version 2.0, January 2004
                    http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

  "License" shall mean the terms and conditions for use, reproduction,
  and distribution as defined by Sections 1 through 9 of this document.

  "Licensor" shall mean the copyright owner or entity authorized by
  the copyright owner that is granting the License.

  "Legal Entity" shall mean the union of the acting entity and all
  other entities that control, are controlled by, or are under common
  control with that entity. For the purposes of this definition,
  "control" means (i) the power, direct or indirect, to cause the
  direction or management of such entity, whether by contract or
  otherwise, or (ii) ownership of fifty percent (50%) or more of the
  outstanding shares, or (iii) beneficial ownership of such entity.

  "You" (or "Your") shall mean an individual or Legal Entity
  exercising permissions granted by this License.

  "Source" form shall mean the preferred form for making modifications,
  including but not limited to software source code, documentation
  source, and configuration files.

  "Object" form shall mean any form resulting from mechanical
  transformation or translation of a Source form, including but
  not limited to compiled object code, generated documentation,
  and conversions to other media types.

  "Work" shall mean the work of authorship, whether in Source or
  Object form, made available under the License, as indicated by a
  copyright notice that is included in or attached to the work
  (an example is provided in the Appendix below).

  "Derivative Works" shall mean any work, whether in Source or Object
  form, that is based on (or derived from) the Work and for which the
  editorial revisions, annotations, elaborations, or other modifications
  represent, as a whole, an original work of authorship. For the purposes
  of this License, Derivative Works shall not include works that remain
  separable from, or merely link (or bind by name) to the interfaces of,
  the Work and Derivative Works thereof.

  "Contribution" shall mean any work of authorship, including
  the original version of the Work and any modifications or additions
  to that Work or Derivative Works thereof, that is intentionally
  submitted to Licensor for inclusion in the Work by the copyright owner
  or by an individual or Legal Entity authorized to submit on behalf of
  the copyright owner. For the purposes of this definition, "submitted"
  means any form of electronic, verbal, or written communication sent
  to the Licensor or its representatives, including but not limited to
  communication on electronic mailing lists, source code control systems,
  and issue tracking systems that are managed by, or on behalf of, the
  Licensor for the purpose of discussing and improving the Work, but
  excluding communication that is conspicuously marked or otherwise
  designated in writing by the copyright owner as "Not a Contribution."

  "Contributor" shall mean Licensor and any individual or Legal Entity
  on behalf of whom a Contribution has been received by Licensor and
  subsequently incorporated within the Work.

2. Grant of Copyright License. Subject to the terms and conditions of
  this License, each Contributor hereby grants to You a perpetual,
  worldwide, non-exclusive, no-charge, royalty-free, irrevocable
  copyright license to reproduce, prepare Derivative Works of,
  publicly display, publicly perform, sublicense, and distribute the
  Work and such Derivative Works in Source or Object form.

3. Grant of Patent License. Subject to the terms and conditions of
  this License, each Contributor hereby grants to You a perpetual,
  worldwide, non-exclusive, no-charge, royalty-free, irrevocable
  (except as stated in this section) patent license to make, have made,
  use, offer to sell, sell, import, and otherwise transfer the Work,
  where such license applies only to those patent claims licensable
  by such Contributor that are necessarily infringed by their
  Contribution(s) alone or by combination of their Contribution(s)
  with the Work to which such Contribution(s) was submitted. If You
  institute patent litigation against any entity (including a
  cross-claim or counterclaim in a lawsuit) alleging that the Work
  or a Contribution incorporated within the Work constitutes direct
  or contributory patent infringement, then any patent licenses
  granted to You under this License for that Work shall terminate
  as of the date such litigation is filed.

4. Redistribution. You may reproduce and distribute copies of the
  Work or Derivative Works thereof in any medium, with or without
  modifications, and in Source or Object form, provided that You
  meet the following conditions:

  (a) You must give any other recipients of the Work or
      Derivative Works a copy of this License; and

  (b) You must cause any modified files to carry prominent notices
      stating that You changed the files; and

  (c) You must retain, in the Source form of any Derivative Works
      that You distribute, all copyright, patent, trademark, and
      attribution notices from the Source form of the Work,
      excluding those notices that do not pertain to any part of
      the Derivative Works; and

  (d) If the Work includes a "NOTICE" text file as part of its
      distribution, then any Derivative Works that You distribute must
      include a readable copy of the attribution notices contained
      within such NOTICE file, excluding those notices that do not
      pertain to any part of the Derivative Works, in at least one
      of the following places: within a NOTICE text file distributed
      as part of the Derivative Works; within the Source form or
      documentation, if provided along with the Derivative Works; or,
      within a display generated by the Derivative Works, if and
      wherever such third-party notices normally appear. The contents
      of the NOTICE file are for informational purposes only and
      do not modify the License. You may add Your own attribution
      notices within Derivative Works that You distribute, alongside
      or as an addendum to the NOTICE text from the Work, provided
      that such additional attribution notices cannot be construed
      as modifying the License.

  You may add Your own copyright statement to Your modifications and
  may provide additional or different license terms and conditions
  for use, reproduction, or distribution of Your modifications, or
  for any such Derivative Works as a whole, provided Your use,
  reproduction, and distribution of the Work otherwise complies with
  the conditions stated in this License.

5. Submission of Contributions. Unless You explicitly state otherwise,
  any Contribution intentionally submitted for inclusion in the Work
  by You to the Licensor shall be under the terms and conditions of
  this License, without any additional terms or conditions.
  Notwithstanding the above, nothing herein shall supersede or modify
  the terms of any separate license agreement you may have executed
  with Licensor regarding such Contributions.

6. Trademarks. This License does not grant permission to use the trade
  names, trademarks, service marks, or product names of the Licensor,
  except as required for reasonable and customary use in describing the
  origin of the Work and reproducing the content of the NOTICE file.

7. Disclaimer of Warranty. Unless required by applicable law or
  agreed to in writing, Licensor provides the Work (and each
  Contributor provides its Contributions) on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
  implied, including, without limitation, any warranties or conditions
  of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
  PARTICULAR PURPOSE. You are solely responsible for determining the
  appropriateness of using or redistributing the Work and assume any
  risks associated with Your exercise of permissions under this License.

8. Limitation of Liability. In no event and under no legal theory,
  whether in tort (including negligence), contract, or otherwise,
  unless required by applicable law (such as deliberate and grossly
  negligent acts) or agreed to in writing, shall any Contributor be
  liable to You for damages, including any direct, indirect, special,
  incidental, or consequential damages of any character arising as a
  result of this License or out of the use or inability to use the
  Work (including but not limited to damages for loss of goodwill,
  work stoppage, computer failure or malfunction, or any and all
  other commercial damages or losses), even if such Contributor
  has been advised of the possibility of such damages.

9. Accepting Warranty or Additional Liability. While redistributing
  the Work or Derivative Works thereof, You may choose to offer,
  and charge a fee for, acceptance of support, warranty, indemnity,
  or other liability obligations and/or rights consistent with this
  License. However, in accepting such obligations, You may act only
  on Your own behalf and on Your sole responsibility, not on behalf
  of any other Contributor, and only if You agree to indemnify,
  defend, and hold each Contributor harmless for any liability
  incurred by, or claims asserted against, such Contributor by reason
  of your accepting any such warranty or additional liability.

END OF TERMS AND CONDITIONS

APPENDIX: How to apply the Apache License to your work.

  To apply the Apache License to your work, attach the following
  boilerplate notice, with the fields enclosed by brackets "[]"
  replaced with your own identifying information. (Don't include
  the brackets!)  The text should be enclosed in the appropriate
  comment syntax for the file format. We also recommend that a
  file or class name and description of purpose be included on the
  same "printed page" as the copyright notice for easier
  identification within third-party archives.

Copyright [yyyy] [name of copyright owner]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## 7. Contact

If you have any questions or suggestions, please contact

Prof. Dr. [Thomas Weise](http://iao.hfuu.edu.cn/5) (汤卫思教授) of the 
Institute of Applied Optimization (应用优化研究所, [IAO](http://iao.hfuu.edu.cn)) of the
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd/)) at
[Hefei University](http://www.hfuu.edu.cn/english/) ([合肥学院](http://www.hfuu.edu.cn/)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
