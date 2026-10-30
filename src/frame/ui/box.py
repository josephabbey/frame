from dataclasses import dataclass

from PIL.ImageDraw import ImageDraw

from .element import Element


@dataclass(kw_only=True)
class Box(Element):
    def draw(self, draw: ImageDraw, x: int, y: int, width: int, height: int):
        draw.rectangle(
            (x, y, x + width, y + height),
            self.bgcolor(self.scheme),
        )
