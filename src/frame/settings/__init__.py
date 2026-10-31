"""Settings storage and access for Frame."""

from typing import TYPE_CHECKING

from .store import SettingsStore

if TYPE_CHECKING:
    from frame.flow.settings import FlowSettings as Settings

__all__ = ["Settings", "SettingsStore"]


def __getattr__(name: str) -> object:
    if name in {"Settings", "FlowSettings"}:
        from frame.flow.settings import FlowSettings

        return FlowSettings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
