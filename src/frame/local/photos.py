"""Google Photos Library implementation of :class:`frame.data.PhotosAPI`."""

import os
from collections.abc import Sequence
from itertools import islice
from pathlib import Path
from typing import cast

from frame.data.photos import Photo, PhotoAlbum, PhotosAPI

PHOTOS_PATH = (
  (Path(cast(str, os.environ.get("FRAME_LOCAL_PHOTOS_PATH"))))
  if ("FRAME_LOCAL_PHOTOS_PATH" in os.environ)
  else Path.home() / "Pictures"
)
assert PHOTOS_PATH.is_dir()


class LocalPhotosAPI(PhotosAPI):
  """Adapter for media the authenticated user has granted the app access to."""

  async def list_albums(self) -> Sequence[PhotoAlbum]:
    return [
      PhotoAlbum(
        id=item.name,
        title=item.name,
        cover_photo_id=next(item.iterdir()).name,
      )
      for item in PHOTOS_PATH.iterdir()
      if item.is_dir()
    ]

  async def get_album(self, album_id: str) -> PhotoAlbum:
    item = PHOTOS_PATH / album_id
    assert item.is_dir()
    return PhotoAlbum(
      id=item.name,
      title=item.name,
      cover_photo_id=next(item.iterdir()).name,
    )

  async def get_photo(self, photo_id: str) -> Photo:
    album_id, _, file_name = photo_id.partition("/")
    path = PHOTOS_PATH / album_id / file_name
    return Photo(
      id=photo_id,
      source_url=path.resolve().as_uri(),
      album_ids=(album_id,),
    )

  async def list_photos(
    self, *, album_id: str | None = None, limit: int | None = None
  ) -> Sequence[Photo]:
    if album_id:
      return [
        Photo(
          id=f"{album_id}/{item.name}",
          source_url=item.resolve().as_uri(),
          album_ids=(album_id,),
        )
        for item in islice((PHOTOS_PATH / album_id).iterdir(), limit)
        if item.is_file()
      ]
    return [
      Photo(
        id=f"{album_dir.name}/{file_name}",
        source_url=(album_dir / file_name).as_uri(),
        album_ids=(album_dir.name,),
      )
      for album_dir, _, file_names in islice(PHOTOS_PATH.walk(), limit)
      if album_dir.parent.samefile(PHOTOS_PATH)
      for file_name in file_names
    ]


LOCAL_PHOTOS_API = LocalPhotosAPI()
