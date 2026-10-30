from dataclasses import dataclass
from enum import StrEnum
from math import cos, pi, sin

from PIL import Image as PILImage
from PIL import ImageDraw


class ShapeToken(StrEnum):
    NONE = "none"
    EXTRA_SMALL = "extra_small"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"
    FULL = "full"


class ShapeFamily(StrEnum):
    ROUNDED = "rounded"
    CUT = "cut"


class ShapeGeometry(StrEnum):
    RECTANGLE = "rectangle"
    ARCH = "arch"
    CIRCLE = "circle"
    OVAL = "oval"
    PILL = "pill"
    DIAMOND = "diamond"
    TRIANGLE = "triangle"
    SLANTED_SQUARE = "slanted_square"


_TOKEN_RADIUS: dict[ShapeToken, int | None] = {
    ShapeToken.NONE: 0,
    ShapeToken.EXTRA_SMALL: 4,
    ShapeToken.SMALL: 8,
    ShapeToken.MEDIUM: 12,
    ShapeToken.LARGE: 16,
    ShapeToken.EXTRA_LARGE: 28,
    ShapeToken.FULL: None,
}


@dataclass(frozen=True)
class Shape:
    """A semantic corner scale and family, optionally with a silhouette."""

    token: ShapeToken = ShapeToken.LARGE
    family: ShapeFamily = ShapeFamily.ROUNDED
    geometry: ShapeGeometry = ShapeGeometry.RECTANGLE
    radius: int | None = None
    # Clockwise from top-left. Use these for grouped containers and sheets.
    corners: tuple[ShapeToken, ShapeToken, ShapeToken, ShapeToken] | None = None


SHAPE_NONE = Shape(ShapeToken.NONE)
SHAPE_EXTRA_SMALL = Shape(ShapeToken.EXTRA_SMALL)
SHAPE_SMALL = Shape(ShapeToken.SMALL)
SHAPE_MEDIUM = Shape(ShapeToken.MEDIUM)
SHAPE_LARGE = Shape(ShapeToken.LARGE)
SHAPE_EXTRA_LARGE = Shape(ShapeToken.EXTRA_LARGE)
SHAPE_FULL = Shape(ShapeToken.FULL)
SHAPE_CUT_LARGE = Shape(ShapeToken.LARGE, ShapeFamily.CUT)
SHAPE_ARCH_LARGE = Shape(ShapeToken.LARGE, geometry=ShapeGeometry.ARCH)
SHAPE_OVAL = Shape(ShapeToken.FULL, geometry=ShapeGeometry.OVAL)
SHAPE_DIAMOND = Shape(ShapeToken.FULL, geometry=ShapeGeometry.DIAMOND)
SHAPE_EXTRA_LARGE_TOP = Shape(
    ShapeToken.EXTRA_LARGE,
    corners=(
        ShapeToken.EXTRA_LARGE,
        ShapeToken.EXTRA_LARGE,
        ShapeToken.NONE,
        ShapeToken.NONE,
    ),
)


def _radius(token: ShapeToken, width: int, height: int, scale: int) -> int:
    value = _TOKEN_RADIUS[token]
    return min(width, height) // 2 if value is None else value * scale


def _rounded_polygon(
    width: int, height: int, radii: tuple[int, int, int, int]
) -> list[tuple[float, float]]:
    tl, tr, br, bl = (min(r, width // 2, height // 2) for r in radii)
    corners = (
        (tl, tl, tl, pi, 1.5 * pi),
        (width - 1 - tr, tr, tr, 1.5 * pi, 2 * pi),
        (width - 1 - br, height - 1 - br, br, 0, 0.5 * pi),
        (bl, height - 1 - bl, bl, 0.5 * pi, pi),
    )
    points: list[tuple[float, float]] = []
    square_corners = ((0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1))
    for index, (cx, cy, radius, start, end) in enumerate(corners):
        if radius == 0:
            points.append(square_corners[index])
            continue
        for step in range(9):
            angle = start + (end - start) * step / 8
            points.append((cx + radius * cos(angle), cy + radius * sin(angle)))
    return points


def shape_mask(
    size: tuple[int, int], shape: Shape, *, scale: int = 1
) -> PILImage.Image:
    """Return a supersampled mask for a Material corner shape or crop silhouette."""
    width, height = size
    mask = PILImage.new("L", (max(1, width), max(1, height)), 0)
    draw = ImageDraw.Draw(mask)
    if width <= 0 or height <= 0:
        return mask

    if shape.geometry == ShapeGeometry.CIRCLE:
        diameter = min(width, height)
        left, top = (width - diameter) // 2, (height - diameter) // 2
        draw.ellipse((left, top, left + diameter - 1, top + diameter - 1), fill=255)
    elif shape.geometry == ShapeGeometry.OVAL:
        draw.ellipse((0, 0, width - 1, height - 1), fill=255)
    elif shape.geometry == ShapeGeometry.PILL:
        draw.rounded_rectangle(
            (0, 0, width - 1, height - 1), radius=min(width, height) // 2, fill=255
        )
    elif shape.geometry == ShapeGeometry.DIAMOND:
        draw.polygon(
            [
                (width // 2, 0),
                (width - 1, height // 2),
                (width // 2, height - 1),
                (0, height // 2),
            ],
            fill=255,
        )
    elif shape.geometry == ShapeGeometry.TRIANGLE:
        draw.polygon(
            [(width // 2, 0), (width - 1, height - 1), (0, height - 1)], fill=255
        )
    elif shape.geometry == ShapeGeometry.SLANTED_SQUARE:
        slant = min(width, height) // 5
        draw.polygon(
            [
                (slant, 0),
                (width - 1, 0),
                (width - 1 - slant, height - 1),
                (0, height - 1),
            ],
            fill=255,
        )
    elif shape.geometry == ShapeGeometry.ARCH:
        radius = min(width // 2, height // 2)
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
        draw.rectangle(
            (0, max(0, height - radius - 1), width - 1, height - 1), fill=255
        )
    else:
        if shape.radius is not None:
            custom_radius = shape.radius * scale
            radii = (custom_radius, custom_radius, custom_radius, custom_radius)
        elif shape.corners is not None:
            top_left, top_right, bottom_right, bottom_left = shape.corners
            radii = (
                _radius(top_left, width, height, scale),
                _radius(top_right, width, height, scale),
                _radius(bottom_right, width, height, scale),
                _radius(bottom_left, width, height, scale),
            )
        else:
            default_radius = _radius(shape.token, width, height, scale)
            radii = (default_radius, default_radius, default_radius, default_radius)
        if shape.family == ShapeFamily.ROUNDED:
            draw.polygon(_rounded_polygon(width, height, radii), fill=255)
        else:
            tl, tr, br, bl = (min(r, width // 2, height // 2) for r in radii)
            draw.polygon(
                [
                    (tl, 0),
                    (width - tr - 1, 0),
                    (width - 1, tr),
                    (width - 1, height - br - 1),
                    (width - br - 1, height - 1),
                    (bl, height - 1),
                    (0, height - bl - 1),
                    (0, tl),
                ],
                fill=255,
            )
    return mask
