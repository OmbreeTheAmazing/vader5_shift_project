from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable, Sequence

from .config import ResolvedConfig, load_config, resolve_config
from .layer_engine import LayerEngine
from .names import canonical_source_button
from .output import NullOutputPad, VirtualPadError, VirtualXboxPad
from .sdl3_input import SDL3Error, SDL3Runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vader-shift",
        description="Hold-based shift layers for the Flydigi Vader 5 Pro on Windows.",
    )
    parser.add_argument(
        "--sdl",
        default=None,
        help="Optional explicit path to SDL3.dll. You can also set SDL3_PATH.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List SDL-visible gamepads.")
    list_parser.set_defaults(func=command_list)

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Watch the controller and print which SDL buttons are currently pressed.",
    )
    monitor_parser.add_argument(
        "config",
        nargs="?",
        help="Optional JSON config file. Its aliases will be shown in monitor output.",
    )
    monitor_parser.add_argument(
        "--device-contains",
        default=None,
        help="Override controller_name_contains for the monitor session.",
    )
    monitor_parser.add_argument(
        "--show-axes",
        action="store_true",
        help="Also print analog axes above the threshold.",
    )
    monitor_parser.add_argument(
        "--axis-threshold",
        type=float,
        default=0.15,
        help="Only show axes whose absolute value is at least this much. Default: 0.15",
    )
    monitor_parser.add_argument(
        "--interval",
        type=float,
        default=0.02,
        help="Polling sleep for the monitor loop in seconds. Default: 0.02",
    )
    monitor_parser.set_defaults(func=command_monitor)

    run_parser = subparsers.add_parser(
        "run",
        help="Run the shift-layer engine and emit a virtual Xbox 360 controller.",
    )
    run_parser.add_argument("config", help="Path to the JSON config file.")
    run_parser.add_argument(
        "--device-contains",
        default=None,
        help="Override controller_name_contains from the config file.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do everything except creating the virtual gamepad. Useful for debugging.",
    )
    run_parser.set_defaults(func=command_run)

    return parser



def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except (SDL3Error, VirtualPadError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1



def command_list(args: argparse.Namespace) -> int:
    with SDL3Runtime(args.sdl) as runtime:
        devices = runtime.list_gamepads()
        if not devices:
            print("No SDL-recognized gamepads were detected.")
            return 1

        print("SDL gamepads:")
        for device in devices:
            print(f"  {device.instance_id}: {device.name}")
        return 0



def command_monitor(args: argparse.Namespace) -> int:
    config = load_config(args.config) if args.config else resolve_config({})
    needle = args.device_contains or config.controller_name_contains

    with SDL3Runtime(args.sdl) as runtime:
        with runtime.open_matching(needle) as gamepad:
            print(f"Monitoring: {gamepad.name}")
            available_buttons = ", ".join(gamepad.available_buttons()) or "(none)"
            available_axes = ", ".join(gamepad.available_axes()) or "(none)"
            print(f"Buttons SDL says are mapped: {available_buttons}")
            print(f"Axes SDL says are mapped: {available_axes}")
            mapping = gamepad.mapping_string()
            if mapping:
                print(f"SDL mapping: {mapping}")
            print("Press Ctrl+C to stop.")

            last_buttons: set[str] | None = None
            last_axes: dict[str, float] | None = None
            try:
                while True:
                    state = gamepad.poll()
                    filtered_axes = _filter_axes(state.axes, args.axis_threshold)
                    buttons_changed = last_buttons is None or state.buttons != last_buttons
                    axes_changed = args.show_axes and (last_axes is None or filtered_axes != last_axes)
                    if buttons_changed or axes_changed:
                        line = f"Buttons: {_format_buttons(state.buttons, config)}"
                        if args.show_axes:
                            line += f" | Axes: {_format_axes(filtered_axes)}"
                        print(line)
                        last_buttons = set(state.buttons)
                        last_axes = dict(filtered_axes)
                    time.sleep(max(0.0, float(args.interval)))
            except KeyboardInterrupt:
                print("\nStopped monitor.")
                return 0



def command_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    needle = args.device_contains or config.controller_name_contains
    engine = LayerEngine(config)

    with SDL3Runtime(args.sdl) as runtime:
        with runtime.open_matching(needle) as gamepad:
            output = NullOutputPad() if args.dry_run else VirtualXboxPad()
            try:
                print(f"Running with controller: {gamepad.name}")
                print(
                    "Mapped SDL buttons: "
                    + (", ".join(gamepad.available_buttons()) or "(none)")
                )
                mapping = gamepad.mapping_string()
                if mapping:
                    print(f"SDL mapping: {mapping}")
                if args.dry_run:
                    print("Dry run mode is enabled. No virtual gamepad will be created.")
                else:
                    print("Virtual Xbox 360 output is active. Press Ctrl+C to stop.")

                last_layers: tuple[str, ...] | None = None
                interval = 1.0 / float(config.poll_hz)
                next_tick = time.perf_counter()

                while True:
                    state = gamepad.poll()
                    transformed = engine.transform(state)
                    output.apply(transformed)

                    current_layers = tuple(transformed.active_layers)
                    if config.debug and current_layers != last_layers:
                        print(
                            "Active layers: "
                            + (", ".join(current_layers) if current_layers else "(none)")
                        )
                        last_layers = current_layers

                    next_tick += interval
                    remaining = next_tick - time.perf_counter()
                    if remaining > 0:
                        time.sleep(remaining)
                    else:
                        next_tick = time.perf_counter()
            except KeyboardInterrupt:
                print("\nStopped layer engine.")
                return 0
            finally:
                output.close()



def _filter_axes(axes: dict[str, float], threshold: float) -> dict[str, float]:
    return {
        name: value
        for name, value in axes.items()
        if abs(float(value)) >= float(threshold)
    }



def _format_axes(axes: dict[str, float]) -> str:
    if not axes:
        return "(none above threshold)"
    return ", ".join(f"{name}={value:+.3f}" for name, value in sorted(axes.items()))



def _format_buttons(buttons: Iterable[str], config: ResolvedConfig) -> str:
    sorted_buttons = sorted(buttons)
    if not sorted_buttons:
        return "(none)"

    rendered: list[str] = []
    for button_name in sorted_buttons:
        aliases = _config_aliases_for_button(button_name, config.aliases)
        if aliases:
            rendered.append(f"{button_name} [{' '.join(aliases)}]")
        else:
            rendered.append(button_name)
    return ", ".join(rendered)



def _config_aliases_for_button(button_name: str, aliases: dict[str, str]) -> list[str]:
    matches: list[str] = []
    for alias_name in sorted(aliases):
        try:
            if canonical_source_button(alias_name, aliases) == button_name:
                matches.append(alias_name)
        except ValueError:
            continue
    return matches
