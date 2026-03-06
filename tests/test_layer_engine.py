from __future__ import annotations

import unittest

from vader_shift.config import resolve_config
from vader_shift.layer_engine import LayerEngine
from vader_shift.state import InputState


class LayerEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = resolve_config(
            {
                "aliases": {
                    "lb": "left_shoulder",
                    "m1": "right_paddle1",
                    "m2": "right_paddle2",
                    "m3": "left_paddle1",
                    "m4": "left_paddle2",
                },
                "base_overrides": {
                    "m1": "x",
                    "m2": "b",
                    "m3": "y",
                    "m4": "a",
                },
                "layers": [
                    {
                        "name": "lb_dpad",
                        "when_held": "lb",
                        "overrides": {
                            "m1": "dpad_up",
                            "m2": "dpad_down",
                            "m3": "dpad_right",
                            "m4": "dpad_left",
                        },
                    }
                ],
            }
        )
        self.engine = LayerEngine(self.config)

    def test_base_override_without_modifier(self) -> None:
        state = InputState(buttons={"right_paddle1"}, axes={})
        output = self.engine.transform(state)
        self.assertEqual(output.buttons, {"x"})
        self.assertEqual(output.active_layers, [])

    def test_layer_override_replaces_base_output(self) -> None:
        state = InputState(
            buttons={"left_shoulder", "right_paddle1", "right_paddle2"},
            axes={},
        )
        output = self.engine.transform(state)
        self.assertEqual(output.buttons, {"left_shoulder", "dpad_up", "dpad_down"})

    def test_unmapped_extra_button_is_silent(self) -> None:
        state = InputState(buttons={"misc4"}, axes={})
        output = self.engine.transform(state)
        self.assertEqual(output.buttons, set())

    def test_multiple_sources_can_target_same_virtual_button(self) -> None:
        config = resolve_config(
            {
                "aliases": {"m1": "right_paddle1"},
                "base_overrides": {"m1": "a"},
            }
        )
        engine = LayerEngine(config)
        state = InputState(buttons={"south", "right_paddle1"}, axes={})
        output = engine.transform(state)
        self.assertEqual(output.buttons, {"a"})

    def test_axes_are_passed_through(self) -> None:
        state = InputState(buttons=set(), axes={"leftx": 0.5, "right_trigger": 1.0})
        output = self.engine.transform(state)
        self.assertEqual(output.axes, {"leftx": 0.5, "right_trigger": 1.0})


if __name__ == "__main__":
    unittest.main()
