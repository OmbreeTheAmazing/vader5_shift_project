from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .names import canonical_output_button, canonical_source_button, normalize_name


@dataclass(frozen=True)
class ResolvedLayer:
    name: str
    when_held: str
    overrides: Dict[str, str]


@dataclass(frozen=True)
class ResolvedConfig:
    controller_name_contains: str
    poll_hz: int
    aliases: Dict[str, str] = field(default_factory=dict)
    base_overrides: Dict[str, str] = field(default_factory=dict)
    layers: List[ResolvedLayer] = field(default_factory=list)
    debug: bool = False


DEFAULT_CONFIG = {
    "controller_name_contains": "Vader 5",
    "poll_hz": 250,
    "aliases": {},
    "base_overrides": {},
    "layers": [],
    "debug": False,
}


def load_config(path: str | Path) -> ResolvedConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return resolve_config(data)


def resolve_config(data: dict) -> ResolvedConfig:
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)

    aliases = {
        normalize_name(key): normalize_name(value)
        for key, value in dict(merged.get("aliases", {})).items()
    }

    controller_name_contains = str(merged.get("controller_name_contains", "Vader 5")).strip()
    poll_hz = int(merged.get("poll_hz", 250))
    if poll_hz < 30 or poll_hz > 1000:
        raise ValueError("poll_hz must be between 30 and 1000")

    base_overrides = {
        canonical_source_button(source_name, aliases): canonical_output_button(target_name)
        for source_name, target_name in dict(merged.get("base_overrides", {})).items()
    }

    layers: list[ResolvedLayer] = []
    for index, raw_layer in enumerate(list(merged.get("layers", []))):
        if "when_held" not in raw_layer:
            raise ValueError(f"Layer #{index + 1} is missing 'when_held'")
        layer_name = str(raw_layer.get("name") or f"layer_{index + 1}")
        when_held = canonical_source_button(str(raw_layer["when_held"]), aliases)
        overrides = {
            canonical_source_button(source_name, aliases): canonical_output_button(target_name)
            for source_name, target_name in dict(raw_layer.get("overrides", {})).items()
        }
        layers.append(ResolvedLayer(name=layer_name, when_held=when_held, overrides=overrides))

    return ResolvedConfig(
        controller_name_contains=controller_name_contains,
        poll_hz=poll_hz,
        aliases=aliases,
        base_overrides=base_overrides,
        layers=layers,
        debug=bool(merged.get("debug", False)),
    )
