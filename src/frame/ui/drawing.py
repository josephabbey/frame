from PIL import Image
from PIL.ImageDraw import ImageDraw


class Drawing(ImageDraw):
    """Pillow drawing surface plus frame rendering context."""

    frame_scale: int
    photo_mask: Image.Image

    def __init__(self, image: Image.Image, frame_scale: int, photo_mask: Image.Image):
        super().__init__(image)
        self.frame_scale = frame_scale
        self.photo_mask = photo_mask
