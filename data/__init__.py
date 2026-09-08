"""Instance generation and data loaders for MMCLBP."""

from .data import Data
from .virginia_beach import load_virginia_beach_instance

__all__ = ["Data", "load_virginia_beach_instance"]
