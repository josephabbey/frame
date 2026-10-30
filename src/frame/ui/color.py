from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from material_color_utilities import DynamicScheme

ColorValue = str | int | tuple[int, ...]


class ColorRole(StrEnum):
    BACKGROUND = "background"
    SURFACE = "surface"
    SURFACE_DIM = "surface_dim"
    SURFACE_BRIGHT = "surface_bright"
    SURFACE_CONTAINER_LOWEST = "surface_container_lowest"
    SURFACE_CONTAINER_LOW = "surface_container_low"
    SURFACE_CONTAINER = "surface_container"
    SURFACE_CONTAINER_HIGH = "surface_container_high"
    SURFACE_CONTAINER_HIGHEST = "surface_container_highest"
    ON_SURFACE = "on_surface"
    SURFACE_VARIANT = "surface_variant"
    ON_SURFACE_VARIANT = "on_surface_variant"
    INVERSE_SURFACE = "inverse_surface"
    INVERSE_ON_SURFACE = "inverse_on_surface"
    OUTLINE = "outline"
    OUTLINE_VARIANT = "outline_variant"
    SHADOW = "shadow"
    SCRIM = "scrim"
    SURFACE_TINT = "surface_tint"
    PRIMARY = "primary"
    ON_PRIMARY = "on_primary"
    PRIMARY_CONTAINER = "primary_container"
    ON_PRIMARY_CONTAINER = "on_primary_container"
    INVERSE_PRIMARY = "inverse_primary"
    SECONDARY = "secondary"
    ON_SECONDARY = "on_secondary"
    SECONDARY_CONTAINER = "secondary_container"
    ON_SECONDARY_CONTAINER = "on_secondary_container"
    TERTIARY = "tertiary"
    ON_TERTIARY = "on_tertiary"
    TERTIARY_CONTAINER = "tertiary_container"
    ON_TERTIARY_CONTAINER = "on_tertiary_container"
    ERROR = "error"
    ON_ERROR = "on_error"
    ERROR_CONTAINER = "error_container"
    ON_ERROR_CONTAINER = "on_error_container"
    PRIMARY_FIXED = "primary_fixed"
    PRIMARY_FIXED_DIM = "primary_fixed_dim"
    ON_PRIMARY_FIXED = "on_primary_fixed"
    ON_PRIMARY_FIXED_VARIANT = "on_primary_fixed_variant"
    SECONDARY_FIXED = "secondary_fixed"
    SECONDARY_FIXED_DIM = "secondary_fixed_dim"
    ON_SECONDARY_FIXED = "on_secondary_fixed"
    ON_SECONDARY_FIXED_VARIANT = "on_secondary_fixed_variant"
    TERTIARY_FIXED = "tertiary_fixed"
    TERTIARY_FIXED_DIM = "tertiary_fixed_dim"
    ON_TERTIARY_FIXED = "on_tertiary_fixed"
    ON_TERTIARY_FIXED_VARIANT = "on_tertiary_fixed_variant"


class Color(ABC):
    @abstractmethod
    def __call__(self, scheme: DynamicScheme) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class HexColor(Color):
    value: str

    def __call__(self, scheme: DynamicScheme) -> str:
        return self.value


@dataclass(frozen=True)
class SchemeColor(Color):
    role: ColorRole

    def __call__(self, scheme: DynamicScheme) -> str:
        return getattr(scheme, self.role.value)


