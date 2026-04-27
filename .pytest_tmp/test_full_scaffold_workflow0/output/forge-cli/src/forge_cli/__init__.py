"""forge-cli — CLI tool (Python)."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__: str = _pkg_version("forge-cli")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"
