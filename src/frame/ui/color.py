from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from material_color_utilities import DynamicScheme


@dataclass
class Color(ABC):
    @abstractmethod
    def __call__(self, scheme: DynamicScheme):
        pass


@dataclass
class HexColor:
    color: str

    def __call__(self, scheme: DynamicScheme):
        return self.color


@dataclass
class SchemeColor(Color):
    color: Literal[
        "background",
        "surface",
        "surface_dim",
        "surface_bright",
        "surface_container_lowest",
        "surface_container_low",
        "surface_container",
        "surface_container_high",
        "surface_container_highest",
        "on_surface",
        "surface_variant",
        "on_surface_variant",
        "inverse_surface",
        "inverse_on_surface",
        "outline",
        "outline_variant",
        "shadow",
        "scrim",
        "surface_tint",
        "primary",
        "on_primary",
        "primary_container",
        "on_primary_container",
        "inverse_primary",
        "secondary",
        "on_secondary",
        "secondary_container",
        "on_secondary_container",
        "tertiary",
        "on_tertiary",
        "tertiary_container",
        "on_tertiary_container",
        "error",
        "on_error",
        "error_container",
        "on_error_container",
        "primary_fixed",
        "primary_fixed_dim",
        "on_primary_fixed",
        "on_primary_fixed_variant",
        "secondary_fixed",
        "secondary_fixed_dim",
        "on_secondary_fixed",
        "on_secondary_fixed_variant",
        "tertiary_fixed",
        "tertiary_fixed_dim",
        "on_tertiary_fixed",
        "on_tertiary_fixed_variant",
    ]

    def __call__(self, scheme: DynamicScheme):
        return getattr(scheme, self.color)


BACKGROUND = field(default_factory=lambda: SchemeColor("background"))
SURFACE = field(default_factory=lambda: SchemeColor("surface"))
SURFACE_DIM = field(default_factory=lambda: SchemeColor("surface_dim"))
SURFACE_BRIGHT = field(default_factory=lambda: SchemeColor("surface_bright"))
SURFACE_CONTAINER_LOWEST = field(default_factory=lambda: SchemeColor("surface_container_lowest"))
SURFACE_CONTAINER_LOW = field(default_factory=lambda: SchemeColor("surface_container_low"))
SURFACE_CONTAINER = field(default_factory=lambda: SchemeColor("surface_container"))
SURFACE_CONTAINER_HIGH = field(default_factory=lambda: SchemeColor("surface_container_high"))
SURFACE_CONTAINER_HIGHEST = field(default_factory=lambda: SchemeColor("surface_container_highest"))
ON_SURFACE = field(default_factory=lambda: SchemeColor("on_surface"))
SURFACE_VARIANT = field(default_factory=lambda: SchemeColor("surface_variant"))
ON_SURFACE_VARIANT = field(default_factory=lambda: SchemeColor("on_surface_variant"))
INVERSE_SURFACE = field(default_factory=lambda: SchemeColor("inverse_surface"))
INVERSE_ON_SURFACE = field(default_factory=lambda: SchemeColor("inverse_on_surface"))
OUTLINE = field(default_factory=lambda: SchemeColor("outline"))
OUTLINE_VARIANT = field(default_factory=lambda: SchemeColor("outline_variant"))
SHADOW = field(default_factory=lambda: SchemeColor("shadow"))
SCRIM = field(default_factory=lambda: SchemeColor("scrim"))
SURFACE_TINT = field(default_factory=lambda: SchemeColor("surface_tint"))
PRIMARY = field(default_factory=lambda: SchemeColor("primary"))
ON_PRIMARY = field(default_factory=lambda: SchemeColor("on_primary"))
PRIMARY_CONTAINER = field(default_factory=lambda: SchemeColor("primary_container"))
ON_PRIMARY_CONTAINER = field(default_factory=lambda: SchemeColor("on_primary_container"))
INVERSE_PRIMARY = field(default_factory=lambda: SchemeColor("inverse_primary"))
SECONDARY = field(default_factory=lambda: SchemeColor("secondary"))
ON_SECONDARY = field(default_factory=lambda: SchemeColor("on_secondary"))
SECONDARY_CONTAINER = field(default_factory=lambda: SchemeColor("secondary_container"))
ON_SECONDARY_CONTAINER = field(default_factory=lambda: SchemeColor("on_secondary_container"))
TERTIARY = field(default_factory=lambda: SchemeColor("tertiary"))
ON_TERTIARY = field(default_factory=lambda: SchemeColor("on_tertiary"))
TERTIARY_CONTAINER = field(default_factory=lambda: SchemeColor("tertiary_container"))
ON_TERTIARY_CONTAINER = field(default_factory=lambda: SchemeColor("on_tertiary_container"))
ERROR = field(default_factory=lambda: SchemeColor("error"))
ON_ERROR = field(default_factory=lambda: SchemeColor("on_error"))
ERROR_CONTAINER = field(default_factory=lambda: SchemeColor("error_container"))
ON_ERROR_CONTAINER = field(default_factory=lambda: SchemeColor("on_error_container"))
PRIMARY_FIXED = field(default_factory=lambda: SchemeColor("primary_fixed"))
PRIMARY_FIXED_DIM = field(default_factory=lambda: SchemeColor("primary_fixed_dim"))
ON_PRIMARY_FIXED = field(default_factory=lambda: SchemeColor("on_primary_fixed"))
ON_PRIMARY_FIXED_VARIANT = field(default_factory=lambda: SchemeColor("on_primary_fixed_variant"))
SECONDARY_FIXED = field(default_factory=lambda: SchemeColor("secondary_fixed"))
SECONDARY_FIXED_DIM = field(default_factory=lambda: SchemeColor("secondary_fixed_dim"))
ON_SECONDARY_FIXED = field(default_factory=lambda: SchemeColor("on_secondary_fixed"))
ON_SECONDARY_FIXED_VARIANT = field(default_factory=lambda: SchemeColor("on_secondary_fixed_variant"))
TERTIARY_FIXED = field(default_factory=lambda: SchemeColor("tertiary_fixed"))
TERTIARY_FIXED_DIM = field(default_factory=lambda: SchemeColor("tertiary_fixed_dim"))
ON_TERTIARY_FIXED = field(default_factory=lambda: SchemeColor("on_tertiary_fixed"))
ON_TERTIARY_FIXED_VARIANT = field(default_factory=lambda: SchemeColor("on_tertiary_fixed_variant"))
