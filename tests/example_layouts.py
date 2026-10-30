"""Example still layouts for an 800x480 Inky Impression photo frame.

Render the built-in photo samples with:
    uv run python tests/example_layouts.py

The examples include full_bleed, gallery_triptych, editorial, side_by_side,
memory_grid, and daily_digest. Select photos and layouts by name with:
    uv run python tests/example_layouts.py --photos IMG_0977~2.jpg IMG_1318.HEIC \
        --layouts full_bleed editorial

The source photo can be any Pillow-supported image. Output PNGs are written to
``tests/rendered_examples/`` by default.
"""

import argparse
from pathlib import Path

from material_color_utilities import Variant, theme_from_image
from PIL import Image as PILImage

from frame.ui import (
    PRIMARY_CONTAINER,
    SHAPE_ARCH_LARGE,
    SHAPE_EXTRA_LARGE,
    SHAPE_MEDIUM,
    SPACE_100,
    SPACE_150,
    SPACE_175,
    SPACE_200,
    SPACE_250,
    SPACE_300,
    SPACE_400,
    Card,
    Column,
    Image,
    ImageFit,
    Row,
    Text,
    TextAlign,
    TypographyRole,
    render,
)

WIDTH = 800
HEIGHT = 480


def scheme_for(photo: Path):
    """Build an expressive Material 3 scheme from the lead photo."""
    with PILImage.open(photo) as source:
        image = source.convert("RGB")
    return theme_from_image(image, variant=Variant.EXPRESSIVE).schemes.light


def full_bleed(photos: list[Path], scheme):
    """A borderless photograph with a calm caption band below it."""
    return Column(
        scheme=scheme,
        padding=SPACE_300,
        gap=SPACE_175,
        main_sizes=[None, 86],
        children=[
            Image(
                scheme=scheme,
                source=photos[0],
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
                        text="A day worth keeping",
                        role=TypographyRole.TITLE_LARGE,
                        emphasized=True,
                    ),
                    Text(
                        scheme=scheme,
                        text="A moment to remember",
                        role=TypographyRole.LABEL_LARGE,
                    ),
                ],
            ),
        ],
    )


def gallery_triptych(photos: list[Path], scheme):
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
                        source=photos[0],
                        fit=ImageFit.COVER,
                        focal_point=(0.48, 0.42),
                        shape=SHAPE_MEDIUM,
                    ),
                    Image(
                        scheme=scheme,
                        source=photos[1 % len(photos)],
                        fit=ImageFit.COVER,
                        focal_point=(0.5, 0.5),
                        shape=SHAPE_MEDIUM,
                    ),
                    Image(
                        scheme=scheme,
                        source=photos[2 % len(photos)],
                        fit=ImageFit.COVER,
                        focal_point=(0.5, 0.5),
                        shape=SHAPE_MEDIUM,
                    ),
                ],
            ),
            Text(
                scheme=scheme,
                text="Little moments, together",
                role=TypographyRole.HEADLINE_SMALL,
                emphasized=True,
                align=TextAlign.CENTER,
            ),
        ],
    )


def editorial(photos: list[Path], scheme):
    """A generous image with an expressive date and caption column."""
    return Row(
        scheme=scheme,
        padding=SPACE_400,
        gap=SPACE_300,
        weights=[3, 2],
        children=[
            Image(
                scheme=scheme,
                source=photos[0],
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
                        text="12:34",
                        role=TypographyRole.DISPLAY_LARGE,
                        emphasized=True,
                        tabular_numbers=True,
                    ),
                    Text(
                        scheme=scheme,
                        text="The afternoon light found its way through the trees.",
                        role=TypographyRole.HEADLINE_SMALL,
                        emphasized=True,
                    ),
                    Text(
                        scheme=scheme,
                        text="A MOMENT IN TIME",
                        role=TypographyRole.LABEL_MEDIUM,
                    ),
                ],
            ),
        ],
    )


def side_by_side(photos: list[Path], scheme):
    """A quiet split composition with a photo and a bold color panel."""
    return Row(
        scheme=scheme,
        padding=SPACE_300,
        gap=SPACE_300,
        weights=[3, 2],
        children=[
            Image(
                scheme=scheme,
                source=photos[0],
                fit=ImageFit.COVER,
                focal_point=(0.5, 0.45),
                shape=SHAPE_EXTRA_LARGE,
            ),
            Card(
                scheme=scheme,
                bgcolor=PRIMARY_CONTAINER,
                content_padding=SPACE_300,
                children=[
                    Text(
                        scheme=scheme,
                        text="FRIDAY, JUNE 14",
                        role=TypographyRole.LABEL_LARGE,
                    ),
                    Text(
                        scheme=scheme,
                        text="Somewhere beautiful",
                        role=TypographyRole.HEADLINE_MEDIUM,
                        emphasized=True,
                    ),
                    Text(
                        scheme=scheme,
                        text="A little space to slow down and take it all in.",
                        role=TypographyRole.BODY_LARGE,
                    ),
                ],
            ),
        ],
    )


