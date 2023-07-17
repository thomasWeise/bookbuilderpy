"""bookbuilderpy is a package for compiling electronic books."""
from typing import Final

import bookbuilderpy.version
from bookbuilderpy.build import Build

__version__: Final[str] = bookbuilderpy.version.__version__

__all__ = (
    "Build",)
