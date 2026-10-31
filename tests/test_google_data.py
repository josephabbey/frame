import asyncio
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from frame.data import OAuthToken
from frame.google import (
    GoogleAccountAPI,
    GoogleCalendarAPI,
    GoogleOAuthConfig,
    GoogleTasksAPI,
)


class FakeGoogleTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Mapping[str, str] | None]] = []

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        del params, json
        self.calls.append((method, url, headers))
        if url.endswith("/calendarList"):
            return {"items": [{"id": "primary", "summary": "Home", "primary": True}]}
        if url.endswith("/events"):
            return {
                "items": [
                    {
                        "id": "event-1",
                        "summary": "Planning",
                        "start": {"dateTime": "2026-10-31T09:00:00Z"},
                        "end": {"dateTime": "2026-10-31T10:00:00Z"},
                    }
                ]
            }
        if url.endswith("/lists"):
            return {"items": [{"id": "inbox", "title": "Inbox"}]}
        if url.endswith("/tasks"):
            return {"items": [{"id": "task-1", "title": "Send brief"}]}
        return {"sub": "google-user", "email": "person@example.com"}


def test_google_clients_map_google_payloads_to_shared_models():
    async def run() -> None:
        transport = FakeGoogleTransport()
        token = OAuthToken(access_token="access", token_type="Bearer")
        calendar = GoogleCalendarAPI(transport, token)
        tasks = GoogleTasksAPI(transport, token)

        calendars = await calendar.list_calendars()
        events = await calendar.list_events(
            events_start := datetime(2026, 10, 31),
            events_start.replace(hour=23),
        )
        task_lists = await tasks.list_task_lists()
        listed_tasks = await tasks.list_tasks(list_ids=("inbox",))

        assert calendars[0].is_primary is True
        assert events[0].title == "Planning"
        assert task_lists[0].name == "Inbox"
        assert listed_tasks[0].title == "Send brief"
        assert transport.calls[0][2] == {"Authorization": "Bearer access"}

    asyncio.run(run())


def test_google_account_builds_authorization_url_and_maps_profile():
    async def run() -> None:
        account = GoogleAccountAPI(
            FakeGoogleTransport(),
            OAuthToken(access_token="access", token_type="Bearer"),
            GoogleOAuthConfig("client", "secret", "https://frame.example/oauth"),
        )
        profile = await account.get_account(account.token)

        assert "client_id=client" in account.authorization_url(
            state="state", scopes=("openid", "email")
        )
        assert profile.email == "person@example.com"

    asyncio.run(run())
