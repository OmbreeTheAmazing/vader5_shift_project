from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .state import InputState

SDL_INIT_GAMEPAD = 0x00002000
SDL_INIT_EVENTS = 0x00004000

BUTTON_ENUMS: Dict[str, int] = {
    "south": 0,
    "east": 1,
    "west": 2,
    "north": 3,
    "back": 4,
    "guide": 5,
    "start": 6,
    "left_stick": 7,
    "right_stick": 8,
    "left_shoulder": 9,
    "right_shoulder": 10,
    "dpad_up": 11,
    "dpad_down": 12,
    "dpad_left": 13,
    "dpad_right": 14,
    "misc1": 15,
    "right_paddle1": 16,
    "left_paddle1": 17,
    "right_paddle2": 18,
    "left_paddle2": 19,
    "touchpad": 20,
    "misc2": 21,
    "misc3": 22,
    "misc4": 23,
    "misc5": 24,
    "misc6": 25,
}

AXIS_ENUMS: Dict[str, int] = {
    "leftx": 0,
    "lefty": 1,
    "rightx": 2,
    "righty": 3,
    "left_trigger": 4,
    "right_trigger": 5,
}


class SDL3Error(RuntimeError):
    pass


@dataclass(frozen=True)
class GamepadInfo:
    instance_id: int
    name: str


