"""The package containing the pre-defined bookbuilderpy resources."""
from typing import Final

import bookbuilderpy.version
from bookbuilderpy.resources._resource import load_resource
from bookbuilderpy.resources._resource_server import ResourceServer

__version__: Final[str] = bookbuilderpy.version.__version__

__all__ = ("load_resource",
           "ResourceServer")
