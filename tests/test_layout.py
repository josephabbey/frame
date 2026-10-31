from pathlib import Path

from material_color_utilities import theme_from_color
from PIL import Image as PILImage

from frame.flow.settings import FlowSettings
from frame.layout import (
    PairingLayout,
    editorial,
    full_bleed,
    gallery_triptych,
    pairing_layout,
)
from frame.ui import render


def test_pairing_layout_renders_from_settings():
    settings = FlowSettings(
        frame_key="abcdef1234567890abcdef123456",
        frame_name="Living Room",
        flow_url="https://frame-flow-mocha-eight.vercel.app/",
    )
    element = pairing_layout(settings)
    image = render(element, width=800, height=480)

    assert image.size == (800, 480)
    assert image.mode == "RGB"


def test_pairing_layout_class_renders_from_string():
    layout = PairingLayout(
        "https://frame-flow-mocha-eight.vercel.app/?key=123456789012345678901234&name=Frame",
        frame_name="Bedside",
        frame_key="123456789012345678901234",
    )
    image = render(layout, width=800, height=480)

    image.show()

    assert image.size == (800, 480)


def test_photo_layouts_render_with_test_photos():
    photo_dir = Path(__file__).parent / "photos"
    sample_photos = sorted(photo_dir.glob("*.jpg"))
    if not sample_photos:
        # Fall back to creating a dummy RGB image if photos directory has no jpgs
        dummy = Path(__file__).parent / "test_photo.png"
        PILImage.new("RGB", (400, 300), (100, 150, 200)).save(dummy)
        sample_photos = [dummy]

    scheme = theme_from_color("#4A6572").schemes.light
    photos = [sample_photos[0]] * 3

    for layout_fn in (full_bleed, gallery_triptych, editorial):
        elem = layout_fn(photos, scheme)
        image = render(elem, width=800, height=480)
        assert image.size == (800, 480)
