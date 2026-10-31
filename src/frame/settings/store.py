"""Filesystem persistence and change dispatch for settings."""

import json
import logging
import os
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "frame"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "settings.json"


class SettingsStore:
    """Manages reading, writing, and notifying observers of settings."""

    def __init__(
        self,
        path: Path | str | None = None,
        settings_type: Any = None,
    ) -> None:
        if path is None:
            env_path = os.environ.get("FRAME_SETTINGS_PATH")
            self.path = Path(env_path) if env_path else DEFAULT_CONFIG_FILE
        else:
            self.path = Path(path)

        if settings_type is None:
            try:
                from frame.flow.settings import FlowSettings

                settings_type = FlowSettings
            except ImportError, RuntimeError:
                settings_type = None
        self.settings_type = settings_type

        self._listeners: list[Callable[[Any], None]] = []
        self._current_settings: Any = None

    @property
    def current(self) -> Any:
        """Return the current in-memory settings, loading them if needed."""
        if self._current_settings is None:
            self._current_settings = self.load()
        return self._current_settings

    def _instantiate(self) -> Any:
        settings_type = self.settings_type
        if settings_type is None:
            return {}
        if isinstance(settings_type, type):
            return settings_type()
        if callable(settings_type):
            return settings_type()
        return settings_type

    def _to_dict(self, settings: Any) -> dict[str, Any]:
        if hasattr(settings, "to_dict"):
            return settings.to_dict(include_secrets=True)
        if isinstance(settings, Mapping):
            return dict(settings)
        return {"value": settings}

    def _from_dict(self, data: Mapping[str, Any]) -> Any:
        settings_type = self.settings_type
        if settings_type is None:
            return dict(data)
        if hasattr(settings_type, "from_dict"):
            return settings_type.from_dict(data)
        if isinstance(settings_type, type):
            try:
                return settings_type(**data)
            except TypeError, ValueError:
                return settings_type()
        if callable(settings_type):
            return settings_type(data)
        return data

    def load(self) -> Any:
        """Load settings from disk or create defaults if the file does not exist."""
        if not self.path.exists():
            settings = self._instantiate()
            self.save(settings)
            self._current_settings = settings
            return settings

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise TypeError("Settings file must contain a JSON object")
            settings = self._from_dict(data)
        except OSError, ValueError, TypeError, json.JSONDecodeError:
            settings = self._instantiate()

        self._current_settings = settings
        return settings

    def save(self, settings: Any) -> None:
        """Atomically persist settings to disk with restricted permissions."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = self._to_dict(settings)

        fd, temp_path = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".settings-tmp-",
        )
        try:
            with open(fd, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, self.path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        self._current_settings = settings
        self._notify(settings)

    def update(self, **kwargs: Any) -> Any:
        """Update specific settings attributes or keys and save the result."""
        current = self.current
        if isinstance(current, Mapping) and not hasattr(current, "to_dict"):
            current.update(kwargs)
        else:
            for key, value in kwargs.items():
                if hasattr(current, key):
                    setattr(current, key, value)
                elif isinstance(current, Mapping):
                    current[key] = value
                else:
                    setattr(current, key, value)
        self.save(current)
        return current

    def add_listener(self, callback: Callable[[Any], None]) -> Callable[[], None]:
        """Register a callback for settings updates. Returns an unregister function."""

        def unsubscribe() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        self._listeners.append(callback)
        return unsubscribe

    def _notify(self, settings: Any) -> None:
        for listener in list(self._listeners):
            try:
                listener(settings)
            except Exception:
                logger.debug("Settings store listener failed", exc_info=True)
