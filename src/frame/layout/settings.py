from dataclasses import dataclass

from frame.settings import Settings


@dataclass(slots=True, kw_only=True)
class LayoutSettings(Settings):
  inset_left: int = 0
  inset_top: int = 0
  inset_right: int = 0
  inset_bottom: int = 0


LAYOUT_SETTINGS = LayoutSettings.load()
