from .element import Element
from PIL import Image, ImageDraw


def render(el: Element, width: int, height: int) -> Image.Image:
  buffer = Image.new(
    mode="RGB",
    size=(
      width,
      height
    ),
  )

  draw = ImageDraw.Draw(buffer)

  el.draw(
    draw,
    0, 0,
    width, height,
  )

  return buffer
