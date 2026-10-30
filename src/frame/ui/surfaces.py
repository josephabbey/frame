from dataclasses import dataclass, field

from PIL import Image as PILImage
from PIL import ImageChops

from .color import SURFACE_CONTAINER, Color
from .drawing import Drawing
from .element import Element
from .layout import Column
from .shapes import SHAPE_MEDIUM, Shape, shape_mask
from .spacing import SPACE_200, SpacingToken


@dataclass(kw_only=True)
class RoundedBox(Element):
    shape: Shape = SHAPE_MEDIUM
    radius: int | None = None
    outline: Color | None = None
    outline_width: int = 0

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        scale = draw.frame_scale
        width_px = max(1, self.outline_width * scale)
        shape = (
            Shape(
                token=self.shape.token,
                family=self.shape.family,
                geometry=self.shape.geometry,
                radius=self.radius,
                corners=self.shape.corners,
            )
            if self.radius is not None
            else self.shape
        )
        mask = shape_mask((width, height), shape, scale=scale)
        draw._image.paste(self.bgcolor(self.scheme), (x, y), mask)
        if self.outline:
            inner = PILImage.new("L", (width, height), 0)
            inner_size = (max(1, width - 2 * width_px), max(1, height - 2 * width_px))
            inner_mask = shape_mask(inner_size, shape, scale=scale)
            inner.paste(inner_mask, (width_px, width_px))
            border = ImageChops.subtract(mask, inner)
            draw._image.paste(self.outline(self.scheme), (x, y), border)


@dataclass(kw_only=True)
class Card(RoundedBox):
    bgcolor: Color = SURFACE_CONTAINER
    shape: Shape = SHAPE_MEDIUM
    children: list[Element] = field(default_factory=list)
    content_padding: int | SpacingToken = SPACE_200

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        super().draw(draw, x, y, width, height)
        Column(
            scheme=self.scheme,
            spacing=self.spacing,
            children=self.children,
            padding=self.content_padding,
        ).draw(draw, x, y, width, height)
