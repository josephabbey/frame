from dataclasses import dataclass, field
from typing import Any

from frame.data import OAuthToken
from frame.store import Store


@dataclass(slots=True, kw_only=True)
class GoogleStore(Store):
  """Google OAuth state and persistent Photos Picker workflow state."""

  token: OAuthToken | None = None
  photos_picker_pending_sessions: dict[str, Any] = field(default_factory=dict)

  def __setstate__(self, state: Any) -> None:
    """Load older Google stores while dropping their cached album fields."""
    if isinstance(state, tuple) and len(state) == 2:
      values = {**(state[0] or {}), **(state[1] or {})}
    elif isinstance(state, dict):
      values = state
    else:
      values = {}
    object.__setattr__(self, "_listeners", values.get("_listeners", []))
    object.__setattr__(self, "token", values.get("token"))
    object.__setattr__(
      self,
      "photos_picker_pending_sessions",
      values.get("photos_picker_pending_sessions", {}),
    )


GOOGLE_STORE = GoogleStore.load()
