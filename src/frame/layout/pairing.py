"""Pairing layout displaying the setup QR code for Frame Flow."""

from dataclasses import dataclass
from typing import Any

from material_color_utilities import DynamicScheme, theme_from_color

from frame.flow.settings import FlowSettings
from frame.ui import (
    PRIMARY,
    SPACE_100,
    SPACE_150,
    SPACE_175,
    SPACE_200,
    SPACE_300,
    SURFACE_CONTAINER,
    SURFACE_CONTAINER_LOW,
    Card,
    Center,
    Column,
    Element,
    QRCode,
    Row,
    Spacer,
    Text,
    TextAlign,
    TypographyRole,
)
from frame.ui.drawing import Drawing


def _default_scheme() -> DynamicScheme:
    return theme_from_color("#6750A4").schemes.light


def pairing_layout(
    target: Any,
    *,
    scheme: DynamicScheme | None = None,
    frame_name: str | None = None,
    frame_key: str | None = None,
    status_text: str = "Ready to connect",
) -> Element:
    """Build a Material 3 pairing layout displaying the flow setup QR code."""
    if isinstance(target, FlowSettings) or (
        hasattr(target, "pairing_url") and hasattr(target, "frame_key")
    ):
        pairing_url = target.pairing_url
        name = frame_name or target.frame_name
        key = frame_key or target.frame_key
        active_scheme = (
            scheme
            if scheme is not None
            else theme_from_color(target.theme_color).schemes.light
        )
    else:
        pairing_url = target
        name = frame_name or "Frame"
        key = frame_key or ""
        active_scheme = scheme or _default_scheme()

    key_display = f"...{key[-8:]}" if len(key) >= 12 else key

    return Row(
        scheme=active_scheme,
        padding=SPACE_300,
        gap=SPACE_200,
        weights=[4, 3],
        children=[
            Column(
                scheme=active_scheme,
                padding=SPACE_150,
                gap=SPACE_175,
                children=[
                    Text(
                        scheme=active_scheme,
                        text="CONNECT TO PHONE",
                        role=TypographyRole.LABEL_MEDIUM,
                        fgcolor=PRIMARY,
                    ),
                    Text(
                        scheme=active_scheme,
                        text="Connect your frame",
                        role=TypographyRole.HEADLINE_LARGE,
                        emphasized=True,
                    ),
                    Text(
                        scheme=active_scheme,
                        text="Scan the QR code with your phone camera to pair with Frame Flow and connect Google Photos.",
                        role=TypographyRole.BODY_LARGE,
                    ),
                    Spacer(scheme=active_scheme, flex_weight=1),
                    Card(
                        scheme=active_scheme,
                        bgcolor=SURFACE_CONTAINER_LOW,
                        content_padding=SPACE_150,
                        children=[
                            Row(
                                scheme=active_scheme,
                                gap=SPACE_100,
                                children=[
                                    Text(
                                        scheme=active_scheme,
                                        text=f"Frame: {name}",
                                        role=TypographyRole.TITLE_SMALL,
                                        emphasized=True,
                                    ),
                                    Spacer(scheme=active_scheme, flex_weight=1),
                                    Text(
                                        scheme=active_scheme,
                                        text=status_text,
                                        role=TypographyRole.LABEL_SMALL,
                                        fgcolor=PRIMARY,
                                    ),
                                ],
                            ),
                            Text(
                                scheme=active_scheme,
                                text=f"Key: {key_display}",
                                role=TypographyRole.BODY_SMALL,
                                tabular_numbers=True,
                            ),
                        ],
                    ),
                ],
            ),
            Center(
                scheme=active_scheme,
                child=Card(
                    scheme=active_scheme,
                    bgcolor=SURFACE_CONTAINER,
                    content_padding=SPACE_200,
                    children=[
                        QRCode(
                            scheme=active_scheme,
                            data=pairing_url,
                        ),
                        Text(
                            scheme=active_scheme,
                            text="Scan with camera",
                            role=TypographyRole.LABEL_MEDIUM,
                            align=TextAlign.CENTER,
                        ),
                    ],
                ),
            ),
        ],
    )


@dataclass(kw_only=True)
class PairingLayout(Element):
    """Pairing layout element that can be rendered directly."""

    target: Any
    frame_name: str | None = None
    frame_key: str | None = None
    status_text: str = "Ready to connect"

    def __init__(
        self,
        target: Any,
        *,
        scheme: DynamicScheme | None = None,
        frame_name: str | None = None,
        frame_key: str | None = None,
        status_text: str = "Ready to connect",
        **kwargs: Any,
    ) -> None:
        active_scheme = (
            scheme
            if scheme is not None
            else (
                theme_from_color(target.theme_color).schemes.light
                if isinstance(target, FlowSettings)
                or (hasattr(target, "theme_color") and hasattr(target, "pairing_url"))
                else _default_scheme()
            )
        )
        super().__init__(scheme=active_scheme, **kwargs)
        self.target = target
        self.frame_name = frame_name
        self.frame_key = frame_key
        self.status_text = status_text

    def draw(self, draw: Drawing, x: int, y: int, width: int, height: int) -> None:
        tree = pairing_layout(
            self.target,
            scheme=self.scheme,
            frame_name=self.frame_name,
            frame_key=self.frame_key,
            status_text=self.status_text,
        )
        tree.draw(draw, x, y, width, height)
