"""Weather domain models and the contract implemented by weather providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class WeatherCondition(StrEnum):
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    FOG = "fog"
    RAIN = "rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"
    WIND = "wind"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True, slots=True)
class CurrentWeather:
    observed_at: datetime
    temperature_c: float
    condition: WeatherCondition
    feels_like_c: float | None = None
    humidity_percent: int | None = None
    wind_speed_kph: float | None = None
    precipitation_probability: int | None = None


@dataclass(frozen=True, slots=True)
class DailyForecast:
    date: date
    condition: WeatherCondition
    high_c: float
    low_c: float
    precipitation_probability: int | None = None


@dataclass(frozen=True, slots=True)
class Weather:
    location: Location
    current: CurrentWeather
    forecast: tuple[DailyForecast, ...] = ()


class WeatherAPI(ABC):
    """The provider-facing operation required by weather displays."""

    @abstractmethod
    async def get_weather(
        self, location: Location, *, days: int = 5
    ) -> Weather: ...
