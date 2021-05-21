"""The basic preprocessor command strings."""

from typing import Final

#: the command for loading the input data
CMD_INPUT: Final[str] = "relative.input"

#: the meta data id for the date
META_DATE: Final[str] = "date"
#: the meta data id for the date and time
META_DATE_TIME: Final[str] = "time"

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
