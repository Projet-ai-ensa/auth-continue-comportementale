import sys
from pathlib import Path

# Folder of the whole project (one level above tests/)
ROOT = Path(__file__).resolve().parent.parent


def test_python_version():
    # The README says the project needs Python 3.11 or newer
    assert sys.version_info >= (3, 11)


def test_readme_exists():
    # The project must have its README at the root
    assert (ROOT / "README.md").exists()