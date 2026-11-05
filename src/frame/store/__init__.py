import logging
import pickle
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from dacite import from_dict

from frame.settings import SETTINGS_PATH

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


@dataclass(slots=True)
class Store:
  _listeners: list[Callable[[Store], None]] = field(default_factory=list)

  def __post_init__(self):
    registry.append(self)
    self.store()

  @classmethod
  def name(cls):
    return to_title_case(cls.__name__)

  @classmethod
  def path(cls):
    return SETTINGS_PATH / f"{to_snake_case(cls.__name__)}.store"

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
        loaded = pickle.load(f)
        logger.info(f"Loaded store: {cls.name()}")
        if isinstance(loaded, cls):
          return loaded
        else:
          raise TypeError(f"Invalid Store for {cls.name()}")
    except FileNotFoundError:
      created = cls()
      created.store()
      logger.info(f"Created new store: {cls.name()}")
      return created

  def __setattr__(self, key: str, value: Any):
    post_init = hasattr(self, key)
    super().__setattr__(key, value)
    if post_init:
      logger.info(f"Updated value {key} on {self.name()}")
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
        logger.debug("Store listener failed", exc_info=True)
