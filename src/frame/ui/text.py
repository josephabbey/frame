from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from PIL import ImageFont

from .color import Color, ColorValue
from .drawing import Drawing
from .element import Element
from .typography import MATERIAL_3_TYPE_SCALE, TypeStyle, TypographyRole


class TextAlign(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlign(StrEnum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


def _font_candidates(weight: int) -> list[Path]:
    face = "Bold" if weight >= 600 else "Medium" if weight >= 500 else "Regular"
    name = f"Roboto-{face}.ttf"
    roots = [
        Path.home() / ".fonts",
        Path.home() / ".local/share/fonts",
        Path("/usr/share/fonts/truetype/roboto"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/TTF"),
    ]
    candidates = [root / name for root in roots]
    candidates.extend(
        root / ("DejaVuSans-Bold.ttf" if weight >= 600 else "DejaVuSans.ttf")
        for root in roots
    )
    return candidates


def _load_font(path: str | None, size: int, weight: int) -> ImageFont.FreeTypeFont:
    candidates = [Path(path).expanduser()] if path else _font_candidates(weight)
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    return cast(ImageFont.FreeTypeFont, ImageFont.load_default(size=size))


def _set_variable_weight(font: ImageFont.FreeTypeFont, weight: int) -> None:
    """Set a variable font's wght axis when the chosen face provides one."""
    get_axes = getattr(font, "get_variation_axes", None)
    set_axes = getattr(font, "set_variation_by_axes", None)
    if get_axes is None or set_axes is None:
        return
    try:
        axes = get_axes()
        values = [axis["default"] for axis in axes]
        for index, axis in enumerate(axes):
            name = axis["name"]
            if isinstance(name, bytes):
                name = name.decode(errors="ignore")
            if str(name).lower() in {"weight", "wght"}:
                values[index] = min(axis["maximum"], max(axis["minimum"], weight))
        set_axes(values)
    except OSError, TypeError, ValueError, KeyError:
        return


@dataclass(kw_only=True)
class Text(Element):
    text: str
    role: TypographyRole = TypographyRole.BODY_LARGE
    size: int | None = None
    line_height: int | None = None
    font: str | None = None
    bold_font: str | None = None
    weight: int | None = None
    emphasized: bool = False
    letter_spacing: float | None = None
    tabular_numbers: bool = False
    type_scale: Mapping[TypographyRole, TypeStyle] | None = None
    color: Color | ColorValue | None = None
    align: TextAlign = TextAlign.LEFT
    valign: VerticalAlign = VerticalAlign.MIDDLE
    max_lines: int | None = None

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        scale = draw.frame_scale
        token = (self.type_scale or MATERIAL_3_TYPE_SCALE)[self.role]
        px_size = max(1, (self.size or token.size) * scale)
        leading = (self.line_height or token.line_height) * scale
        tracking = (
            token.tracking if self.letter_spacing is None else self.letter_spacing
        ) * scale
        weight = (
            self.weight
            if self.weight is not None
            else token.emphasized_weight
            if self.emphasized
            else token.weight
        )
        if self.emphasized and self.bold_font:
            font_path = self.bold_font
        else:
            font_path = self.font
        face = _load_font(font_path, px_size, weight)
        if self.font:
            _set_variable_weight(face, weight)
        line_height = max(px_size, leading)
        ascent, descent = face.getmetrics()
        half_leading = max(0, line_height - ascent - descent) // 2
        features = ["tnum"] if self.tabular_numbers else None

        def text_width(value: str) -> float:
            return (
                draw.textlength(value, font=face, features=features)
                + (len(value) - 1) * tracking
            )

        lines: list[str] = []
        for paragraph in self.text.splitlines() or [""]:
            current = ""
            for word in paragraph.split():
                candidate = f"{current} {word}" if current else word
                if current and text_width(candidate) > width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        line_limit = max(0, height // line_height)
        if self.max_lines is not None:
            line_limit = min(line_limit, self.max_lines)
        truncated = len(lines) > line_limit
        lines = lines[:line_limit]
        if truncated and lines:
            last = lines[-1].rstrip()
            while last and text_width(last + "…") > width:
                last = last[:-1]
            lines[-1] = last + "…"

        total_height = line_height * len(lines)
        if self.valign == VerticalAlign.TOP:
            top = y
        elif self.valign == VerticalAlign.MIDDLE:
            top = y + (height - total_height) // 2
        else:
            top = y + height - total_height
        if self.color is None:
            fill = self.fgcolor(self.scheme)
        elif isinstance(self.color, Color):
            fill = self.color(self.scheme)
        else:
            fill = self.color
        for index, line in enumerate(lines):
            line_width = text_width(line)
            if self.align == TextAlign.LEFT:
                left = x
            elif self.align == TextAlign.CENTER:
                left = x + (width - line_width) // 2
            else:
                left = x + width - line_width
            baseline = top + index * line_height + half_leading + ascent
            if tracking == 0:
                draw.text(
                    (left, baseline),
                    line,
                    font=face,
                    fill=fill,
                    anchor="ls",
                    features=features,
                )
                continue
            cursor = left
            for character in line:
                draw.text(
                    (cursor, baseline),
                    character,
                    font=face,
                    fill=fill,
                    anchor="ls",
                    features=features,
                )
                cursor += (
                    draw.textlength(character, font=face, features=features) + tracking
                )
