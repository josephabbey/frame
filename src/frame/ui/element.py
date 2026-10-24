from abc import ABC, abstractmethod
from dataclasses import dataclass

from material_color_utilities import DynamicScheme
from PIL.ImageDraw import ImageDraw

from .color import BACKGROUND, ON_SURFACE, Color


@dataclass(kw_only=True)
class Element(ABC):
    scheme: DynamicScheme
    bgcolor: Color = BACKGROUND
    fgcolor: Color = ON_SURFACE

    @abstractmethod
    def draw(self, draw: ImageDraw, x: int, y: int, width: int, height: int):
        pass
