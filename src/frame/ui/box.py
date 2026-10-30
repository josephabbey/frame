from dataclasses import dataclass

from .drawing import Drawing
from .element import Element


@dataclass(kw_only=True)
class Box(Element):
    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        draw.rectangle(
            (x, y, x + width - 1, y + height - 1),
            self.bgcolor(self.scheme),
        )
