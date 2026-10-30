from dataclasses import dataclass

import qrcode
import qrcode.constants
from PIL.ImageDraw import ImageDraw

from .element import Element


@dataclass(kw_only=True)
class QRCode(Element):
    data: str
    version = 1
    error_correction = qrcode.constants.ERROR_CORRECT_L

    def draw(self, draw: ImageDraw, x: int, y: int, width: int, height: int):
        qr = qrcode.QRCode(
            version=self.version, error_correction=self.error_correction, box_size=1
        )
        qr.add_data(self.data)
        qr.make(fit=True)
        draw._image.paste(
            qr.make_image(
                fill_color=self.fgcolor(self.scheme),
                back_color=self.bgcolor(self.scheme),
            )
            .get_image()
            .resize((width, height)),
            (x, y),
        )
