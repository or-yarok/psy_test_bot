from enum import Enum, auto
from typing import Any

class AutoGen(Enum):
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return name.lower()

class Commands(AutoGen):
    QUIT       = auto()
    DISCLAIMER = auto()
    AUTHOR     = auto()
    CREDITS    = auto()
    MENU       = auto()


all_commands = [cmd.value for cmd in Commands]


