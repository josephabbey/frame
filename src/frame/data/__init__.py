"""Provider-neutral data contracts for content shown by a frame."""

from .account import Account, AccountAPI, OAuthToken
from .calendar import Calendar, CalendarAPI, CalendarEvent
from .photos import Photo, PhotoAlbum, PhotosAPI
from .tasks import Task, TaskList, TaskPriority, TasksAPI, TaskStatus
from .weather import (
    CurrentWeather,
    DailyForecast,
    Location,
    Weather,
    WeatherAPI,
    WeatherCondition,
)

__all__ = [
    "Account",
    "AccountAPI",
    "Calendar",
    "CalendarAPI",
    "CalendarEvent",
    "CurrentWeather",
    "DailyForecast",
    "Location",
    "OAuthToken",
    "Photo",
    "PhotoAlbum",
    "PhotosAPI",
    "Task",
    "TaskList",
    "TaskPriority",
    "TaskStatus",
    "TasksAPI",
    "Weather",
    "WeatherAPI",
    "WeatherCondition",
]
