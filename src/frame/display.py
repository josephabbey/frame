import asyncio
import logging

from inky import Inky_Impressions_7


def display():

  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
  )

  logger = logging.getLogger(__name__)

  from .layout import build_layout
  from .loop import LOOP
  from .ui import render

  TODO_PERIOD = 1800
  assert TODO_PERIOD > 60  # Avoid overlapping writes

  async def refresh_loop():
    output = Inky_Impressions_7()
    output.set_border(output.WHITE)
    while True:
      layout = await build_layout()
      output.set_image(render(layout, width=output.width, height=output.height))
      output.show(busy_wait=False)
      await asyncio.sleep(TODO_PERIOD)

  LOOP.create_task(refresh_loop())
  LOOP.run_forever()
