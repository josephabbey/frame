import asyncio
import logging
from logging.handlers import SocketHandler

from frame.loop import LOOP

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
)

from frame.layout import build_layout
from frame.ui import render

logger = logging.getLogger(__name__)
logging.getLogger("frame").setLevel(logging.DEBUG)
logging.getLogger("frame").addHandler(SocketHandler("127.0.0.1", 19996))


TODO_PERIOD = 60


async def refresh_loop():
  while True:
    try:
      logger.info("Regenerating layout")
      layout = await build_layout()
      with open("output.png", "wb") as f:
        (await render(layout, width=800, height=480)).save(f)
      await asyncio.sleep(TODO_PERIOD)
    except Exception as e:
      logger.error(e)
      await asyncio.sleep(5)


def debug():
  LOOP.create_task(refresh_loop())
  LOOP.run_forever()
