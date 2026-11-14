import dataclasses
from pickle import *
from typing import IO, Any


def apply_dataclass_defaults(obj: Any) -> Any:
  """Recursively checks for dataclasses and applies missing default values."""
  # Handle dataclass instances (excluding the class itself)
  if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
    cls = type(obj)
    for field in dataclasses.fields(cls):
      if not hasattr(obj, field.name):
        if field.default is not dataclasses.MISSING:
          setattr(obj, field.name, field.default)
        elif field.default_factory is not dataclasses.MISSING:
          setattr(obj, field.name, field.default_factory())

  # Recursively traverse common container types
  if isinstance(obj, dict):
    for k, v in obj.items():
      obj[k] = apply_dataclass_defaults(v)
  elif isinstance(obj, list):
    for i, item in enumerate(obj):
      obj[i] = apply_dataclass_defaults(item)
  elif isinstance(obj, tuple):
    # Tuples are immutable, so we rebuild them if any elements change
    processed = tuple(apply_dataclass_defaults(item) for item in obj)
    return processed
  elif isinstance(obj, set):
    # Sets are also immutable regarding their elements' attributes in place, but we can rebuild
    processed = {apply_dataclass_defaults(item) for item in obj}
    return processed

  return obj


def load_with_defaults(file: IO[bytes], *args: Any, **kwargs: Any) -> Any:
  """Wrapper for load() that applies dataclass default values."""
  obj = load(file, *args, **kwargs)
  return apply_dataclass_defaults(obj)


def loads_with_defaults(data: bytes, *args: Any, **kwargs: Any) -> Any:
  """Wrapper for loads() that applies dataclass default values."""
  obj = loads(data, *args, **kwargs)
  return apply_dataclass_defaults(obj)
