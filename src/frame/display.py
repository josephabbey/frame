import asyncio
import logging

from inky import Inky_Impressions_7

from frame.layout import build_layout

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
)

from frame.ui import render

logger = logging.getLogger(__name__)


TODO_PERIOD = 5


async def refresh_loop():
  output = Inky_Impressions_7()
  output.set_border(output.WHITE)
  while True:
    layout = await build_layout()
    output.set_image(render(layout, width=output.width, height=output.height))
    output.show()
    await asyncio.sleep(TODO_PERIOD)


def display():
  loop = asyncio.new_event_loop()
  loop.create_task(refresh_loop())
  loop.run_forever()
