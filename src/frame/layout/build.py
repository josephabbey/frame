from collections.abc import Callable, Sequence
from enum import Enum
from random import choice, choices

from material_color_utilities import DynamicScheme, theme_from_color

from frame.data import Photo
from frame.layout.photos import full_bleed, gallery_triptych
from frame.local.photos import LOCAL_PHOTOS_API
from frame.ui import Element

default_scheme = theme_from_color(source="#FFC0CB").schemes.light

TODO_PHOTOS_API = LOCAL_PHOTOS_API


async def get_random_photos_from_random_album(n: int):
  albums = await TODO_PHOTOS_API.list_albums()
  album = choice(albums)

  photos = await TODO_PHOTOS_API.list_photos(album_id=album.id)
  return choices(photos, k=n)


class LAYOUTS(Enum):
  def __new__(cls, *args, **kwargs):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj

  def __init__(
    self, func: Callable[[Sequence[Photo], DynamicScheme], Element], num_photos: int = 0
  ):
    self.func = func
    self.num_photos = num_photos

  FULL_BLEED = (full_bleed, 1)
  GALLERY_TRIPTYCH = (gallery_triptych, 3)


async def build_layout() -> Element:
  considered_layouts = [LAYOUTS.FULL_BLEED, LAYOUTS.GALLERY_TRIPTYCH]
  layout = choice(considered_layouts)
  return layout.func(
    await get_random_photos_from_random_album(layout.num_photos), default_scheme
  )
