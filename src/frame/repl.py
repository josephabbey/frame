import asyncio
import logging
import runpy
from logging.handlers import SocketHandler


def repl():
  logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
  )

  logger = logging.getLogger(__name__)
  logging.getLogger("frame").setLevel(logging.WARNING)
  logging.getLogger("frame").addHandler(SocketHandler("127.0.0.1", 19996))

  from .loop import LOOP

  class FrameLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def new_event_loop(self):
      return LOOP

  # Tell asyncio to use your existing LOOP instance
  asyncio.set_event_loop_policy(FrameLoopPolicy())

  # Launch Python's built-in asyncio REPL
  runpy.run_module("asyncio", run_name="__main__")
