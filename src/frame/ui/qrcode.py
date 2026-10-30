from dataclasses import dataclass

import qrcode
import qrcode.constants

from .drawing import Drawing
from .element import Element


@dataclass(kw_only=True)
class QRCode(Element):
    data: str
    version = 1
    error_correction = qrcode.constants.ERROR_CORRECT_L
    quiet_zone: int = 4

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        qr = qrcode.QRCode(
            version=self.version,
            error_correction=self.error_correction,
            box_size=1,
            border=0,
        )
        qr.add_data(self.data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        count = len(matrix)
        scale = draw.frame_scale
        quiet_zone = max(0, self.quiet_zone)
        logical_module = min(width, height) // scale // (count + 2 * quiet_zone)
        if logical_module < 1:
            return

        # Keep every module an integer number of native display pixels. The
        # final supersample reduction therefore cannot interpolate QR edges.
        module_size = logical_module * scale
        code_size = count * module_size
        origin_x = x + ((width - code_size) // (2 * scale)) * scale
        origin_y = y + ((height - code_size) // (2 * scale)) * scale
        draw.rectangle(
            (x, y, x + width - 1, y + height - 1), fill=self.bgcolor(self.scheme)
        )
        for row, modules in enumerate(matrix):
            for column, dark in enumerate(modules):
                if dark:
                    left = origin_x + column * module_size
                    top = origin_y + row * module_size
                    draw.rectangle(
                        (left, top, left + module_size - 1, top + module_size - 1),
                        fill=self.fgcolor(self.scheme),
                    )
