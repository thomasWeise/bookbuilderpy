"""The basic preprocessor command strings."""

from typing import Final, Optional

#: the command for loading the input data
#: \relative.input{path}
CMD_INPUT: Final[str] = "relative.input"

#: a relative code input to be included as a listing:
#: \relative.code{label}{caption}{path}{lines}{labels}{args}
#: label: the label of the listing
#: caption: the caption of the listing
#: path: the relative path fragment to resolve
#: lines: the lines of the code to keep, or empty to keep all
#: labels: the labels for selecting code pieces, or empty to keep all
#: args: any additional arguments to pass to the code renderer
CMD_RELATIVE_CODE: Final[str] = "relative.code"

#: an absolute code input to be included as a listing:
#: \absolute.code{label}{caption}{path}{lines}{labels}{args}
#: label: the label of the listing
#: caption: the caption of the listing
#: path: the absolute path fragment to resolve
#: lines: the lines of the code to keep, or empty to keep all
#: labels: the labels for selecting code pieces, or empty to keep all
#: args: any additional arguments to pass to the code renderer
CMD_ABSOLUTE_CODE: Final[str] = "absolute.code"

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
#: \\relative.figure{label}{caption}{path}{args}
CMD_RELATIVE_FIGURE: Final[str] = "relative.figure"

#: an absolute figure reference
#: \\absolute.figure{label}{caption}{path}{args}
CMD_ABSOLUTE_FIGURE: Final[str] = "absolute.figure"

#: the meta data id for the current date
META_DATE: Final[str] = "date"
#: the meta data id for the current date and time
META_DATE_TIME: Final[str] = "time"
#: the meta data id for the current year
META_YEAR: Final[str] = "year"
#: the meta-information about the commit
META_GIT_COMMIT: Final[str] = "gitcommit"
#: the url to the git repository
META_GIT_URL: Final[str] = "giturl"
#: the git commit date and time
META_GIT_DATE: Final[str] = "gitdate"
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
#: \\meta{id}
CMD_GET_META: Final[str] = "meta"

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
#: the language namehe
META_LANG_NAME: Final[str] = "name"
#: The name of the current language.
META_CUR_LANG_NAME: Final[str] = f"{META_LANG}.{META_LANG_NAME}"

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
