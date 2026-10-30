from dataclasses import dataclass
from enum import StrEnum


class TypographyRole(StrEnum):
    DISPLAY_LARGE = "display_large"
    DISPLAY_MEDIUM = "display_medium"
    DISPLAY_SMALL = "display_small"
    HEADLINE_LARGE = "headline_large"
    HEADLINE_MEDIUM = "headline_medium"
    HEADLINE_SMALL = "headline_small"
    TITLE_LARGE = "title_large"
    TITLE_MEDIUM = "title_medium"
    TITLE_SMALL = "title_small"
    BODY_LARGE = "body_large"
    BODY_MEDIUM = "body_medium"
    BODY_SMALL = "body_small"
    LABEL_LARGE = "label_large"
    LABEL_MEDIUM = "label_medium"
    LABEL_SMALL = "label_small"


@dataclass(frozen=True)
class TypeStyle:
    size: int
    line_height: int
    tracking: float = 0
    weight: int = 400
    emphasized_weight: int = 500


# Material 3 type scale. Display and headline styles get generous leading for
# editorial layouts; body and label styles remain compact and easy to scan.
MATERIAL_3_TYPE_SCALE: dict[TypographyRole, TypeStyle] = {
    TypographyRole.DISPLAY_LARGE: TypeStyle(57, 64, -0.25),
    TypographyRole.DISPLAY_MEDIUM: TypeStyle(45, 52),
    TypographyRole.DISPLAY_SMALL: TypeStyle(36, 44),
    TypographyRole.HEADLINE_LARGE: TypeStyle(32, 40),
    TypographyRole.HEADLINE_MEDIUM: TypeStyle(28, 36),
    TypographyRole.HEADLINE_SMALL: TypeStyle(24, 32),
    TypographyRole.TITLE_LARGE: TypeStyle(22, 28),
    TypographyRole.TITLE_MEDIUM: TypeStyle(16, 24, 0.15, 500, 600),
    TypographyRole.TITLE_SMALL: TypeStyle(14, 20, 0.1, 500, 600),
    TypographyRole.BODY_LARGE: TypeStyle(16, 24, 0.5),
    TypographyRole.BODY_MEDIUM: TypeStyle(14, 20, 0.25),
    TypographyRole.BODY_SMALL: TypeStyle(12, 16, 0.4),
    TypographyRole.LABEL_LARGE: TypeStyle(14, 20, 0.1, 500, 600),
    TypographyRole.LABEL_MEDIUM: TypeStyle(12, 16, 0.5, 500, 600),
    TypographyRole.LABEL_SMALL: TypeStyle(11, 16, 0.5, 500, 600),
}
