from dataclasses import dataclass
from datetime import date, datetime

from frame.data import (
  CurrentWeather,
  DailyForecast,
  Location,
  Weather,
  WeatherAPI,
  WeatherCondition,
)
from frame.web.client import Client

BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(slots=True, kw_only=True)
class OpenMeteoWeatherAPI(Client, WeatherAPI):
  def _map_condition(self, wmo_code: int) -> WeatherCondition:
    """Maps WMO Weather interpretation codes to WeatherCondition enum."""
    if wmo_code == 0:
      return WeatherCondition.CLEAR
    elif wmo_code in (1, 2):
      return WeatherCondition.PARTLY_CLOUDY
    elif wmo_code == 3:
      return WeatherCondition.CLOUDY
    elif wmo_code in (45, 48):
      return WeatherCondition.FOG
    elif (51 <= wmo_code <= 67) or (80 <= wmo_code <= 82):
      return WeatherCondition.RAIN
    elif (71 <= wmo_code <= 77) or (85 <= wmo_code <= 86):
      return WeatherCondition.SNOW
    elif 95 <= wmo_code <= 99:
      return WeatherCondition.THUNDERSTORM
    return WeatherCondition.UNKNOWN

  async def get_weather(self, location: Location, *, days: int = 5) -> Weather:
    params = {
      "latitude": str(location.latitude),
      "longitude": str(location.longitude),
      "current": (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,wind_speed_10m"
      ),
      "daily": (
        "weather_code,temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max"
      ),
      "timezone": location.timezone,
      "forecast_days": str(days),
    }

    # Uses the inherited request method from Client
    data = await self.request_json("GET", BASE_URL, params=params)

    # Parse current weather
    current_data = data.get("current", {})
    observed_at_str = current_data.get("time")
    observed_at = (
      datetime.fromisoformat(observed_at_str) if observed_at_str else datetime.now()
    )
    current_code = current_data.get("weather_code", 0)

    # Parse daily forecast
    daily_data = data.get("daily", {})
    times = daily_data.get("time", [])
    codes = daily_data.get("weather_code", [])
    max_temps = daily_data.get("temperature_2m_max", [])
    min_temps = daily_data.get("temperature_2m_min", [])
    precip_probs = daily_data.get("precipitation_probability_max", [])

    forecast_list = []
    for i in range(len(times)):
      forecast_date = date.fromisoformat(times[i])
      condition = self._map_condition(codes[i] if i < len(codes) else 0)
      high_c = (
        float(max_temps[i]) if i < len(max_temps) and max_temps[i] is not None else 0.0
      )
      low_c = (
        float(min_temps[i]) if i < len(min_temps) and min_temps[i] is not None else 0.0
      )
      precip_prob = (
        int(precip_probs[i])
        if i < len(precip_probs) and precip_probs[i] is not None
        else None
      )
      forecast_list.append(
        DailyForecast(
          date=forecast_date,
          condition=condition,
          high_c=high_c,
          low_c=low_c,
          precipitation_probability=precip_prob,
        )
      )

    current_precip_prob = (
      forecast_list[0].precipitation_probability if forecast_list else None
    )

    current_weather = CurrentWeather(
      observed_at=observed_at,
      temperature_c=float(current_data.get("temperature_2m", 0.0)),
      condition=self._map_condition(current_code),
      feels_like_c=(
        float(current_data.get("apparent_temperature"))
        if current_data.get("apparent_temperature") is not None
        else None
      ),
      humidity_percent=(
        int(current_data.get("relative_humidity_2m"))
        if current_data.get("relative_humidity_2m") is not None
        else None
      ),
      wind_speed_kph=(
        float(current_data.get("wind_speed_10m"))
        if current_data.get("wind_speed_10m") is not None
        else None
      ),
      precipitation_probability=current_precip_prob,
    )

    return Weather(
      location=location,
      current=current_weather,
      forecast=tuple(forecast_list),
    )


OPENMETEO_WEATHER_API = OpenMeteoWeatherAPI()
