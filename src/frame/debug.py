import asyncio
import logging
from logging.handlers import SocketHandler


def debug():
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
  )

  logger = logging.getLogger(__name__)
  logging.getLogger("frame").setLevel(logging.DEBUG)
  logging.getLogger("frame").addHandler(SocketHandler("127.0.0.1", 19996))

  from .layout import build_layout
  from .loop import LOOP
  from .ui import render

  TODO_PERIOD = 60

  async def refresh_loop():
    while True:
      try:
        logger.info("Regenerating layout")
        layout = await build_layout()
        with open("output.png", "wb") as f:
          (await render(layout, width=800, height=480)).save(f)
        await asyncio.sleep(TODO_PERIOD)
      except Exception:
        logger.exception("Found an error")
        await asyncio.sleep(5)

  LOOP.create_task(refresh_loop())
  LOOP.run_forever()
