from dataclasses import dataclass, field
from enum import StrEnum

from .drawing import Drawing
from .element import Element
from .spacing import SPACE_0, SPACE_200, SpacingToken


class Axis(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Alignment(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


@dataclass(kw_only=True)
class Spacer(Element):
    """An empty flex child. Its ``flex_weight`` controls free-space share."""

    flex_weight: float = 1

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        pass


@dataclass(kw_only=True)
class Stack(Element):
    """Lay children out on one axis, distributing remaining space by weight."""

    children: list[Element] = field(default_factory=list)
    axis: Axis = Axis.VERTICAL
    gap: int | SpacingToken = SPACE_0
    padding: int | SpacingToken = SPACE_0
    cross_align: Alignment = Alignment.STRETCH
    main_align: Alignment = Alignment.START
    weights: list[float] | None = None
    main_sizes: list[int | None] | None = None

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        if not self.children:
            return
        vertical = self.axis == Axis.VERTICAL
        main_size = height if vertical else width
        cross_size = width if vertical else height
        scale = draw.frame_scale
        inset = self.spacing.resolve(self.padding) * scale
        main_size = max(0, main_size - 2 * inset)
        cross_size = max(0, cross_size - 2 * inset)
        gap = max(0, self.spacing.resolve(self.gap) * scale)
        available = max(0, main_size - gap * (len(self.children) - 1))
        weights = self.weights or [
            getattr(child, "flex_weight", 1) for child in self.children
        ]
        weights = (weights + [0] * len(self.children))[: len(self.children)]
        main_sizes = (self.main_sizes or [None] * len(self.children))[
            : len(self.children)
        ]
        main_sizes += [None] * (len(self.children) - len(main_sizes))
        scale = draw.frame_scale
        main_sizes = [None if size is None else size * scale for size in main_sizes]
        fixed_total = sum(max(0, size) for size in main_sizes if size is not None)
        fixed = [max(0, size) if size is not None else 0 for size in main_sizes]
        flex_space = max(0, available - fixed_total)
        total_weight = sum(
            max(0, w) for i, w in enumerate(weights) if main_sizes[i] is None
        )
        sizes = [fixed[i] for i in range(len(self.children))]
        for i, size in enumerate(main_sizes):
            if size is None and total_weight:
                sizes[i] = int(flex_space * max(0, weights[i]) / total_weight)
        # Put rounding remainder in the final flexible child.
        if total_weight:
            flex_indices = [i for i, size in enumerate(main_sizes) if size is None]
            sizes[flex_indices[-1]] += flex_space - sum(sizes[i] for i in flex_indices)
        used = sum(sizes) + gap * (len(self.children) - 1)
        cursor = inset + (
            max(0, main_size - used) // 2
            if self.main_align == Alignment.CENTER
            else max(0, main_size - used)
            if self.main_align == Alignment.END
            else 0
        )
        for child, child_main in zip(self.children, sizes):
            child_cross = cross_size
            cross_offset = inset
            if self.cross_align != Alignment.STRETCH:
                # Fixed-size children may advertise a preferred cross dimension.
                preferred = getattr(child, "preferred_size", None)
                child_cross = min(cross_size, preferred) if preferred else cross_size
                if self.cross_align == Alignment.CENTER:
                    cross_offset += (cross_size - child_cross) // 2
                elif self.cross_align == Alignment.END:
                    cross_offset += cross_size - child_cross
            if vertical:
                child.draw(draw, x + cross_offset, y + cursor, child_cross, child_main)
            else:
                child.draw(draw, x + cursor, y + cross_offset, child_main, child_cross)
            cursor += child_main + gap


@dataclass(kw_only=True)
class Column(Stack):
    axis: Axis = Axis.VERTICAL


@dataclass(kw_only=True)
class Row(Stack):
    axis: Axis = Axis.HORIZONTAL


@dataclass(kw_only=True)
class Padding(Element):
    child: Element
    inset: int | SpacingToken = SPACE_200

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        inset = max(0, self.spacing.resolve(self.inset) * draw.frame_scale)
        self.child.draw(
            draw,
            x + inset,
            y + inset,
            max(0, width - 2 * inset),
            max(0, height - 2 * inset),
        )


@dataclass(kw_only=True)
class Center(Element):
    child: Element
    width: int | None = None
    height: int | None = None

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        scale = draw.frame_scale
        child_width = (
            min(width, self.width * scale) if self.width is not None else width
        )
        child_height = (
            min(height, self.height * scale) if self.height is not None else height
        )
        self.child.draw(
            draw,
            x + (width - child_width) // 2,
            y + (height - child_height) // 2,
            child_width,
            child_height,
        )
