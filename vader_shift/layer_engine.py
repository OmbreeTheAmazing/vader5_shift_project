from __future__ import annotations

from .config import ResolvedConfig, ResolvedLayer
from .names import DEFAULT_SOURCE_TO_OUTPUT
from .state import InputState, OutputState


class LayerEngine:
    def __init__(self, config: ResolvedConfig):
        self.config = config

    def active_layers(self, state: InputState) -> list[ResolvedLayer]:
        return [layer for layer in self.config.layers if layer.when_held in state.buttons]

    def map_button(self, button_name: str, active_layers: list[ResolvedLayer]) -> str | None:
        for layer in active_layers:
            if button_name in layer.overrides:
                target = layer.overrides[button_name]
                return None if target == "none" else target

        if button_name in self.config.base_overrides:
            target = self.config.base_overrides[button_name]
            return None if target == "none" else target

        target = DEFAULT_SOURCE_TO_OUTPUT.get(button_name)
        return None if target in (None, "none") else target

    def transform(self, state: InputState) -> OutputState:
        active_layers = self.active_layers(state)
        output_buttons: set[str] = set()

        for button_name in state.buttons:
            target = self.map_button(button_name, active_layers)
            if target:
                output_buttons.add(target)

        return OutputState(
            buttons=output_buttons,
            axes=dict(state.axes),
            active_layers=[layer.name for layer in active_layers],
        )
