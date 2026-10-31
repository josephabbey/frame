"""Google Photos Library implementation of :class:`frame.data.PhotosAPI`."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from frame.data.photos import Photo, PhotoAlbum, PhotosAPI

from .client import GoogleClient

_BASE_URL = "https://photoslibrary.googleapis.com/v1"


def _timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class GooglePhotosAPI(GoogleClient, PhotosAPI):
    """Adapter for media the authenticated user has granted the app access to."""

    async def list_albums(self) -> Sequence[PhotoAlbum]:
        payload = await self.request("GET", f"{_BASE_URL}/albums")
        return tuple(
            PhotoAlbum(
                id=str(item["id"]),
                title=str(item.get("title", "")),
                cover_photo_id=item.get("coverPhotoMediaItemId"),
            )
            for item in payload.get("albums", [])
        )

    async def list_photos(
        self, *, album_id: str | None = None, limit: int | None = None
    ) -> Sequence[Photo]:
        body: dict[str, Any] = {}
        if album_id:
            body["albumId"] = album_id
        if limit:
            body["pageSize"] = limit
        payload = await self.request(
            "POST", f"{_BASE_URL}/mediaItems:search", json=body
        )
        return tuple(
            self._photo_from_payload(item, album_id)
            for item in payload.get("mediaItems", [])
        )

    @staticmethod
    def _photo_from_payload(payload: Mapping[str, Any], album_id: str | None) -> Photo:
        metadata = payload.get("mediaMetadata", {})
        return Photo(
            id=str(payload["id"]),
            source_url=str(payload["baseUrl"]),
            thumbnail_url=str(payload["baseUrl"]) + "=w400-h400-c",
            captured_at=_timestamp(metadata.get("creationTime")),
            width=int(metadata["width"]) if metadata.get("width") else None,
            height=int(metadata["height"]) if metadata.get("height") else None,
            caption=payload.get("description"),
            album_ids=(album_id,) if album_id else (),
        )
