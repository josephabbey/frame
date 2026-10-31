from datetime import UTC, datetime, timedelta
from inspect import isabstract

from frame.data import (
    AccountAPI,
    CalendarAPI,
    CalendarEvent,
    OAuthToken,
    Photo,
    PhotosAPI,
    Task,
    TaskPriority,
    TasksAPI,
    WeatherAPI,
    WeatherCondition,
)


def test_domain_models_preserve_provider_data():
    starts_at = datetime(2026, 10, 31, 9, tzinfo=UTC)
    event = CalendarEvent(
        id="event-1",
        calendar_id="primary",
        title="Planning",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        attendees=("person@example.com",),
    )
    task = Task(
        id="task-1",
        list_id="inbox",
        title="Send brief",
        priority=TaskPriority.HIGH,
    )
    photo = Photo(id="photo-1", source_url="https://example.com/photo.jpg")

    assert event.attendees == ("person@example.com",)
    assert task.priority is TaskPriority.HIGH
    assert photo.thumbnail_url is None
    assert WeatherCondition.PARTLY_CLOUDY == "partly_cloudy"


def test_oauth_token_expiry_uses_the_token_timezone():
    expired = OAuthToken(
        access_token="access",
        token_type="Bearer",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    valid = OAuthToken(
        access_token="access",
        token_type="Bearer",
        expires_at=datetime.now(UTC) + timedelta(seconds=1),
    )

    assert expired.is_expired is True
    assert valid.is_expired is False


def test_provider_contracts_require_an_implementation():
    assert all(isabstract(api) for api in (AccountAPI, CalendarAPI, PhotosAPI, TasksAPI, WeatherAPI))
