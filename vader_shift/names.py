from __future__ import annotations

from typing import Mapping

SOURCE_BUTTONS = [
    "south",
    "east",
    "west",
    "north",
    "back",
    "guide",
    "start",
    "left_stick",
    "right_stick",
    "left_shoulder",
    "right_shoulder",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "misc1",
    "right_paddle1",
    "left_paddle1",
    "right_paddle2",
    "left_paddle2",
    "touchpad",
    "misc2",
    "misc3",
    "misc4",
    "misc5",
    "misc6",
]

SOURCE_AXES = [
    "leftx",
    "lefty",
    "rightx",
    "righty",
    "left_trigger",
    "right_trigger",
]

OUTPUT_BUTTONS = [
    "a",
    "b",
    "x",
    "y",
    "back",
    "guide",
    "start",
    "left_stick",
    "right_stick",
    "left_shoulder",
    "right_shoulder",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "none",
]

DEFAULT_SOURCE_TO_OUTPUT = {
    "south": "a",
    "east": "b",
    "west": "x",
    "north": "y",
    "back": "back",
    "guide": "guide",
    "start": "start",
    "left_stick": "left_stick",
    "right_stick": "right_stick",
    "left_shoulder": "left_shoulder",
    "right_shoulder": "right_shoulder",
    "dpad_up": "dpad_up",
    "dpad_down": "dpad_down",
    "dpad_left": "dpad_left",
    "dpad_right": "dpad_right",
}

DEFAULT_SOURCE_ALIASES = {
    "a": "south",
    "b": "east",
    "x": "west",
    "y": "north",
    "back": "back",
    "select": "back",
    "view": "back",
    "guide": "guide",
    "home": "guide",
    "start": "start",
    "menu": "start",
    "options": "start",
    "ls": "left_stick",
    "l3": "left_stick",
    "rs": "right_stick",
    "r3": "right_stick",
    "lb": "left_shoulder",
    "l1": "left_shoulder",
    "rb": "right_shoulder",
    "r1": "right_shoulder",
    "up": "dpad_up",
    "down": "dpad_down",
    "left": "dpad_left",
    "right": "dpad_right",
    "du": "dpad_up",
    "dd": "dpad_down",
    "dl": "dpad_left",
    "dr": "dpad_right",
    "share": "misc1",
}

OUTPUT_ALIASES = {
    "south": "a",
    "east": "b",
    "west": "x",
    "north": "y",
    "lb": "left_shoulder",
    "l1": "left_shoulder",
    "rb": "right_shoulder",
    "r1": "right_shoulder",
    "ls": "left_stick",
    "rs": "right_stick",
    "l3": "left_stick",
    "r3": "right_stick",
    "du": "dpad_up",
    "dd": "dpad_down",
    "dl": "dpad_left",
    "dr": "dpad_right",
    "pass": "none",
    "off": "none",
    "null": "none",
}


def normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _merged_aliases(user_aliases: Mapping[str, str] | None = None) -> dict[str, str]:
    aliases = {normalize_name(k): normalize_name(v) for k, v in DEFAULT_SOURCE_ALIASES.items()}
    if user_aliases:
        aliases.update({normalize_name(k): normalize_name(v) for k, v in user_aliases.items()})
    return aliases


def canonical_source_button(name: str, user_aliases: Mapping[str, str] | None = None) -> str:
    value = normalize_name(name)
    aliases = _merged_aliases(user_aliases)
    seen: set[str] = set()
    while value in aliases:
        if value in seen:
            raise ValueError(f"Circular alias detected for source button '{name}'")
        seen.add(value)
        value = aliases[value]
    if value not in SOURCE_BUTTONS:
        raise ValueError(
            f"Unknown source button '{name}'. Supported canonical names: {', '.join(SOURCE_BUTTONS)}"
        )
    return value


def canonical_output_button(name: str) -> str:
    value = normalize_name(name)
    value = OUTPUT_ALIASES.get(value, value)
    if value not in OUTPUT_BUTTONS:
        raise ValueError(
            f"Unknown output button '{name}'. Supported canonical names: {', '.join(OUTPUT_BUTTONS)}"
        )
    return value


def pretty_aliases_for_button(button_name: str, user_aliases: Mapping[str, str] | None = None) -> list[str]:
    canonical = canonical_source_button(button_name, user_aliases)
    aliases = _merged_aliases(user_aliases)
    return sorted([alias for alias, target in aliases.items() if target == canonical])
