from datetime import datetime


def timestamp(value: str | None) -> datetime | None:
  return datetime.fromisoformat(value) if value else None
