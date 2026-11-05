import io
import logging
import urllib.request

from PIL import Image

logger = logging.getLogger(__name__)


def image_from_url(url: str) -> Image.Image:
  logger.debug(f"Opening {url}")
  with urllib.request.urlopen(url) as res:
    data = res.read()
  img = Image.open(io.BytesIO(data))
  img.load()
  return img
