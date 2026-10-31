"""Flow-specific configuration for Frame."""

import json
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlencode, urlsplit, urlunsplit

from frame.data.account import OAuthToken
from frame.settings.store import SettingsStore


def _generate_frame_key() -> str:
    """Generate a high-entropy per-frame secret key."""
    return secrets.token_urlsafe(32)


@dataclass(slots=True)
class FlowSettings:
    """Frame Flow configuration and device state."""

    frame_key: str = field(default_factory=_generate_frame_key)
    frame_name: str = "Frame"
    flow_url: str = "https://frame-flow.vercel.app"
    google_token: OAuthToken | None = None
    display_refresh_seconds: int = 300
    theme_color: str = "#6750A4"
    custom: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.frame_key) < 24:
            raise ValueError("frame_key must be at least 24 characters")
        if len(self.frame_key) > 256:
            raise ValueError("frame_key must be at most 256 characters")

    @property
    def pairing_url(self) -> str:
        """Construct the URL encoded into the pairing QR code."""
        parsed = urlsplit(self.flow_url)
        path = parsed.path or "/"
        if not path.endswith("/"):
            path += "/"
        params = {"key": self.frame_key, "name": self.frame_name}
        new_query = urlencode(params)
        combined_query = f"{parsed.query}&{new_query}" if parsed.query else new_query
        return urlunsplit(
            (parsed.scheme, parsed.netloc, path, combined_query, parsed.fragment)
        )

    @property
    def websocket_url(self) -> str:
        """Construct the relay WebSocket URL for this frame."""
        parsed = urlsplit(self.flow_url)
        scheme = "ws" if parsed.scheme == "http" else "wss"
        netloc = parsed.netloc or parsed.path
        path = "/api/socket"
        query = urlencode({"role": "device", "key": self.frame_key})
        return urlunsplit((scheme, netloc, path, query, ""))

    def to_dict(self, *, include_secrets: bool = True) -> dict[str, Any]:
        """Convert settings to a serializable dictionary."""
        data = {
            "frame_name": self.frame_name,
            "display_refresh_seconds": self.display_refresh_seconds,
            "theme_color": self.theme_color,
            "custom": dict(self.custom),
        }
        data["flow_url"] = self.flow_url
        if include_secrets:
            data["frame_key"] = self.frame_key
            if self.google_token is not None:
                data["google_token"] = {
                    "access_token": self.google_token.access_token,
                    "token_type": self.google_token.token_type,
                    "expires_at": (
                        self.google_token.expires_at.isoformat()
                        if self.google_token.expires_at is not None
                        else None
                    ),
                    "refresh_token": self.google_token.refresh_token,
                    "scopes": list(self.google_token.scopes),
                }
            else:
                data["google_token"] = None
        else:
            data["frame_key"] = (
                f"...{self.frame_key[-6:]}" if len(self.frame_key) > 6 else "..."
            )
            data["has_google_token"] = self.google_token is not None
            if self.google_token is not None:
                data["google_token_scopes"] = list(self.google_token.scopes)
                data["google_token_expired"] = self.google_token.is_expired
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FlowSettings:
        """Reconstruct FlowSettings from a mapping."""
        token_data = data.get("google_token")
        google_token: OAuthToken | None = None
        if isinstance(token_data, Mapping):
            expires_at = token_data.get("expires_at")
            if isinstance(expires_at, str):
                parsed_expires_at = datetime.fromisoformat(expires_at)
            elif isinstance(expires_at, (int, float)):
                parsed_expires_at = datetime.fromtimestamp(expires_at, tz=UTC)
            else:
                parsed_expires_at = None

            google_token = OAuthToken(
                access_token=str(token_data.get("access_token", "")),
                token_type=str(token_data.get("token_type", "Bearer")),
                expires_at=parsed_expires_at,
                refresh_token=(
                    str(token_data["refresh_token"])
                    if token_data.get("refresh_token") is not None
                    else None
                ),
                scopes=tuple(token_data.get("scopes", ())),
            )

        return cls(
            frame_name=str(data.get("frame_name", "Frame")),
            display_refresh_seconds=int(data.get("display_refresh_seconds", 300)),
            theme_color=str(data.get("theme_color", "#6750A4")),
            custom=dict(data.get("custom", {})),
            frame_key=str(data.get("frame_key") or _generate_frame_key()),
            flow_url=str(data.get("flow_url", "https://frame-flow.vercel.app")),
            google_token=google_token,
        )


class FlowSettingsStore(SettingsStore):
    """Settings store whose default settings are FlowSettings."""

    @property
    def current(self) -> FlowSettings:  # type: ignore[override]
        if self._current_settings is None:
            self._current_settings = self.load()
        return cast(FlowSettings, self._current_settings)

    def load(self) -> FlowSettings:  # type: ignore[override]
        if not self.path.exists():
            settings = FlowSettings()
            self.save(settings)
            self._current_settings = settings
            return settings

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise TypeError("Settings file must contain a JSON object")
            settings = FlowSettings.from_dict(data)
        except OSError, ValueError, TypeError, json.JSONDecodeError:
            settings = FlowSettings()

        self._current_settings = settings
        return settings
