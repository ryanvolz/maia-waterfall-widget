import importlib.metadata

try:
    __version__ = importlib.metadata.version("maia_waterfall_nicegui")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

from .waterfall import Waterfall

__all__ = ["Waterfall"]
