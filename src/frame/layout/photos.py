"""Still photo display layouts for Frame."""

from collections.abc import Sequence

from material_color_utilities import DynamicScheme, theme_from_image

from frame.data import Photo
from frame.ui import (
  SHAPE_ARCH_LARGE,
  SHAPE_EXTRA_LARGE,
  SHAPE_MEDIUM,
  SPACE_100,
  SPACE_150,
  SPACE_175,
  SPACE_200,
  SPACE_300,
  SPACE_400,
  Card,
  Column,
  Element,
  Image,
  ImageFit,
  Row,
  Text,
  TextAlign,
  TypographyRole,
)
from frame.utils.image import image_from_url


async def full_bleed(
  photos: Sequence[Photo],
  scheme: DynamicScheme,
  *,
  title: str = "A day worth keeping",
  subtitle: str = "A moment to remember",
) -> Element:
  """A borderless photograph with a calm caption band below it."""
  # override scheme
  scheme = theme_from_image(
    img=await image_from_url(photos[0].source_url)
  ).schemes.light
  return Column(
    scheme=scheme,
    padding=SPACE_300,
    gap=SPACE_175,
    main_sizes=[None, 86],
    children=[
      Image(
        scheme=scheme,
        source=photos[0].source_url,
        fit=ImageFit.COVER,
        focal_point=(0.5, 0.44),
        shape=SHAPE_EXTRA_LARGE,
      ),
      Card(
        scheme=scheme,
        shape=SHAPE_MEDIUM,
        content_padding=SPACE_200,
        children=[
          Text(
            scheme=scheme,
            text=title,
            role=TypographyRole.TITLE_LARGE,
            emphasized=True,
          ),
          Text(
            scheme=scheme,
            text=subtitle,
            role=TypographyRole.LABEL_LARGE,
          ),
        ],
      ),
    ],
  )


async def gallery_triptych(
  photos: Sequence[Photo],
  scheme: DynamicScheme,
  *,
  caption: str = "Little moments, together",
) -> Element:
  """A large hero crop balanced by two smaller portrait crops."""
  return Column(
    scheme=scheme,
    padding=SPACE_300,
    gap=SPACE_200,
    main_sizes=[None, 72],
    children=[
      Row(
        scheme=scheme,
        gap=SPACE_175,
        main_sizes=[None, None, None],
        weights=[2, 1, 1],
        children=[
          Image(
            scheme=scheme,
            source=photos[0].source_url,
            fit=ImageFit.COVER,
            focal_point=(0.48, 0.42),
            shape=SHAPE_MEDIUM,
          ),
          Image(
            scheme=scheme,
            source=photos[1 % len(photos)].source_url,
            fit=ImageFit.COVER,
            focal_point=(0.5, 0.5),
            shape=SHAPE_MEDIUM,
          ),
          Image(
            scheme=scheme,
            source=photos[2 % len(photos)].source_url,
            fit=ImageFit.COVER,
            focal_point=(0.5, 0.5),
            shape=SHAPE_MEDIUM,
          ),
        ],
      ),
      Text(
        scheme=scheme,
        text=caption,
        role=TypographyRole.HEADLINE_SMALL,
        emphasized=True,
        align=TextAlign.CENTER,
      ),
    ],
  )


async def editorial(
  photos: Sequence[Photo],
  scheme: DynamicScheme,
  *,
  time_text: str = "12:34",
  headline: str = "The afternoon light found its way through the trees.",
  caption: str = "A MOMENT IN TIME",
) -> Element:
  """A generous image with an expressive date and caption column."""
  return Row(
    scheme=scheme,
    padding=SPACE_400,
    gap=SPACE_300,
    weights=[3, 2],
    children=[
      Image(
        scheme=scheme,
        source=photos[0].source_url,
        fit=ImageFit.COVER,
        focal_point=(0.52, 0.45),
        shape=SHAPE_ARCH_LARGE,
      ),
      Column(
        scheme=scheme,
        padding=SPACE_100,
        gap=SPACE_150,
        main_sizes=[82, None, 56],
        children=[
          Text(
            scheme=scheme,
            text=time_text,
            role=TypographyRole.DISPLAY_LARGE,
            emphasized=True,
            tabular_numbers=True,
          ),
          Text(
            scheme=scheme,
            text=headline,
            role=TypographyRole.HEADLINE_SMALL,
            emphasized=True,
          ),
          Text(
            scheme=scheme,
            text=caption,
            role=TypographyRole.LABEL_MEDIUM,
          ),
        ],
      ),
    ],
  )
