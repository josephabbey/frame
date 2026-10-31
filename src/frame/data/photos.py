"""Photo domain models and the contract implemented by photo providers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PhotoAlbum:
    id: str
    title: str
    cover_photo_id: str | None = None


@dataclass(frozen=True, slots=True)
class Photo:
    id: str
    source_url: str
    thumbnail_url: str | None = None
    captured_at: datetime | None = None
    width: int | None = None
    height: int | None = None
    caption: str | None = None
    album_ids: tuple[str, ...] = field(default_factory=tuple)


class PhotosAPI(ABC):
    """The provider-facing operations required by photo displays."""

    @abstractmethod
    async def list_albums(self) -> Sequence[PhotoAlbum]: ...

    @abstractmethod
    async def list_photos(
        self,
        *,
        album_id: str | None = None,
        limit: int | None = None,
    ) -> Sequence[Photo]: ...
