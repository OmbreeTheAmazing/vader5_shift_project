# Vader5 Shift

A small Windows utility that gives the Flydigi Vader 5 Pro hold-based shift layers.

The project reads the physical controller through SDL3, applies a software layer engine,
and outputs a virtual Xbox 360 controller through `vgamepad`.

This is meant for cases where the controller works in Flydigi Space Station, but normal
remap tools still cannot build the kind of hold-based layer behavior you want.

## What it does

Example behavior:

- Default layer:
  - M1 -> X
  - M2 -> B
  - M3 -> Y
  - M4 -> A
- While holding LB:
  - LB still goes through to the game
  - M1 -> D-pad Up
  - M2 -> D-pad Down
  - M3 -> D-pad Right
  - M4 -> D-pad Left

The config format is generic enough for more layers and other button mappings.

## Why this architecture

The project uses three pieces:

1. **SDL3 input**
   - Reads the physical controller.
   - Lets you inspect which extra buttons are exposed as paddles or misc buttons.
2. **Layer engine**
   - Applies base mappings plus hold-based layer overrides.
3. **Virtual Xbox output**
   - Emits a standard virtual Xbox 360 pad through `vgamepad`.

That avoids needing native D-input support on the controller.

## Status

This repository is a practical prototype, not a finished commercial app.

Current scope:

- Windows only
- Command-line interface only
- Shift layers for digital buttons
- Analog passthrough for sticks and triggers
- No raw HID fallback backend yet
- No tray UI yet
- No automatic hotplug recovery yet

## Project layout

- `vader_shift/sdl3_input.py`
  - SDL3 loading and gamepad polling
- `vader_shift/layer_engine.py`
  - Hold-layer logic
- `vader_shift/output.py`
  - Virtual Xbox 360 output through `vgamepad`
- `sample-configs/lb_dpad_layer.json`
  - Example config similar to your requested layout
- `tests/test_layer_engine.py`
  - Unit tests for the layer logic

## Requirements

- Windows 10 or 11
- Python 3.10+
- SDL3 runtime DLL
- `vgamepad`
- ViGEmBus driver (installed automatically by `vgamepad` on Windows)
- Optional but strongly recommended: HidHide to avoid double input in games

## Installation

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Install SDL3 runtime

Get a recent SDL3 runtime and place `SDL3.dll` in one of these places:

- next to the project root
- next to the Python entry point
- anywhere on `PATH`
- or set `SDL3_PATH` to the full DLL path

Example:

```powershell
$env:SDL3_PATH = "C:\tools\SDL3\SDL3.dll"
```

### 3. Optional: configure HidHide

If a game sees both the physical Vader 5 and the virtual Xbox pad, you will get double input.

HidHide is the normal fix:

- hide the physical controller from games
- whitelist your Python interpreter or packaged executable so this utility can still read it

### 4. Space Station recommendation

Use a clean Space Station profile while testing.

Recommended starting point:

- avoid keyboard macro output from the extra buttons
- avoid profile auto-switch tricks
- keep the controller in a simple controller-output mode

The monitor command below will tell you what SDL can actually see.

## Quick start

### List gamepads detected by SDL

```powershell
python -m vader_shift list
```

### Monitor button names

This is the first thing to run, because it tells you how SDL names the Vader 5's extra buttons on your machine.

```powershell
python -m vader_shift monitor sample-configs/lb_dpad_layer.json --show-axes
```

Press each extra button one at a time and note the printed SDL button name.

The sample config assumes:

- `m1` -> `right_paddle1`
- `m2` -> `right_paddle2`
- `m3` -> `left_paddle1`
- `m4` -> `left_paddle2`

If your controller reports a different order, edit the aliases in the JSON.

### Run the layer engine

```powershell
python -m vader_shift run sample-configs/lb_dpad_layer.json
```

Stop with `Ctrl+C`.

## Config format

Example:

```json
{
  "controller_name_contains": "Vader 5",
  "poll_hz": 250,
  "aliases": {
    "lb": "left_shoulder",
    "m1": "right_paddle1",
    "m2": "right_paddle2",
    "m3": "left_paddle1",
    "m4": "left_paddle2"
  },
  "base_overrides": {
    "m1": "x",
    "m2": "b",
    "m3": "y",
    "m4": "a"
  },
  "layers": [
    {
      "name": "lb_dpad",
      "when_held": "lb",
      "overrides": {
        "m1": "dpad_up",
        "m2": "dpad_down",
        "m3": "dpad_right",
        "m4": "dpad_left"
      }
    }
  ]
}
```

### Notes

- `aliases` lets you create friendly names like `m1`, `m2`, `lb`, and `rb`.
- `base_overrides` changes the default behavior of a pressed source button.
- `layers` are activated while `when_held` is pressed.
- The modifier itself still passes through unless you explicitly remap it.
- Layer priority is top-to-bottom in the file. The first active layer that remaps a source button wins.

## Supported canonical source button names

Standard buttons:

- `south`, `east`, `west`, `north`
- `back`, `guide`, `start`
- `left_stick`, `right_stick`
- `left_shoulder`, `right_shoulder`
- `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right`

Extra SDL buttons:

- `misc1`
- `right_paddle1`, `left_paddle1`, `right_paddle2`, `left_paddle2`
- `touchpad`
- `misc2`, `misc3`, `misc4`, `misc5`, `misc6`

Useful built-in aliases:

- `a`, `b`, `x`, `y`
- `lb` / `l1`
- `rb` / `r1`
- `ls` / `l3`
- `rs` / `r3`
- `up`, `down`, `left`, `right`

## Supported output buttons

- `a`, `b`, `x`, `y`
- `back`, `guide`, `start`
- `left_stick`, `right_stick`
- `left_shoulder`, `right_shoulder`
- `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right`
- `none`

`none` disables output for that source button.

## Development

### Run tests

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Dry-run mode

Useful when checking the logic without creating a virtual controller:

```powershell
python -m vader_shift run sample-configs/lb_dpad_layer.json --dry-run
```

## Troubleshooting

### SDL3.dll not found

Use one of these:

```powershell
$env:SDL3_PATH = "C:\full\path\to\SDL3.dll"
python -m vader_shift list
```

### No controller found

Run:

```powershell
python -m vader_shift list
```

If the Vader 5 does not appear there, SDL is not recognizing it as a gamepad with your current runtime or current controller mode.

### Wrong extra-button order

Run monitor mode and press each extra button one by one. Then update the aliases in your JSON.

### Double input in games

Use HidHide so the game only sees the virtual Xbox controller, not the physical Vader 5.

## Next good upgrades

- raw HID fallback backend for cases where SDL misses a button
- simple GUI or tray app
- profile switching in-app
- import/export preset library
- packaged `.exe` build with bundled SDL3 runtime