def memory_grid(photos: list[Path], scheme):
    """A four-photo grid with a simple title bar."""
    return Column(
        scheme=scheme,
        padding=SPACE_300,
        gap=SPACE_200,
        main_sizes=[64, None],
        children=[
            Row(
                scheme=scheme,
                children=[
                    Text(
                        scheme=scheme,
                        text="Collected moments",
                        role=TypographyRole.HEADLINE_SMALL,
                        emphasized=True,
                    ),
                    Text(
                        scheme=scheme,
                        text="SUMMER 2025",
                        role=TypographyRole.LABEL_LARGE,
                        align=TextAlign.RIGHT,
                    ),
                ],
                weights=[1, 1],
            ),
            Column(
                scheme=scheme,
                gap=SPACE_150,
                weights=[1, 1],
                children=[
                    Row(
                        scheme=scheme,
                        gap=SPACE_150,
                        weights=[1, 1],
                        children=[
                            Image(
                                scheme=scheme,
                                source=photos[0],
                                fit=ImageFit.COVER,
                                shape=SHAPE_MEDIUM,
                            ),
                            Image(
                                scheme=scheme,
                                source=photos[1 % len(photos)],
                                fit=ImageFit.COVER,
                                shape=SHAPE_MEDIUM,
                            ),
                        ],
                    ),
                    Row(
                        scheme=scheme,
                        gap=SPACE_150,
                        weights=[1, 1],
                        children=[
                            Image(
                                scheme=scheme,
                                source=photos[2 % len(photos)],
                                fit=ImageFit.COVER,
                                shape=SHAPE_MEDIUM,
                            ),
                            Image(
                                scheme=scheme,
                                source=photos[3 % len(photos)],
                                fit=ImageFit.COVER,
                                shape=SHAPE_MEDIUM,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def daily_digest(photos: list[Path], scheme):
    """A compact photo-led dashboard with a small supporting image."""
    return Row(
        scheme=scheme,
        padding=SPACE_300,
        gap=SPACE_250,
        weights=[3, 2],
        children=[
            Image(
                scheme=scheme,
                source=photos[0],
                fit=ImageFit.COVER,
                focal_point=(0.5, 0.42),
                shape=SHAPE_EXTRA_LARGE,
            ),
            Column(
                scheme=scheme,
                gap=SPACE_150,
                main_sizes=[None, 96],
                children=[
                    Card(
                        scheme=scheme,
                        content_padding=SPACE_250,
                        children=[
                            Text(
                                scheme=scheme,
                                text="MONDAY",
                                role=TypographyRole.LABEL_LARGE,
                            ),
                            Text(
                                scheme=scheme,
                                text="08:42",
                                role=TypographyRole.DISPLAY_MEDIUM,
                                emphasized=True,
                                tabular_numbers=True,
                            ),
                            Text(
                                scheme=scheme,
                                text="A good day to get outside",
                                role=TypographyRole.TITLE_MEDIUM,
                            ),
                        ],
                    ),
                    Image(
                        scheme=scheme,
                        source=photos[1 % len(photos)],
                        fit=ImageFit.COVER,
                        focal_point=(0.5, 0.5),
                        shape=SHAPE_MEDIUM,
                    ),
                ],
            ),
        ],
    )


EXAMPLES = {
    "full_bleed": full_bleed,
    "gallery_triptych": gallery_triptych,
    "editorial": editorial,
    "side_by_side": side_by_side,
    "memory_grid": memory_grid,
    "daily_digest": daily_digest,
}

PHOTO_DIR = Path(__file__).parent / "photos"
DEFAULT_PHOTOS = [
    "IMG_0977~2.jpg",
    "F97ECF67-6D35-4D6E-99CE-CB109EADBE77.jpg",
    "IMG_1318.HEIC",
]


def readable_photos() -> list[Path]:
    photos = []
    for path in sorted(PHOTO_DIR.iterdir()):
        if not path.is_file():
            continue
        try:
            with PILImage.open(path) as image:
                image.verify()
            photos.append(path)
        except OSError, ValueError:
            continue
    return photos


def main() -> None:
    available = readable_photos()
    by_name = {path.name: path for path in available}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--photos",
        nargs="+",
        metavar="FILENAME",
        help="photo filenames from tests/photos (default: three representative photos)",
    )
    parser.add_argument(
        "--layouts",
        nargs="+",
        choices=EXAMPLES,
        default=list(EXAMPLES),
        help="layouts to render (default: all)",
    )
    parser.add_argument(
        "--all-photos", action="store_true", help="render every readable test photo"
    )
    parser.add_argument(
        "--list-photos", action="store_true", help="list readable photos and exit"
    )
    parser.add_argument("--output", type=Path, default=Path("tests/rendered_examples"))
    args = parser.parse_args()

    if args.list_photos:
        print("\n".join(path.name for path in available))
        return

    if args.all_photos and args.photos:
        parser.error("choose either --all-photos or --photos")
    requested = (
        [path.name for path in available]
        if args.all_photos
        else args.photos or DEFAULT_PHOTOS
    )
    missing = [name for name in requested if name not in by_name]
    if missing:
        parser.error(
            f"photo(s) not readable from {PHOTO_DIR}: {', '.join(missing)}; use --list-photos"
        )
    photos = [by_name[name] for name in requested]
    args.output.mkdir(parents=True, exist_ok=True)
    for photo_index, lead_photo in enumerate(photos):
        ordered_photos = photos[photo_index:] + photos[:photo_index]
        scheme = scheme_for(lead_photo)
        for layout_name in args.layouts:
            image = render(EXAMPLES[layout_name](ordered_photos, scheme), WIDTH, HEIGHT)
            path = args.output / f"{layout_name}--{lead_photo.stem}.png"
            image.save(path)
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()
