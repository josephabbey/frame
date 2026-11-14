import logging
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from dacite import from_dict

from frame.utils import pickle

logger = logging.getLogger(__name__)

registry = []


def to_snake_case(text: str) -> str:
  return re.sub(
    "([a-z0-9])([A-Z])", r"\1_\2", re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
  ).lower()


def to_title_case(text: str) -> str:
  return re.sub(
    "([a-z0-9])([A-Z])", r"\1 \2", re.sub("(.)([A-Z][a-z]+)", r"\1 \2", text)
  ).title()


SETTINGS_PATH = (
  (Path(cast(str, os.environ.get("FRAME_SETTINGS_PATH"))))
  if ("FRAME_SETTINGS_PATH" in os.environ)
  else Path.home() / ".config/frame"
)


SETTINGS_PATH.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class Settings:
  _listeners: list[Callable[[Settings], None]] = field(default_factory=list)

  def __post_init__(self):
    registry.append(self)
    self.store()

  @classmethod
  def name(cls):
    return to_title_case(cls.__name__)

  @classmethod
  def path(cls):
    return SETTINGS_PATH / f"{to_snake_case(cls.__name__)}"

  def to_dict(self):
    return asdict(self)

  @classmethod
  def from_dict(cls, data: dict[str, Any]):
    return from_dict(cls, data)

  def store(self):
    with self.path().open("wb") as f:
      pickle.dump(self, f)

  @classmethod
  def load(cls):
    try:
      with cls.path().open("rb") as f:
        loaded = pickle.load_with_defaults(f)
        logger.info(f"Loaded settings: {cls.name()}")
        if isinstance(loaded, cls):
          return loaded
        else:
          raise TypeError(f"Invalid Settings for {cls.name()}")
    except FileNotFoundError:
      created = cls()
      created.store()
      logger.info(f"Created new settings: {cls.name()}")
      return created

  def __setattr__(self, key: str, value: Any):
    post_init = hasattr(self, key)
    super().__setattr__(key, value)
    if post_init:
      logger.info(f"Updated setting {key} on {self.name()}")
      self._notify()
      self.store()

  def add_listener(self, callback: Callable[[Any], None]) -> Callable[[], None]:
    """Register a callback for settings updates. Returns an unregister function."""

    def unsubscribe() -> None:
      if callback in self._listeners:
        self._listeners.remove(callback)

    self._listeners.append(callback)
    return unsubscribe

  def _notify(self) -> None:
    for listener in self._listeners:
      try:
        listener(self)
      except Exception:
        logger.debug("Settings listener failed", exc_info=True)