class SDL3Runtime:
    def __init__(self, dll_path: str | None = None):
        self._dll = self._load_dll(dll_path)
        self._bind_functions()
        if hasattr(self._dll, "SDL_SetMainReady"):
            self._dll.SDL_SetMainReady()

        self._dll.SDL_SetHint(b"SDL_JOYSTICK_HIDAPI", b"1")
        self._dll.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")

        ok = self._dll.SDL_Init(SDL_INIT_GAMEPAD | SDL_INIT_EVENTS)
        if not ok:
            raise SDL3Error(f"SDL_Init failed: {self.error_text()}")
        self._closed = False

    @staticmethod
    def _candidate_dll_paths(explicit_path: str | None) -> List[str]:
        candidates: list[str] = []
        if explicit_path:
            candidates.append(explicit_path)
        env_path = os.environ.get("SDL3_PATH")
        if env_path:
            candidates.append(env_path)

        module_dir = Path(__file__).resolve().parent
        project_dir = module_dir.parent
        cwd = Path.cwd()
        executable_dir = Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else cwd

        for directory in [cwd, executable_dir, module_dir, project_dir]:
            candidates.append(str(directory / "SDL3.dll"))

        found = ctypes.util.find_library("SDL3")
        if found:
            candidates.append(found)

        candidates.extend(["SDL3.dll", "SDL3"])

        deduped: list[str] = []
        seen: set[str] = set()
        for entry in candidates:
            if entry not in seen:
                seen.add(entry)
                deduped.append(entry)
        return deduped

    def _load_dll(self, explicit_path: str | None) -> ctypes.CDLL:
        errors: list[str] = []
        for candidate in self._candidate_dll_paths(explicit_path):
            try:
                return ctypes.CDLL(candidate)
            except OSError as exc:
                errors.append(f"{candidate}: {exc}")
        joined = "\n".join(errors)
        raise SDL3Error(
            "Unable to load SDL3.dll. Put SDL3.dll next to the project, add it to PATH, or set SDL3_PATH.\n"
            f"Attempts:\n{joined}"
        )

    def _bind_functions(self) -> None:
        self._dll.SDL_GetError.argtypes = []
        self._dll.SDL_GetError.restype = ctypes.c_char_p

        self._dll.SDL_SetHint.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._dll.SDL_SetHint.restype = ctypes.c_bool

        self._dll.SDL_Init.argtypes = [ctypes.c_uint32]
        self._dll.SDL_Init.restype = ctypes.c_bool

        self._dll.SDL_Quit.argtypes = []
        self._dll.SDL_Quit.restype = None

        self._dll.SDL_PumpEvents.argtypes = []
        self._dll.SDL_PumpEvents.restype = None

        if hasattr(self._dll, "SDL_SetMainReady"):
            self._dll.SDL_SetMainReady.argtypes = []
            self._dll.SDL_SetMainReady.restype = None

        self._dll.SDL_free.argtypes = [ctypes.c_void_p]
        self._dll.SDL_free.restype = None

        self._dll.SDL_GetGamepads.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self._dll.SDL_GetGamepads.restype = ctypes.POINTER(ctypes.c_int32)

        self._dll.SDL_GetGamepadNameForID.argtypes = [ctypes.c_int32]
        self._dll.SDL_GetGamepadNameForID.restype = ctypes.c_char_p

        self._dll.SDL_OpenGamepad.argtypes = [ctypes.c_int32]
        self._dll.SDL_OpenGamepad.restype = ctypes.c_void_p

        self._dll.SDL_CloseGamepad.argtypes = [ctypes.c_void_p]
        self._dll.SDL_CloseGamepad.restype = None

        self._dll.SDL_GetGamepadName.argtypes = [ctypes.c_void_p]
        self._dll.SDL_GetGamepadName.restype = ctypes.c_char_p

        self._dll.SDL_GetGamepadMapping.argtypes = [ctypes.c_void_p]
        self._dll.SDL_GetGamepadMapping.restype = ctypes.c_void_p

        self._dll.SDL_GetGamepadButton.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._dll.SDL_GetGamepadButton.restype = ctypes.c_bool

        self._dll.SDL_GetGamepadAxis.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._dll.SDL_GetGamepadAxis.restype = ctypes.c_int16

        self._dll.SDL_GamepadHasButton.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._dll.SDL_GamepadHasButton.restype = ctypes.c_bool

        self._dll.SDL_GamepadHasAxis.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._dll.SDL_GamepadHasAxis.restype = ctypes.c_bool

    def error_text(self) -> str:
        message = self._dll.SDL_GetError()
        return message.decode("utf-8", errors="replace") if message else "Unknown SDL error"

    def list_gamepads(self) -> list[GamepadInfo]:
        count = ctypes.c_int(0)
        pointer = self._dll.SDL_GetGamepads(ctypes.byref(count))
        if not pointer:
            return []

        try:
            ids = [int(pointer[index]) for index in range(count.value)]
        finally:
            self._dll.SDL_free(ctypes.cast(pointer, ctypes.c_void_p))

        devices: list[GamepadInfo] = []
        for instance_id in ids:
            name_ptr = self._dll.SDL_GetGamepadNameForID(instance_id)
            if name_ptr:
                name = name_ptr.decode("utf-8", errors="replace")
            else:
                name = f"Unknown ({instance_id})"
            devices.append(GamepadInfo(instance_id=instance_id, name=name))
        return devices

    def open_matching(self, name_substring: str) -> "SDL3Gamepad":
        needle = name_substring.lower().strip()
        devices = self.list_gamepads()
        for device in devices:
            if not needle or needle in device.name.lower():
                return SDL3Gamepad(self, device.instance_id, device.name)
        available = ", ".join(device.name for device in devices) or "none"
        raise SDL3Error(
            f"No SDL gamepad matched '{name_substring}'. SDL saw: {available}"
        )

    def close(self) -> None:
        if not self._closed:
            self._dll.SDL_Quit()
            self._closed = True

    def __enter__(self) -> "SDL3Runtime":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class SDL3Gamepad:
    def __init__(self, runtime: SDL3Runtime, instance_id: int, initial_name: str):
        self.runtime = runtime
        self.instance_id = instance_id
        self._handle = runtime._dll.SDL_OpenGamepad(instance_id)
        if not self._handle:
            raise SDL3Error(f"SDL_OpenGamepad failed: {runtime.error_text()}")

        name_ptr = runtime._dll.SDL_GetGamepadName(self._handle)
        if name_ptr:
            self.name = name_ptr.decode("utf-8", errors="replace")
        else:
            self.name = initial_name
        self._closed = False

    def mapping_string(self) -> str | None:
        pointer = self.runtime._dll.SDL_GetGamepadMapping(self._handle)
        if not pointer:
            return None
        try:
            raw = ctypes.cast(pointer, ctypes.c_char_p).value
            return raw.decode("utf-8", errors="replace") if raw else None
        finally:
            self.runtime._dll.SDL_free(pointer)

    def available_buttons(self) -> list[str]:
        result: list[str] = []
        for name, enum_value in BUTTON_ENUMS.items():
            if self.runtime._dll.SDL_GamepadHasButton(self._handle, enum_value):
                result.append(name)
        return result

    def available_axes(self) -> list[str]:
        result: list[str] = []
        for name, enum_value in AXIS_ENUMS.items():
            if self.runtime._dll.SDL_GamepadHasAxis(self._handle, enum_value):
                result.append(name)
        return result

    def poll(self) -> InputState:
        self.runtime._dll.SDL_PumpEvents()

        buttons = {
            name
            for name, enum_value in BUTTON_ENUMS.items()
            if self.runtime._dll.SDL_GetGamepadButton(self._handle, enum_value)
        }
        axes = {
            name: _normalize_axis(name, self.runtime._dll.SDL_GetGamepadAxis(self._handle, enum_value))
            for name, enum_value in AXIS_ENUMS.items()
        }
        return InputState(buttons=buttons, axes=axes)

    def close(self) -> None:
        if not self._closed:
            self.runtime._dll.SDL_CloseGamepad(self._handle)
            self._closed = True

    def __enter__(self) -> "SDL3Gamepad":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _normalize_axis(name: str, raw_value: int) -> float:
    if name in {"left_trigger", "right_trigger"}:
        if raw_value <= 0:
            return 0.0
        return min(1.0, raw_value / 32767.0)

    if raw_value == 0:
        return 0.0
    if raw_value < 0:
        return max(-1.0, raw_value / 32768.0)
    return min(1.0, raw_value / 32767.0)
