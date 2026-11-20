"""Google Photos Library API and Picker import integration."""

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

from frame.data.photos import Photo, PhotoAlbum, PhotosAPI
from frame.flow import FLOW_CLIENT
from frame.utils import timestamp

from .account import ALL_SCOPES
from .client import GOOGLE_CLIENT

BASE_URL = "https://photoslibrary.googleapis.com/v1"
SCOPES = {
  "https://www.googleapis.com/auth/photoslibrary.appendonly",
  "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata",
}
ALL_SCOPES.update(SCOPES)
_WRITE_LOCK = asyncio.Lock()


class GooglePhotosAPI(PhotosAPI):
  """Read app-created albums and import Picker selections into one album."""

  def __init__(self) -> None:
    self._write_lock = _WRITE_LOCK

  async def create_album(self, name: str) -> str:
    payload = await GOOGLE_CLIENT.request_json(
      "POST",
      f"{BASE_URL}/albums",
      json={"album": {"title": name}},
    )
    album_id = str(payload["id"])
    return album_id

  async def import_picked_items(
    self,
    items: Sequence[Mapping[str, Any]],
    *,
    album_id: str | None,
    album_title: str,
  ) -> tuple[str | None, int]:
    """Copy picked photos into the persistent app-created album.

    The Library API cannot attach Picker-owned media IDs to an album. It only
    accepts app-created media, so each selected photo is fetched in memory,
    uploaded, and created directly in the app album.
    """
    picked_photos = tuple(
      item
      for item in items
      if item.get("type") == "PHOTO"
      or str((item.get("mediaFile") or {}).get("mimeType", "")).startswith("image/")
    )
    if not picked_photos:
      return album_id, 0

    async with self._write_lock:
      if album_id is None:
        album_id = await self.create_album(album_title)

      upload_tokens: list[tuple[str, str]] = []
      auth_headers = GOOGLE_CLIENT.authorization_headers()
      for item in picked_photos:
        media_file = item.get("mediaFile") or {}
        mime_type = str(media_file.get("mimeType", "image/jpeg"))
        base_url = media_file.get("baseUrl")
        if not base_url:
          raise RuntimeError(f"Picked photo {item.get('id')} has no media URL")

        data = await GOOGLE_CLIENT.request("GET", f"{base_url}=d", headers=auth_headers)
        upload_token = await GOOGLE_CLIENT.request(
          "POST",
          f"{BASE_URL}/uploads",
          headers={
            **auth_headers,
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-Content-Type": mime_type,
            "X-Goog-Upload-Protocol": "raw",
          },
          content=data,
        )
        filename = str(media_file.get("filename") or f"{item.get('id', 'photo')}.jpg")
        upload_tokens.append((upload_token.decode("utf-8").strip(), filename))

      created_count = 0
      for start in range(0, len(upload_tokens), 50):
        batch = upload_tokens[start : start + 50]
        result = await GOOGLE_CLIENT.request_json(
          "POST",
          f"{BASE_URL}/mediaItems:batchCreate",
          json={
            "albumId": album_id,
            "newMediaItems": [
              {"simpleMediaItem": {"uploadToken": token, "fileName": filename}}
              for token, filename in batch
            ],
          },
        )
        outcomes = result.get("newMediaItemResults", [])
        failures = [
          outcome
          for outcome in outcomes
          if outcome.get("status", {}).get("code", 0) != 0
          or not outcome.get("mediaItem")
        ]
        created_count += len(outcomes) - len(failures)
        if failures:
          messages = [
            str(outcome.get("status", {}).get("message", "Unknown error"))
            for outcome in failures
          ]
          raise RuntimeError(
            f"Google Photos created {created_count} of {len(picked_photos)} "
            f"picked photos: {'; '.join(messages)}"
          )
      return album_id, created_count

  async def list_albums(self) -> Sequence[PhotoAlbum]:
    albums: list[PhotoAlbum] = []
    page_token: str | None = None
    while True:
      params = {"pageSize": "50"}
      if page_token:
        params["pageToken"] = page_token
      payload = await GOOGLE_CLIENT.request_json(
        "GET", f"{BASE_URL}/albums", params=params
      )
      albums.extend(
        PhotoAlbum(
          id=str(item["id"]),
          title=str(item.get("title", "")),
          cover_photo_id=item.get("coverPhotoMediaItemId"),
        )
        for item in payload.get("albums", [])
      )
      page_token = payload.get("nextPageToken")
      if not page_token:
        return albums

  async def list_photos(
    self, *, album_id: str | None = None, limit: int | None = None
  ) -> Sequence[Photo]:
    if limit is not None and limit <= 0:
      return ()

    photos: list[Photo] = []
    page_token: str | None = None
    while True:
      page_size = min(100, limit - len(photos)) if limit is not None else 100
      body: dict[str, Any] = {"pageSize": page_size}
      if album_id:
        body["albumId"] = album_id
      if page_token:
        body["pageToken"] = page_token
      payload = await GOOGLE_CLIENT.request_json(
        "POST", f"{BASE_URL}/mediaItems:search", json=body
      )
      photos.extend(
        self._photo_from_payload(item, album_id)
        for item in payload.get("mediaItems", [])
      )
      if limit is not None and len(photos) >= limit:
        return tuple(photos[:limit])
      page_token = payload.get("nextPageToken")
      if not page_token:
        return photos

  async def get_album(self, album_id: str) -> PhotoAlbum:
    payload = await GOOGLE_CLIENT.request_json("GET", f"{BASE_URL}/albums/{album_id}")
    return PhotoAlbum(
      id=str(payload["id"]),
      title=str(payload.get("title", "")),
      cover_photo_id=payload.get("coverPhotoMediaItemId"),
    )

  async def get_photo(self, photo_id: str) -> Photo:
    payload = await GOOGLE_CLIENT.request_json(
      "GET", f"{BASE_URL}/mediaItems/{photo_id}"
    )
    return self._photo_from_payload(payload, None)

  @staticmethod
  def _photo_from_payload(payload: Mapping[str, Any], album_id: str | None) -> Photo:
    metadata = payload.get("mediaMetadata", {})
    base_url = str(payload["baseUrl"])
    return Photo(
      id=str(payload["id"]),
      source_url=f"{base_url}=w2048-h2048",
      thumbnail_url=f"{base_url}=w400-h400-c",
      captured_at=timestamp(metadata.get("creationTime")),
      width=int(metadata["width"]) if metadata.get("width") else None,
      height=int(metadata["height"]) if metadata.get("height") else None,
      caption=payload.get("description"),
      album_ids=(album_id,) if album_id else (),
    )


GOOGLE_PHOTOS_API = GooglePhotosAPI()


async def _albums_get(_):
  return {
    "albums": [
      {
        "id": album.id,
        "title": album.title,
        "cover_photo_id": album.cover_photo_id,
        "cover_photo_url": None
        if album.cover_photo_id is None
        else (
          (
            cover_photo := await GOOGLE_PHOTOS_API.get_photo(album.cover_photo_id)
          ).thumbnail_url
          or cover_photo.source_url
        ),
      }
      for album in await GOOGLE_PHOTOS_API.list_albums()
    ]
  }


FLOW_CLIENT.register_request(
  "data.photos.list_albums",
  _albums_get,
)
