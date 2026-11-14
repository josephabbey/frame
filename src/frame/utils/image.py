import io
import logging

from PIL import Image

from frame.web import CLIENT

logger = logging.getLogger(__name__)


async def image_from_url(url: str) -> Image.Image:
  logger.debug(f"Opening {url}")
  data = await CLIENT.request(method="GET", url=url)
  img = Image.open(io.BytesIO(data))
  img.load()
  return img
