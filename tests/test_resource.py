"""Test the loading of resources."""

from bookbuilderpy.resources import load_resource
from bookbuilderpy.temp import TempDir


def test_resources() -> None:
    """Test access to resources."""
    with TempDir.create() as src, TempDir.create() as dst:
        for s in ["association-for-computing-machinery.csl",
                  "eisvogel.tex",
                  "GitHub.html5"]:
            load_resource(s, src, dst).ensure_file_exists()
