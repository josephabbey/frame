"""Pairing layout displaying the setup QR code for Frame Flow."""

from material_color_utilities import DynamicScheme

from frame.flow.client import FLOW_CLIENT
from frame.flow.store import FLOW_STORE
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


def pairing_layout(
  scheme: DynamicScheme,
  *,
  status_text: str = "Ready to connect",
) -> Element:
  """Build a Material 3 pairing layout displaying the flow setup QR code."""

  pairing_url = FLOW_CLIENT.pairing_url
  key = FLOW_STORE.key

  key_display = f"...{key[-32:]}" if len(key) >= 12 else key

  return Row(
    scheme=scheme,
    padding=SPACE_300,
    gap=SPACE_200,
    weights=[4, 3],
    children=[
      Column(
        scheme=scheme,
        padding=SPACE_150,
        gap=SPACE_175,
        children=[
          Text(
            scheme=scheme,
            text="CONNECT TO PHONE",
            role=TypographyRole.LABEL_MEDIUM,
            fgcolor=PRIMARY,
          ),
          Text(
            scheme=scheme,
            text="Connect your frame",
            role=TypographyRole.HEADLINE_LARGE,
            emphasized=True,
          ),
          Text(
            scheme=scheme,
            text="Scan the QR code with your phone camera to pair with Frame Flow and connect Google Photos.",
            role=TypographyRole.BODY_LARGE,
          ),
          Spacer(scheme=scheme, flex_weight=1),
          Card(
            scheme=scheme,
            bgcolor=SURFACE_CONTAINER_LOW,
            content_padding=SPACE_150,
            children=[
              Row(
                scheme=scheme,
                gap=SPACE_100,
                children=[
                  Text(
                    scheme=scheme,
                    text="Frame",
                    role=TypographyRole.TITLE_SMALL,
                    emphasized=True,
                  ),
                  Spacer(scheme=scheme, flex_weight=1),
                  Text(
                    scheme=scheme,
                    text=status_text,
                    role=TypographyRole.LABEL_SMALL,
                    fgcolor=PRIMARY,
                  ),
                ],
              ),
              Text(
                scheme=scheme,
                text=f"Key: {key_display}",
                role=TypographyRole.BODY_SMALL,
                font="Roboto Mono",
                tabular_numbers=True,
              ),
            ],
          ),
        ],
      ),
      Center(
        scheme=scheme,
        child=Card(
          scheme=scheme,
          bgcolor=SURFACE_CONTAINER,
          content_padding=SPACE_200,
          children=[
            QRCode(
              scheme=scheme,
              data=pairing_url,
            ),
            Text(
              scheme=scheme,
              text="Scan with camera",
              role=TypographyRole.LABEL_MEDIUM,
              align=TextAlign.CENTER,
            ),
          ],
        ),
      ),
    ],
  )
