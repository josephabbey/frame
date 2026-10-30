from abc import ABC, abstractmethod
from dataclasses import dataclass

from material_color_utilities import DynamicScheme

from .color import BACKGROUND, ON_SURFACE, Color
from .drawing import Drawing
from .spacing import M3_SPACING, Spacing


@dataclass(kw_only=True)
class Element(ABC):
    """A noninteractive drawable in logical (native display pixel) units."""

    scheme: DynamicScheme
    bgcolor: Color = BACKGROUND
    fgcolor: Color = ON_SURFACE
    spacing: Spacing = M3_SPACING

    @abstractmethod
    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        """Draw into the high-resolution render surface."""
