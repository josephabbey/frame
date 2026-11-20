from dataclasses import dataclass, field
from typing import Any

from frame.data import OAuthToken
from frame.store import Store


@dataclass(slots=True, kw_only=True)
class GoogleStore(Store):
  """Google OAuth state and persistent Photos Picker workflow state."""

  token: OAuthToken | None = None
  photos_picker_pending_sessions: dict[str, Any] = field(default_factory=dict)


GOOGLE_STORE = GoogleStore.load()
