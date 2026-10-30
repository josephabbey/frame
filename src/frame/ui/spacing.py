from dataclasses import dataclass
from enum import StrEnum


class SpacingToken(StrEnum):
    SPACE_0 = "space0"
    SPACE_25 = "space25"
    SPACE_50 = "space50"
    SPACE_75 = "space75"
    SPACE_100 = "space100"
    SPACE_125 = "space125"
    SPACE_150 = "space150"
    SPACE_175 = "space175"
    SPACE_200 = "space200"
    SPACE_250 = "space250"
    SPACE_300 = "space300"
    SPACE_400 = "space400"
    SPACE_450 = "space450"
    SPACE_500 = "space500"
    SPACE_600 = "space600"
    SPACE_700 = "space700"
    SPACE_800 = "space800"
    SPACE_900 = "space900"


@dataclass(frozen=True)
class Spacing:
    """Material 3 spacing scale, in logical display pixels (dp equivalents)."""

    space0: int = 0
    space25: int = 2
    space50: int = 4
    space75: int = 6
    space100: int = 8
    space125: int = 10
    space150: int = 12
    space175: int = 14
    space200: int = 16
    space250: int = 20
    space300: int = 24
    space400: int = 32
    space450: int = 36
    space500: int = 40
    space600: int = 48
    space700: int = 56
    space800: int = 64
    space900: int = 72

    def resolve(self, value: int | SpacingToken) -> int:
        return getattr(self, value.value) if isinstance(value, SpacingToken) else value


M3_SPACING = Spacing()

SPACE_0 = SpacingToken.SPACE_0
SPACE_25 = SpacingToken.SPACE_25
SPACE_50 = SpacingToken.SPACE_50
SPACE_75 = SpacingToken.SPACE_75
SPACE_100 = SpacingToken.SPACE_100
SPACE_125 = SpacingToken.SPACE_125
SPACE_150 = SpacingToken.SPACE_150
SPACE_175 = SpacingToken.SPACE_175
SPACE_200 = SpacingToken.SPACE_200
SPACE_250 = SpacingToken.SPACE_250
SPACE_300 = SpacingToken.SPACE_300
SPACE_400 = SpacingToken.SPACE_400
SPACE_450 = SpacingToken.SPACE_450
SPACE_500 = SpacingToken.SPACE_500
SPACE_600 = SpacingToken.SPACE_600
SPACE_700 = SpacingToken.SPACE_700
SPACE_800 = SpacingToken.SPACE_800
SPACE_900 = SpacingToken.SPACE_900
