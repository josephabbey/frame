# Frame

A small, noninteractive PIL interface toolkit for Inky Impression photo frames.
It uses logical display pixels, supersampled drawing for smoother text and
rounded geometry, and a seven-color output palette with optional dithering for
photographs.

## Data contracts

`frame.data` contains provider-neutral, immutable structures for calendar,
tasks, photos, weather, and account/OAuth data. Each domain exposes an async
`*API` protocol for a provider implementation to satisfy, without coupling the
display layer to a particular service or HTTP client.

```python
from frame.data import CalendarAPI, Task, Weather

# Implement CalendarAPI, TasksAPI, PhotosAPI, WeatherAPI, or AccountAPI for
# the services used by a frame installation.
```

Google implementations live in `frame.data.google`. Supply a `GoogleTransport`
backed by the application's async HTTP client, an OAuth token for Calendar,
Tasks, Photos, and account calls, and a Maps Weather API key for weather calls.

```python
from material_color_utilities import theme_from_color
from frame.ui import (
    SPACE_200,
    SPACE_300,
    Card,
    Column,
    Image,
    ImageFit,
    Text,
    TypographyRole,
    render,
)

scheme = theme_from_color("#6750a4").schemes.light
screen = Column(
    scheme=scheme,
    padding=SPACE_300,
    gap=SPACE_200,
    main_sizes=[None, 70],
    children=[
        Image(scheme=scheme, source="photos/favourite.jpg", fit=ImageFit.COVER),
        Card(
            scheme=scheme,
            radius=28,
            children=[
                Text(
                    scheme=scheme,
                    text="A favourite moment",
                    role=TypographyRole.TITLE_LARGE,
                    emphasized=True,
                )
            ],
        ),
    ],
)
output = render(screen, width=800, height=480)
output.save("frame.png")
```

Compose `Row` and `Column` elements with `main_sizes` for fixed logical-pixel
children and `weights` for flexible children. `Padding`, `Spacer`, `Card`,
`RoundedBox`, `Text`, `Image`, and `QRCode` are available as building blocks.
Use `ImageFit.COVER` for a crop-to-fill photograph or `ImageFit.CONTAIN` to
preserve the entire image. `render` returns an RGB image ready for the Inky
driver; pass `dither=Image.Dither.NONE` for a clean, stable palette mapping
when dithering is undesirable.

`Text` uses `TypographyRole.BODY_LARGE` by default. Select one of the
`TypographyRole` constants for the display, headline, title, body, or label
hierarchy. Use `emphasized=True` for expressive moments;
provide `font` and `bold_font` paths to select the regular and emphasized faces
available on your frame. Variable fonts use their weight axis when available;
`weight` can override a role's default. `tabular_numbers=True` enables tabular
figures for values such as dates and clocks. The role scale is exposed as
`MATERIAL_3_TYPE_SCALE` and can be overridden with a per-element `type_scale`,
or customized with `size`, `line_height`, and `letter_spacing`. Font lookup
prefers installed Roboto faces and falls back to DejaVu Sans when available.

Use the `SPACE_*` values for spacing in `Row`, `Column`, `Stack`, `Padding`, and
`Card`. They follow the Material 3 scale, where `SPACE_100` is 8 logical pixels;
the scale also includes smaller and fractional steps such as 2, 6, 12, and 20.
Provide a custom immutable `Spacing` object on a layout or component to adapt
the token values for a particular frame or density. Set padding and gaps on
their parent layouts to keep component spacing consistent.

Use `Shape` tokens to keep card corners and image crops in a shared Material 3
shape scale. The presets range from `SHAPE_NONE` through `SHAPE_EXTRA_SMALL`,
`SHAPE_SMALL`, `SHAPE_MEDIUM`, `SHAPE_LARGE`, `SHAPE_EXTRA_LARGE`, and
`SHAPE_FULL`. `Card` defaults to the medium rounded shape; featured photos can
use extra-large corners. A shape uses the rounded family by default and can use
the cut family instead. `SHAPE_EXTRA_LARGE_TOP` demonstrates asymmetric top
corners. Expressive silhouettes such as `SHAPE_ARCH_LARGE`, `SHAPE_OVAL`, and
`SHAPE_DIAMOND` are separate from the corner family. Pass a preset as `shape=`
to `Card`, `RoundedBox`, or `Image`.
