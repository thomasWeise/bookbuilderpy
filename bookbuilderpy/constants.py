"""The basic preprocessor command strings."""

from typing import Final, Optional

#: the command for loading the input data
#: \rel.inputpath}
CMD_INPUT: Final[str] = "rel.input"

#: a relative code input to be included as a listing:
#: \rel.code{label}{caption}{path}{lines}{labels}{args}
#: label: the label of the listing
#: caption: the caption of the listing
#: path: the relative path fragment to resolve
#: lines: the lines of the code to keep, or empty to keep all
#: labels: the labels for selecting code pieces, or empty to keep all
#: args: any additional arguments to pass to the code renderer
CMD_RELATIVE_CODE: Final[str] = "rel.code"

#: an absolute code input to be included as a listing:
#: \abs.code{label}{caption}{path}{lines}{labels}{args}
#: label: the label of the listing
#: caption: the caption of the listing
#: path: the absolute path fragment to resolve
#: lines: the lines of the code to keep, or empty to keep all
#: labels: the labels for selecting code pieces, or empty to keep all
#: args: any additional arguments to pass to the code renderer
CMD_ABSOLUTE_CODE: Final[str] = "abs.code"

#: a git code include:
#: \git.code{repo}{label}{caption}{path}{lines}{labels}{args}
#: repo: the repository ID to use
#: label: the label of the listing
#: caption: the caption of the listing
#: path: the relative path fragment to resolve
#: lines: the lines of the code to keep, or empty to keep all
#: labels: the labels for selecting code pieces, or empty to keep all
#: args: any additional arguments to pass to the code renderer
CMD_GIT_CODE: Final[str] = "git.code"

#: a relative figure reference
#: \rel.figure{label}{caption}{path}{args}
CMD_RELATIVE_FIGURE: Final[str] = "rel.figure"

#: an absolute figure reference
#: \abs.figure{label}{caption}{path}{args}
CMD_ABSOLUTE_FIGURE: Final[str] = "abs.figure"

#: an command for formatting definitions
#: \definition{type}{label}{body}
CMD_DEFINITION: Final[str] = "definition"

#: reference a definition
#: \def.ref{label}
CMD_DEF_REF: Final[str] = "def.ref"

#: the meta data id for the current date
META_DATE: Final[str] = "date"
#: the meta data id for the current date and time
META_DATE_TIME: Final[str] = "time"
#: the meta data id for the current year
META_YEAR: Final[str] = "year"
#: the id of the language in which the project is currently built
# This property can either be set explicitly or is computed from the current
# language id. If the property is not set and there is not language id, then
# this defaults to "en".
META_LANG: Final[str] = "lang"
#: the locale of the current build language
# This property can either be set explicitly or it is computed from the
# current language id. If the language id is a prefix for well-known locales,
# the locale is expanded (e.g., "zh" -> "zh_CN", "en" -> "en_US"). If not,
# then the language id is used as locale. If the language id is not specified,
# then "en_US" is used.
META_LOCALE: Final[str] = "locale"

#: obtain a meta data element
#: \meta{id}
CMD_GET_META: Final[str] = "meta"

#: obtain information about a repository
#: \repo{repo-id}{info-id}
CMD_GET_REPO: Final[str] = "repo"

#: The key for the repository list
META_REPOS: Final[str] = "repos"
#: The key for the repository ID
META_REPO_ID: Final[str] = "id"
#: The key for the repository url
META_REPO_URL: Final[str] = "url"
#: the languages
META_LANGS: Final[str] = "langs"
#: the language id
META_LANG_ID: Final[str] = META_REPO_ID
#: the language name
META_LANG_NAME: Final[str] = "name"
#: The name of the current language.
META_CUR_LANG_NAME: Final[str] = f"{META_LANG}.{META_LANG_NAME}"

#: the key for the  repository name
META_REPO_INFO_NAME: Final[str] = "repo.name"
#: the key for the  repository
META_REPO_INFO_URL: Final[str] = "repo.url"
#: the key for the  repository commit
META_REPO_INFO_COMMIT: Final[str] = "repo.commit"
#: the key for the repository date
META_REPO_INFO_DATE: Final[str] = "repo.date"

#: A meta-data property identifying the website template markdown file.
# The website body markdown *can* contain a tag of the form
# '<div id="files">...</div>'.
# If it does, then this tag an all contents within will be replaced with
# an automatically generated list of files, relative links to files, and
# file sizes.
META_WEBSITE_BODY: Final[str] = "website_body"
#: The begin of the tag to be replaced.
WEBSITE_BODY_TAG_1: Final[str] = '<div id="files">'
#: The end of the tag to be replaced.
WEBSITE_BODY_TAG_2: Final[str] = '</div>'
#: A meta-data property identifying the HTML website wrapper file.
# If this file contains the string "{body}" somewhere, then we will load
# the markdown data identified by the "website_body" attribute, compile
# it, and replace the tag "{body}" with it.
META_WEBSITE_OUTER: Final[str] = "website_outer"
#: The outer tag of the website to be replaced with the body.
WEBSITE_OUTER_TAG: Final[str] = "{body}"
#: A meta-data property identifying the title of a book.
META_TITLE: Final[str] = "title"
#: A meta-data property identifying the author of a book.
META_AUTHOR: Final[str] = "author"

#: the Python programming language
LANG_PYTHON: Final[str] = "python"

#: the undefined programming language
LANG_UNDEFINED: Optional[str] = None

#: the pandoc markdown format
PANDOC_FORMAT_MARKDOWN: Final[str] = "markdown"
#: the pandoc latex format
PANDOC_FORMAT_LATEX: Final[str] = "latex"
#: the pandoc html5 format
PANDOC_FORMAT_HTML5: Final[str] = "html5"
#: the pandoc epub format
PANDOC_FORMAT_EPUB: Final[str] = "epub3"
#: the pandoc latex template
PANDOC_TEMPLATE_LATEX: Final[str] = "template.latex"
#: the pandoc html template
PANDOC_TEMPLATE_HTML5: Final[str] = "template.html"
#: the pandoc epub template
PANDOC_TEMPLATE_EPUB: Final[str] = "template.epub"
#: the csl template
PANDOC_CSL: Final[str] = "csl"
#: the pandoc bibliography key
PANDOC_BIBLIOGRAPHY: Final[str] = "bibliography"

#: The argument to the language list in the download files.
WEBSITE_LANGS_UL_ARG: Final[str] = ' class="langs"'
#: The argument to the language list item in the download files.
WEBSITE_LANGS_LI_ARG: Final[str] = ' class="oneLang"'
#: The argument to the language name item in the download files.
WEBSITE_LANGS_NAME_SPAN_ARG: Final[str] = ' class="oneLangName"'
#: The argument to the single language file download list.
WEBSITE_DOWNLOAD_UL_ARG: Final[str] = ' class="downloads"'
#: The argument to the single file download entry.
WEBSITE_DOWNLOAD_LI_ARG: Final[str] = ' class="download"'
#: The argument to the single file span entry.
WEBSITE_DOWNLOAD_DOWNLOAD_SPAN_ARG: Final[str] = ' class="downloadFile"'
#: The argument to the single file name span entry.
WEBSITE_DOWNLOAD_FILE_A_ARG: Final[str] = ' class="downloadFileName"'
#: The argument to the single file size span entry.
WEBSITE_DOWNLOAD_SIZE_SPAN_ARG: Final[str] = ' class="downloadFileSize"'
#: The argument to the single file description entry.
WEBSITE_DOWNLOAD_FILE_DESC_SPAN_ARG: Final[str] = ' class="downloadFileDesc"'
