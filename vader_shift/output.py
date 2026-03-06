from __future__ import annotations

from typing import Dict

from .state import OutputState


class VirtualPadError(RuntimeError):
    pass


class VirtualXboxPad:
    def __init__(self):
        try:
            import vgamepad as vg
        except ImportError as exc:
            raise VirtualPadError(
                "vgamepad is not installed. Run 'pip install -r requirements.txt'."
            ) from exc

        self._vg = vg
        self._pad = vg.VX360Gamepad()
        self._last_buttons: set[str] = set()
        self._last_axes: Dict[str, float] = {
            "leftx": 0.0,
            "lefty": 0.0,
            "rightx": 0.0,
            "righty": 0.0,
            "left_trigger": 0.0,
            "right_trigger": 0.0,
        }

        self._button_map = {
            "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "left_stick": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "right_stick": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "left_shoulder": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "right_shoulder": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "dpad_up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            "dpad_down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            "dpad_left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            "dpad_right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }

    def apply(self, state: OutputState) -> bool:
        if not self._changed(state):
            return False

        buttons_to_release = self._last_buttons - state.buttons
        buttons_to_press = state.buttons - self._last_buttons

        for button_name in sorted(buttons_to_release):
            self._pad.release_button(button=self._button_map[button_name])

        for button_name in sorted(buttons_to_press):
            self._pad.press_button(button=self._button_map[button_name])

        self._pad.left_trigger_float(value_float=_clamp01(state.axes.get("left_trigger", 0.0)))
        self._pad.right_trigger_float(value_float=_clamp01(state.axes.get("right_trigger", 0.0)))
        self._pad.left_joystick_float(
            x_value_float=_clamp11(state.axes.get("leftx", 0.0)),
            y_value_float=_clamp11(state.axes.get("lefty", 0.0)),
        )
        self._pad.right_joystick_float(
            x_value_float=_clamp11(state.axes.get("rightx", 0.0)),
            y_value_float=_clamp11(state.axes.get("righty", 0.0)),
        )
        self._pad.update()

        self._last_buttons = set(state.buttons)
        for axis_name in self._last_axes:
            self._last_axes[axis_name] = float(state.axes.get(axis_name, 0.0))
        return True

    def close(self) -> None:
        self._pad.reset()
        self._pad.update()

    def _changed(self, state: OutputState) -> bool:
        if state.buttons != self._last_buttons:
            return True
        for axis_name, old_value in self._last_axes.items():
            new_value = float(state.axes.get(axis_name, 0.0))
            if abs(new_value - old_value) > 1e-5:
                return True
        return False


class NullOutputPad:
    def apply(self, state: OutputState) -> bool:
        return True

    def close(self) -> None:
        return None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))



def _clamp11(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))
