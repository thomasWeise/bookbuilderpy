[![make build](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml/badge.svg)](https://github.com/thomasWeise/bookbuilderpy/actions/workflows/build.yaml)

# bookbuilderpy

A Python&nbsp;3-based environment for the automated compilation of books from markdown.

## 1. Introduction

The goal of this package is to provide you with a pipeline that can:
  - automatically compile books written in [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) to formats such as [pdf](https://www.iso.org/standard/75839.html), stand-alone [html](https://www.w3.org/TR/html5/), 
[epub](https://www.w3.org/publishing/epub32/), and [azw3](http://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf),
  - support a hierarchical file structure for the book sources, i.e., allow you divide the book into chapters in folders which can contain sub-folders with sections and sub-sub-folders with sub-sections,
  - support the automatic download and inclusion of code snippets from git repositories,
  - allow the book to be written in multiple languages, and finally
  - generate a website that lists all produced files so that you can copy everything to a web folder and offer your work for download without any further hassle.

This python package requires that [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) must be installed.
Most likely, this package will only work under Linux - at least I did not test it under Windows.

## 2. Installation

You can easily install this package and its required packages using [`pip`](https://pypi.org/project/pip/) by doing

```shell
pip install git+https://github.com/thomasWeise/bookbuilderpy.git
```

If you want the full tool chain, though, you also need  [pandoc](http://pandoc.org/), [TeX Live](http://tug.org/texlive/), and [calibre](http://calibre-ebook.com) and run all of it on a Linux system.
So it might be easier to just use the [docker container](http://hub.docker.com/r/thomasweise/docker-bookbuilder/) that comes with everything pre-installed.
You can then run it as:

```shell
docker run -v "INPUT_DIR":/input/ \
           -v "OUTPUT_DIR":/output/ \
           -t -i thomasweise/docker-bookbuilderpy BOOK_ROOT_MD_FILE
```

Here, it is assumed that

- `INPUT_DIR` is the directory where your book sources reside, let's say `/home/my/book/sources/`.
- `BOOK_ROOT_MD_FILE` is the root file of your book, say `book.md` (in which case, the full path of `book.md` would be `/home/my/book/sources/book.md`). Notice that you can specify only a single file, but this file can reference other files in sub-directories of `INPUT_DIR` by using commands such as  `\rel.input` (see [below](#32-bookbuilderpy-specific-commands)).
- `OUTPUT_DIR` is the output directory where the compiled files should be placed, e.g., `/home/my/book/compiled/`. This is where the resulting files will be placed.

## 3. Provided Functionality

## 3.1. Basic commands provided by `pandoc` and off-the-shelf filters

The following basic commands are already available in pandoc's [markdown](http://pandoc.org/MANUAL.html#pandocs-markdown) flavor and/or are provided by the existing pandoc plugins that we use:

- Chapters, sections, sub-sections etc. are created by putting their title on a single line preceded by `#`, `##`, or `###`, etc. For example, the line `## This is a section` starts a section with the given title. 
- You can use LaTeX maths as inline formulae such `$\sqrt{5}+4^4$` and as stand-alone equations like `$$x=\frac{5}{6}$$`. A line such as `$$ x = y + z $$ {#eq:xyz}` will create an equation that can be referenced using `[@eq:xyz]` in the text.
- References to bibliography can be done `[@ABC; @DEF]` where `ABC` and `DEF` would then be keys into your BibTeX file, which, in turn, would be specified in the metadata as `bibliography: bibtexfile.bib`. 

## 3.2. `bookbuilderpy`-specific commands

The following new commands are added:

- `\rel.input{path}` recursively includes and processes the contents of the file identified by `path`. `path` must be in a sub-folder of the current folder. The deepest folder of the new full path will become the current folder for any (recursive) `\rel.input{path}` invocations in the new file as well as `\rel.code` and `\rel.figure` commands. [Language-specific file resolution](#331-language-specification-and-resolution) will apply.
- `\relative.code{label}{caption}{path}{lines}{labels}{args}` is used to include code (or portions of code) from a source code file located in the current folder (or any `path` beneath it). [Language-specific file resolution](#331-language-specification-and-resolution) will apply. This command has the following arguments:
  + `label`: the label of the listing, must be of the form `lst:something` and can then be referenced in the text as `[@lst:something]`. 
  + `caption`: the caption of the listing
  + `path`: the relative path fragment to resolve
  + `lines`: the lines of the code to keep in the form `1-3,6`, or empty to keep all
  + `labels`: the labels for selecting code pieces, or empty to keep all. For instance, specifying `a,b` will keep all code between line comments `start a` and `end a` and `start b` and `end b`
  + args: any additional, language-specific arguments to pass to the code renderer. For python, we automatically strip type hints, docstrings, and comments from the code and also re-format the code. With `doc` you keep the docstrings, with `comments` you keep the comments, with `hints` you keep the type hints.
- `\git.code{repo}{label}{caption}{path}{lines}{labels}{args}` works the same as `\relative.code`, but uses code from the specified git repository instead (see [Metadata](#332-git-repositories)). [Language-specific file resolution](#331-language-specification-and-resolution) does *not* apply.
- `\rel.figure{label}{caption}{path}{args}` includes a figure into the book. [Language-specific file resolution](#331-language-specification-and-resolution) will apply. This command has the following arguments:
  + `label`: the label of the figure, must be of the form `fig:something` and can then be referenced in the text as `[@fig:something]`.
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

You can develop your book in one single language or in multiple languages in parallel.
The language(s) can be specified in the metadata following the pattern below:

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

If and only you specify multiple locales, then the language `id` has one very important purpose:
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
The idea is that the "inner" website could be the README.md file of the repository where your book is and the outer website allows you to specify a container and proper CSS styles for rendering it.
This mechanism works as follows:

The inner website is loaded as a string.
It can contain the text `{body}` exactly once and this text is then replaced by the rendered markdown of the inner website.
The inner website must somewhere contain a div tag `<div id="files"> .... </div>`.
This tag and everything inside will be replaced with an automatically generated list of all the generated files.
If the [`langs` attribute](#331-language-specification-and-resolution) is specified, there will be one nested list per language.
The lists will have the following CSS-classes:

- `langs`: for the main list of multiple languages
- `oneLang`: for the language list item
- `oneLangName`: for the span with the language name
- `downloads`: for the download list per language
- `download`: for the download list entry
- `downloadFile`: for the span containing the file download
- `downloadFileName`: for the span with the file name
- `downloadFileSize`: for the span with the file size
- `downloadFileDesc`: for the description of the file format

The result of this rendering process is then stored in a file `index.html`.

### 3.3.4. Other Metadata

- `title`: the book's title
- `keywords`: a list of keywords
- `author`: the book author or a list of authors
- `date`: the date when the book was written (you can set this to `\meta{data}` and the current date of the build process will be used).
- `bibliography`: the path to the BibTeX file, e.g., `bibliography.bib`
- `csl`: the bibliography style. Set this to `association-for-computing-machinery.csl` to use the default style offered by the package.
- `link-citations`: set this to `true` to get clickable bibliography references
- `template.html`: the template for rendering to HTML. Set this to `GitHub.html5` to use the default style offered by the package.
- `template.latex`: the template for rendering to PDF. Set this to `eisvogel.tex` to use the default style offered by the package.
- The language-specific component titles explained-by-example are already supported by pandoc and its filters:

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
- Any other `xxxTitle` allows you to specify a `type`to be used for a `\definition{type}{label}{body}` command.
- `header-includes`: allows you to insert stuff into the headers of the format. For PDF/LaTeX, it is useful to put something like the stuff below, as it will make the result nicer if you have many code listings:
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
```

- Setup for pandoc's crossref: You may wish to include the following text
```yaml
# pandoc-crossref setup
cref: true
chapters: true
linkReferences: true
listings: false
codeBlockCaptions: true
```


## 4. License

The copyright holder of this package is Prof. Dr. Thomas Weise (see Contact).
The package is licensed under the GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.
This package also contains third-party components which are under the following licenses;

### 4.1. [Wandmalfarbe/pandoc-latex-template](http://github.com/Wandmalfarbe/pandoc-latex-template)

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
    
### 4.2 [tajmone/pandoc-goodies HTML Template](http://github.com/tajmone/pandoc-goodies)

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


## 5. Contact

If you have any questions or suggestions, please contact

Prof. Dr. [Thomas Weise](http://iao.hfuu.edu.cn/5) (汤卫思教授) of the 
Institute of Applied Optimization (应用优化研究所, [IAO](http://iao.hfuu.edu.cn)) of the
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/jsjx/)) at
[Hefei University](http://www.hfuu.edu.cn/english/) ([合肥学院](http://www.hfuu.edu.cn/)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
