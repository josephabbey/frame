from dataclasses import dataclass

from frame.settings import Settings


@dataclass(slots=True, kw_only=True)
class LayoutSettings(Settings):
  inset_left = 0
  inset_top = 0
  inset_right = 0
  inset_bottom = 0


LAYOUT_SETTINGS = LayoutSettings.load()
