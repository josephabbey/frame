from inky.auto import auto
from inky.inky import Inky
from material_color_utilities import theme_from_color

from frame.ui import QRCode, render

layout = QRCode(
    scheme=theme_from_color("#f00").schemes.light, data="https://josephabbey.dev"
)


def debug():
    render(layout, width=800, height=480).show()


def display():
    output: Inky = auto()
    output.set_border(output.WHITE)
    output.set_image(render(layout, width=output.width, height=output.height))
    output.show()
