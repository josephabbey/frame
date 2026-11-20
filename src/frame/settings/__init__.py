import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import MISSING, asdict, dataclass, field, fields
from typing import Any

from dacite import from_dict

from frame.flow.client import FLOW_CLIENT
from frame.store import SETTINGS_PATH
from frame.utils import pickle

logger = logging.getLogger(__name__)

registry: dict[str, Settings] = {}


def to_snake_case(text: str) -> str:
  return re.sub(
    "([a-z0-9])([A-Z])", r"\1_\2", re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
  ).lower()


def to_title_case(text: str) -> str:
  return re.sub(
    "([a-z0-9])([A-Z])", r"\1 \2", re.sub("(.)([A-Z][a-z]+)", r"\1 \2", text)
  ).title()


SETTINGS_PATH.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class Settings:
  _listeners: list[Callable[[Settings], None]] = field(default_factory=list)

  def __post_init__(self):
    registry[self.key()] = self

  @classmethod
  def key(cls):
    return cls.__name__

  @classmethod
  def name(cls):
    return to_title_case(cls.__name__)

  @classmethod
  def path(cls):
    return SETTINGS_PATH / f"{to_snake_case(cls.__name__)}"

  @classmethod
  def static_details(cls) -> dict[str, dict]:
    ret = {
      f.name: {
        "name": (f.name).replace("_", " ").title(),
        "type": f.type.__name__,
        "default": f.default if f.default is not MISSING else None,
      }
      for f in fields(cls)
    }
    ret.pop("_listeners")
    return ret

  def details(self) -> dict[str, dict]:
    return {
      key: {
        **details,
        "value": self.__getattribute__(key),
      }
      for (key, details) in self.static_details().items()
    }

  def to_dict(self):
    ret = asdict(self)
    ret.pop("_listeners")
    return ret

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
        if isinstance(loaded, cls):
          loaded.__post_init__()
          logger.info(f"Loaded settings: {cls.name()}")
          return loaded
        else:
          raise TypeError(f"Invalid Settings for {cls.name()}")
    except FileNotFoundError:
      created = cls()
      created.store()
      logger.info(f"Created new settings: {cls.name()}")
      return created

  def set(self, key: str, value: Any):
    self.__setattr__(key, value)

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


FLOW_CLIENT.register_request(
  "settings.list_components",
  lambda _: (
    logger.info(f"Registry: {registry}"),
    {
      "components": {
        key: {
          "name": component.name(),
          "details": component.details(),
        }
        for (key, component) in registry.items()
      }
    },
  )[1],
)


def component_set(message: Mapping):
  registry.get(message.get("component")).set(message.get("key"), message.get("value"))


FLOW_CLIENT.register_request(
  "settings.set",
  component_set,
)
