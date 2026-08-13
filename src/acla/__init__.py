"""A-CLA reference package."""

from .nonoverlap import detect_nonoverlapping
from .overlap import detect_overlap_extension

__all__ = ["detect_nonoverlapping", "detect_overlap_extension"]
__version__ = "1.0.0"
