"""Google Maps Weather API implementation of :class:`frame.data.WeatherAPI`."""

from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

from frame.data.weather import (
    CurrentWeather,
    DailyForecast,
    Location,
    Weather,
    WeatherAPI,
    WeatherCondition,
)

from .transport import GoogleTransport

_BASE_URL = "https://weather.googleapis.com/v1"


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _condition(value: Mapping[str, Any] | None) -> WeatherCondition:
    value = value or {}
    raw = str(value.get("type", value.get("description", "unknown"))).lower()
    if "thunder" in raw:
        return WeatherCondition.THUNDERSTORM
    if "snow" in raw or "ice" in raw:
        return WeatherCondition.SNOW
    if "rain" in raw or "drizzle" in raw or "shower" in raw:
        return WeatherCondition.RAIN
    if "fog" in raw or "haze" in raw:
        return WeatherCondition.FOG
    if "wind" in raw:
        return WeatherCondition.WIND
    if "partly" in raw or "mostly" in raw:
        return WeatherCondition.PARTLY_CLOUDY
    if "cloud" in raw or "overcast" in raw:
        return WeatherCondition.CLOUDY
    if "clear" in raw or "sun" in raw:
        return WeatherCondition.CLEAR
    return WeatherCondition.UNKNOWN


def _degrees(value: Mapping[str, Any] | None) -> float | None:
    return (
        float(value["degrees"]) if value and value.get("degrees") is not None else None
    )


class GoogleWeatherAPI(WeatherAPI):
    """Maps Weather client authenticated with a Google Maps API key."""

    def __init__(self, transport: GoogleTransport, api_key: str) -> None:
        self.transport = transport
        self.api_key = api_key

    async def get_weather(self, location: Location, *, days: int = 5) -> Weather:
        params = {
            "location.latitude": str(location.latitude),
            "location.longitude": str(location.longitude),
        }
        headers = {"x-goog-api-key": self.api_key}
        current_payload = await self.transport.request(
            "GET",
            f"{_BASE_URL}/currentConditions:lookup",
            headers=headers,
            params=params,
        )
        forecast_payload = await self.transport.request(
            "GET",
            f"{_BASE_URL}/forecast/days:lookup",
            headers=headers,
            params={**params, "days": str(days)},
        )
        return Weather(
            location=location,
            current=self._current_from_payload(current_payload),
            forecast=tuple(
                self._forecast_from_payload(item)
                for item in forecast_payload.get("forecastDays", [])
            ),
        )

    @staticmethod
    def _current_from_payload(payload: Mapping[str, Any]) -> CurrentWeather:
        return CurrentWeather(
            observed_at=_timestamp(
                str(payload.get("currentTime", datetime.now(UTC).isoformat()))
            ),
            temperature_c=float(payload["temperature"]["degrees"]),
            condition=_condition(payload.get("weatherCondition")),
            feels_like_c=_degrees(payload.get("feelsLikeTemperature")),
            humidity_percent=(
                int(payload["relativeHumidity"])
                if payload.get("relativeHumidity")
                else None
            ),
            wind_speed_kph=_degrees(payload.get("wind", {}).get("speed")),
            precipitation_probability=payload.get("precipitationProbability", {}).get(
                "percent"
            ),
        )

    @staticmethod
    def _forecast_from_payload(payload: Mapping[str, Any]) -> DailyForecast:
        interval = payload.get("interval", {})
        return DailyForecast(
            date=date.fromisoformat(str(interval.get("startTime", "1970-01-01"))[:10]),
            condition=_condition(
                payload.get("daytimeForecast", {}).get("weatherCondition")
            ),
            high_c=float(payload["maxTemperature"]["degrees"]),
            low_c=float(payload["minTemperature"]["degrees"]),
            precipitation_probability=payload.get("daytimeForecast", {})
            .get("precipitation", {})
            .get("probability", {})
            .get("percent"),
        )
