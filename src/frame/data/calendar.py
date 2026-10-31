"""Calendar domain models and the contract implemented by calendar providers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Calendar:
    """A calendar a provider makes available to an account."""

    id: str
    name: str
    color: str | None = None
    is_primary: bool = False


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    """A time-bound event, including all-day events represented by midnight bounds."""

    id: str
    calendar_id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    all_day: bool = False
    location: str | None = None
    description: str | None = None
    url: str | None = None
    attendees: tuple[str, ...] = field(default_factory=tuple)


class CalendarAPI(ABC):
    """The provider-facing operations required by calendar displays."""

    @abstractmethod
    async def list_calendars(self) -> Sequence[Calendar]: ...

    @abstractmethod
    async def list_events(
        self,
        starts_at: datetime,
        ends_at: datetime,
        *,
        calendar_ids: Sequence[str] | None = None,
    ) -> Sequence[CalendarEvent]: ...
