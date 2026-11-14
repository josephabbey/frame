import secrets
from dataclasses import dataclass, field

from frame.store import Store


def _generate_frame_key() -> str:
  """Generate a high-entropy per-frame secret key."""
  return secrets.token_urlsafe(64)


@dataclass(slots=True)
class FlowStore(Store):
  """Frame Flow configuration and device state."""

  key: str = field(default_factory=_generate_frame_key)


FLOW_STORE = FlowStore.load()