BACKGROUND = SchemeColor(ColorRole.BACKGROUND)
SURFACE = SchemeColor(ColorRole.SURFACE)
SURFACE_DIM = SchemeColor(ColorRole.SURFACE_DIM)
SURFACE_BRIGHT = SchemeColor(ColorRole.SURFACE_BRIGHT)
SURFACE_CONTAINER_LOWEST = SchemeColor(ColorRole.SURFACE_CONTAINER_LOWEST)
SURFACE_CONTAINER_LOW = SchemeColor(ColorRole.SURFACE_CONTAINER_LOW)
SURFACE_CONTAINER = SchemeColor(ColorRole.SURFACE_CONTAINER)
SURFACE_CONTAINER_HIGH = SchemeColor(ColorRole.SURFACE_CONTAINER_HIGH)
SURFACE_CONTAINER_HIGHEST = SchemeColor(ColorRole.SURFACE_CONTAINER_HIGHEST)
ON_SURFACE = SchemeColor(ColorRole.ON_SURFACE)
SURFACE_VARIANT = SchemeColor(ColorRole.SURFACE_VARIANT)
ON_SURFACE_VARIANT = SchemeColor(ColorRole.ON_SURFACE_VARIANT)
INVERSE_SURFACE = SchemeColor(ColorRole.INVERSE_SURFACE)
INVERSE_ON_SURFACE = SchemeColor(ColorRole.INVERSE_ON_SURFACE)
OUTLINE = SchemeColor(ColorRole.OUTLINE)
OUTLINE_VARIANT = SchemeColor(ColorRole.OUTLINE_VARIANT)
SHADOW = SchemeColor(ColorRole.SHADOW)
SCRIM = SchemeColor(ColorRole.SCRIM)
SURFACE_TINT = SchemeColor(ColorRole.SURFACE_TINT)
PRIMARY = SchemeColor(ColorRole.PRIMARY)
ON_PRIMARY = SchemeColor(ColorRole.ON_PRIMARY)
PRIMARY_CONTAINER = SchemeColor(ColorRole.PRIMARY_CONTAINER)
ON_PRIMARY_CONTAINER = SchemeColor(ColorRole.ON_PRIMARY_CONTAINER)
INVERSE_PRIMARY = SchemeColor(ColorRole.INVERSE_PRIMARY)
SECONDARY = SchemeColor(ColorRole.SECONDARY)
ON_SECONDARY = SchemeColor(ColorRole.ON_SECONDARY)
SECONDARY_CONTAINER = SchemeColor(ColorRole.SECONDARY_CONTAINER)
ON_SECONDARY_CONTAINER = SchemeColor(ColorRole.ON_SECONDARY_CONTAINER)
TERTIARY = SchemeColor(ColorRole.TERTIARY)
ON_TERTIARY = SchemeColor(ColorRole.ON_TERTIARY)
TERTIARY_CONTAINER = SchemeColor(ColorRole.TERTIARY_CONTAINER)
ON_TERTIARY_CONTAINER = SchemeColor(ColorRole.ON_TERTIARY_CONTAINER)
ERROR = SchemeColor(ColorRole.ERROR)
ON_ERROR = SchemeColor(ColorRole.ON_ERROR)
ERROR_CONTAINER = SchemeColor(ColorRole.ERROR_CONTAINER)
ON_ERROR_CONTAINER = SchemeColor(ColorRole.ON_ERROR_CONTAINER)
PRIMARY_FIXED = SchemeColor(ColorRole.PRIMARY_FIXED)
PRIMARY_FIXED_DIM = SchemeColor(ColorRole.PRIMARY_FIXED_DIM)
ON_PRIMARY_FIXED = SchemeColor(ColorRole.ON_PRIMARY_FIXED)
ON_PRIMARY_FIXED_VARIANT = SchemeColor(ColorRole.ON_PRIMARY_FIXED_VARIANT)
SECONDARY_FIXED = SchemeColor(ColorRole.SECONDARY_FIXED)
SECONDARY_FIXED_DIM = SchemeColor(ColorRole.SECONDARY_FIXED_DIM)
ON_SECONDARY_FIXED = SchemeColor(ColorRole.ON_SECONDARY_FIXED)
ON_SECONDARY_FIXED_VARIANT = SchemeColor(ColorRole.ON_SECONDARY_FIXED_VARIANT)
TERTIARY_FIXED = SchemeColor(ColorRole.TERTIARY_FIXED)
TERTIARY_FIXED_DIM = SchemeColor(ColorRole.TERTIARY_FIXED_DIM)
ON_TERTIARY_FIXED = SchemeColor(ColorRole.ON_TERTIARY_FIXED)
ON_TERTIARY_FIXED_VARIANT = SchemeColor(ColorRole.ON_TERTIARY_FIXED_VARIANT)
