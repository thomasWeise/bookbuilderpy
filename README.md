[![make build](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml/badge.svg)](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml)

# bookbuilderpy

A [Python&nbsp;3](https://docs.python.org/3)-based environment for the automated compilation of books from markdown.

1. [Introduction](#1-introduction)
2. [Installation and Local Use](#2-installation-and-local-use)
3. [Provided Functionality](#3-provided-functionality)
   1. [Basic commands provided by `pandoc` and off-the-shelf filters](#31-basic-commands-provided-by-pandoc-and-off-the-shelf-filters)
   2. [`bookbuilderpy`-specific commands](#32-bookbuilderpy-specific-commands)
   3. [Metadata](#33-metadata)
      1. [Language Specification and Resolution](#331-language-specification-and-resolution)
      2. [Git Repositories](#332-git-repositories)
      3. [Website Construction](#333-website-construction)
      4. [Other Metadata](#334-other-metadata)
   4. [Graphics](#34-graphics)
4. [GitHub Pipeline](#4-github-pipeline)
      1. [The Repository](#41-the-repository)
      2. [The GitHub Action](#42-the-github-action)
5. [Related Projects and Components](#5-related-projects-and-components)
      1. [Own Contributed Projects and Components](#51-own-contributed-projects-and-components)
      2. [Related Projects and Components Used](#52-related-projects-and-components-used)
6. [License](#6-license)
      1. [Wandmalfarbe/pandoc-latex-template](#61-wandmalfarbepandoc-latex-template)
      2. [tajmone/pandoc-goodies HTML Template](#62-tajmonepandoc-goodies-html-template)
7. [Contact](#7-contact)

## 1. Introduction

The goal of this package is to provide you with a pipeline that can:
  - automatically compile books written in [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) to formats such as [pdf](https://www.iso.org/standard/75839.html), stand-alone [html](https://www.w3.org/TR/html5/), 
[epub](https://www.w3.org/publishing/epub32/), and [azw3](http://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf),
  - support a hierarchical file structure for the book sources, i.e., allow you divide the book into chapters in folders which can contain sub-folders with sections and sub-sub-folders with sub-sections,
  - support the automatic download and inclusion of code snippets from git repositories,
  - allow the book to be written in multiple languages, and finally
  - generate a website that lists all produced files so that you can copy everything to a web folder and offer your work for download without any further hassle.

This [Python&nbsp;3](https://docs.python.org/3) package requires that [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) must be installed.
Most likely, this package will only work under [Linux](https://www.linux.org) &ndash; at least I did not test it under Windows.
All commands and examples in the following require [Linux](https://www.linux.org).

## 2. Installation and Local Use

The following examples are for [Ubuntu](https://ubuntu.com) [Linux](https://www.linux.org).
Under other flavors, they may work differently and different commands may be required.
Execute the examples at your own risk.

You can easily install this package and its required packages using [`pip`](https://pypi.org/project/pip/) by doing

```shell
pip install git+https://github.com/thomasWeise/bookbuilderpy.git
```

If you want the full tool chain, though, you also need  [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) and run all of it on a Linux system.
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

If you want to try the above, you can clone the "minimal working example" repository [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe) and run the process to see what it does as follows **execute the code below at your own risk**:

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

```markdown
\newcommand{\mathSpace}[1]{\mathbb{#1}}
\newcommand{\realNumbers}{\mathSpace{R}}

Assume that $x\in\realNumbers$ is a value larger than $2$, then $\sqrt{x}>1$ is also true.
```

- Tables can be created as follows:

```markdown
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
- `\rel.code{label}{caption}{path}{lines}{labels}{args}` is used to include code (or portions of code) from a source code file located in the current folder (or any `path` beneath it). [Language-specific file resolution](#331-language-specification-and-resolution) will apply. This command has the following arguments:
  + `label`: the label of the listing, e.g., `something`. Will automatically be prefixed by `lst:` and can then be referenced in the text, e.g., as `The algorithm is specified in [@lst:something].`. 
  + `caption`: the caption of the listing
  + `path`: the relative path fragment to resolve
  + `lines`: the lines of the code to keep in the form `1-3,6`, or empty to keep all
  + `labels`: the labels for selecting code pieces, or empty to keep all. For instance, specifying `a,b` will keep all code between line comments `start a` and `end a` and `start b` and `end b`
  + args: any additional, language-specific arguments to pass to the code renderer. For python, we automatically strip type hints, docstrings, and comments from the code and also re-format the code. With `doc` you keep the docstrings, with `comments` you keep the comments, with `hints` you keep the type hints.
- `\git.code{repo}{label}{caption}{path}{lines}{labels}{args}` works the same as `\relative.code`, but uses code from the specified git repository instead (see [Metadata](#332-git-repositories)). [Language-specific file resolution](#331-language-specification-and-resolution) does *not* apply.
- `\rel.figure{label}{caption}{path}{args}` includes a figure into the book. [Language-specific file resolution](#331-language-specification-and-resolution) will apply. This command has the following arguments:
  + `label`: the label of the figure, e.g., `something`. It will be automatically prefixed by `fig:` can then be referenced in the text, e.g., as `As illustrated in [@fig:something], ...`.
  + `caption`: the caption of the figure
  + `path`: the relative path fragment to resolve
  + `args`: other arguments, e.g., `width=XX%` for making the figure having a width corresponding to `XX%` of the available with.
- `\definition{type}{label}{body}` creates a definition of the given type (where the metadata must somewhere specify `typeTitle`) that can be referenced via `\def.ref{label}` anywhere in the text. The body containing the actual definition of the definition is `body`. For example `\definition{def}{bla}{A *definition* is a text about something.}` with `defTitle: Definition` in the metadata would generate something like `**Definition 1**: A *definition* is a text about something.` and `\def.ref{bla}` would then become `Definition 1` (but as clickable hyperlink).
- `\meta{key}` any metadata string you specify in your [metadata](#33-metadata), including `title`, `author`, etc., with the following additional keys:
  + `time`: the ISO date and time when the book building process was started,
  + `date`: the ISO date when the book building process was started,
  + `year`: the year when the book building process was started,
  + `lang`: the current [language](#331-language-specification-and-resolution) id, or `en` if none is specified
  + `locale`: the locale inferred from the current language id
  + `name`: the current language name, or `English` if none is specified (this is a bit a dodgy property name, but for now I will stick with it&hellip;)
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
header-includes:
- |
  ```{=latex}
  \usepackage[section,above,below]{placeins}
  \let\Oldsubsection\subsection
  \renewcommand{\subsection}{\FloatBarrier\Oldsubsection}
  \addtolength{\topskip}{0pt plus 10pt}
  \interfootnotelinepenalty=10000
  \raggedbottom
  \usepackage[nameinlink]{cleveref}
  \crefname{chapter}{Chapter}{Chapters}
  \crefname{section}{Section}{Sections}
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
After that, the files in this folder will be deployed to the branch `gh-pages`, which will become the website for your book.

Let's say your username was `thomasWeise` and your book repository was `bookbuilderpy-mwe`.
To make this website visible, go to your GitHub project's [thomasWeise/bookbuilderpy-mwe](https://github.com/thomasWeise/bookbuilderpy-mwe), click `Settings`, then go to `Pages`, then under `Source` choose `gh-pages` and click `Save`.
A few minutes afterwards, your book's website will appear as <https://thomasweise.github.io/bookbuilderpy-mwe>.
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
- [docker](https://en.wikipedia.org/wiki/Docker_(software)), used to create containers in which all required software is pre-installed,
- [`cabal`](http://www.haskell.org/cabal/), the compilation and package management system via which pandoc is obtained,
- [`calibre`](http://calibre-ebook.com), which allows us to convert epub to awz3 files
- [`imagemagick`](http://www.imagemagick.org/) used by `pandoc` for image conversion
- [`ghostscript`](http://ghostscript.com/), used by our script to include all fonts into a pdf
- [`poppler-utils`](http://poppler.freedesktop.org/), used by our script for checking whether the pdfs are OK.

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

## 7. Contact

If you have any questions or suggestions, please contact

Prof. Dr. [Thomas Weise](http://iao.hfuu.edu.cn/5) (汤卫思教授) of the 
Institute of Applied Optimization (应用优化研究所, [IAO](http://iao.hfuu.edu.cn)) of the
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/jsjx/)) at
[Hefei University](http://www.hfuu.edu.cn/english/) ([合肥学院](http://www.hfuu.edu.cn/)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
