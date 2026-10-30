from PIL import Image

from .drawing import Drawing
from .element import Element


def render(
    el: Element,
    width: int,
    height: int,
    *,
    supersample: int = 3,
    palette: list[tuple[int, int, int]] | None = None,
    dither: Image.Dither = Image.Dither.FLOYDSTEINBERG,
) -> Image.Image:
    """Render at elevated resolution, reduce cleanly, then map to Inky colors.

    The returned RGB image is suitable for ``Inky.set_image``. Impression 7-color
    panels support black, white, red, yellow, blue, green, and orange; ``palette``
    can be supplied to match a particular panel/driver revision.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if supersample < 1:
        raise ValueError("supersample must be at least 1")

    scale = supersample
    canvas = Image.new("RGB", (width * scale, height * scale), "white")
    photo_mask = Image.new("L", canvas.size, 0)
    draw = Drawing(canvas, scale, photo_mask)
    el.draw(draw, 0, 0, width * scale, height * scale)
    if scale > 1:
        canvas = canvas.resize((width, height), Image.Resampling.LANCZOS)
        photo_mask = photo_mask.resize((width, height), Image.Resampling.NEAREST)

    if palette is None:
        palette = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 0, 0),
            (255, 255, 0),
            (0, 0, 255),
            (0, 255, 0),
            (255, 128, 0),
        ]
    if palette:
        colors = [tuple(max(0, min(255, int(c))) for c in color) for color in palette]
        swatches = Image.new("P", (len(colors), 1))
        flat = [channel for color in colors for channel in color]
        swatches.putpalette(flat + [0] * (768 - len(flat)))
        clean = canvas.quantize(palette=swatches, dither=Image.Dither.NONE).convert(
            "RGB"
        )
        if dither == Image.Dither.NONE or photo_mask.getbbox() is None:
            return clean
        photographic = canvas.quantize(palette=swatches, dither=dither).convert("RGB")
        clean.paste(photographic, mask=photo_mask)
        return clean
    return canvas
