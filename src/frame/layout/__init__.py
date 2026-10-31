"""Layout submodule for Frame."""

from .pairing import PairingLayout, pairing_layout
from .photos import editorial, full_bleed, gallery_triptych

__all__ = [
    "PairingLayout",
    "editorial",
    "full_bleed",
    "gallery_triptych",
    "pairing_layout",
]
