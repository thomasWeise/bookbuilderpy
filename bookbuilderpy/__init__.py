"""bookbuilderpy is a package for compiling electronic books."""
from typing import Final
from bookbuilderpy.build import Build

import bookbuilderpy.version

__version__: Final[str] = bookbuilderpy.version.__version__

__all__ = (
    "Build",)
