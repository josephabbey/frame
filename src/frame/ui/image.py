from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PIL import Image as PILImage

from .drawing import Drawing
from .element import Element
from .shapes import Shape, shape_mask


class ImageFit(StrEnum):
    COVER = "cover"
    CONTAIN = "contain"
    FILL = "fill"


ImageSource = str | Path | PILImage.Image


@dataclass(kw_only=True)
class Image(Element):
    """Photograph element with contain/cover scaling and optional focal point."""

    source: ImageSource
    fit: ImageFit = ImageFit.COVER
    focal_point: tuple[float, float] = (0.5, 0.5)
    shape: Shape | None = None

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        image = (
            self.source.copy()
            if isinstance(self.source, PILImage.Image)
            else PILImage.open(self.source)
        )
        image = image.convert("RGB")
        if self.fit == ImageFit.FILL:
            fitted = image.resize((width, height), PILImage.Resampling.LANCZOS)
        else:
            factor = (
                max(width / image.width, height / image.height)
                if self.fit == ImageFit.COVER
                else min(width / image.width, height / image.height)
            )
            size = (
                max(1, round(image.width * factor)),
                max(1, round(image.height * factor)),
            )
            resized = image.resize(size, PILImage.Resampling.LANCZOS)
            if self.fit == ImageFit.COVER:
                fx, fy = self.focal_point
                left = round((resized.width - width) * min(1, max(0, fx)))
                top = round((resized.height - height) * min(1, max(0, fy)))
                fitted = resized.crop((left, top, left + width, top + height))
            else:
                fitted = PILImage.new("RGB", (width, height), self.bgcolor(self.scheme))
                fitted.paste(
                    resized,
                    ((width - resized.width) // 2, (height - resized.height) // 2),
                )
        mask = (
            shape_mask((width, height), self.shape, scale=draw.frame_scale)
            if self.shape
            else None
        )
        draw._image.paste(fitted, (x, y), mask)
        if draw.photo_mask is not None:
            if mask is not None:
                draw.photo_mask.paste(255, (x, y), mask)
            else:
                draw.photo_mask.paste(255, (x, y, x + fitted.width, y + fitted.height))
