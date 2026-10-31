"""Google Calendar implementation of :class:`frame.data.CalendarAPI`."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from frame.data.calendar import Calendar, CalendarAPI, CalendarEvent

from .client import GoogleClient

_BASE_URL = "https://www.googleapis.com/calendar/v3"


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _event_time(value: Mapping[str, Any]) -> tuple[datetime, bool]:
    if date_time := value.get("dateTime"):
        return _timestamp(str(date_time)), False
    return datetime.fromisoformat(str(value["date"])).replace(tzinfo=UTC), True


class GoogleCalendarAPI(GoogleClient, CalendarAPI):
    async def list_calendars(self) -> Sequence[Calendar]:
        payload = await self.request("GET", f"{_BASE_URL}/users/me/calendarList")
        return tuple(
            Calendar(
                id=str(item["id"]),
                name=str(item.get("summary", "")),
                color=item.get("backgroundColor"),
                is_primary=bool(item.get("primary", False)),
            )
            for item in payload.get("items", [])
        )

    async def list_events(
        self,
        starts_at: datetime,
        ends_at: datetime,
        *,
        calendar_ids: Sequence[str] | None = None,
    ) -> Sequence[CalendarEvent]:
        ids = calendar_ids or ("primary",)
        events: list[CalendarEvent] = []
        for calendar_id in ids:
            payload = await self.request(
                "GET",
                f"{_BASE_URL}/calendars/{calendar_id}/events",
                params={
                    "timeMin": starts_at.isoformat(),
                    "timeMax": ends_at.isoformat(),
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
            )
            events.extend(
                self._event_from_payload(item, calendar_id)
                for item in payload.get("items", [])
                if item.get("status") != "cancelled"
            )
        return tuple(events)

    @staticmethod
    def _event_from_payload(payload: Mapping[str, Any], calendar_id: str) -> CalendarEvent:
        starts_at, all_day = _event_time(payload["start"])
        ends_at, _ = _event_time(payload["end"])
        return CalendarEvent(
            id=str(payload["id"]),
            calendar_id=calendar_id,
            title=str(payload.get("summary", "")),
            starts_at=starts_at,
            ends_at=ends_at,
            all_day=all_day,
            location=payload.get("location"),
            description=payload.get("description"),
            url=payload.get("htmlLink"),
            attendees=tuple(
                attendee["email"]
                for attendee in payload.get("attendees", [])
                if attendee.get("email")
            ),
        )
