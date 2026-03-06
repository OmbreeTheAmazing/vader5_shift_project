from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class InputState:
    buttons: Set[str] = field(default_factory=set)
    axes: Dict[str, float] = field(default_factory=dict)

    def copy(self) -> "InputState":
        return InputState(buttons=set(self.buttons), axes=dict(self.axes))


@dataclass
class OutputState:
    buttons: Set[str] = field(default_factory=set)
    axes: Dict[str, float] = field(default_factory=dict)
    active_layers: List[str] = field(default_factory=list)

    def copy(self) -> "OutputState":
        return OutputState(
            buttons=set(self.buttons),
            axes=dict(self.axes),
            active_layers=list(self.active_layers),
        )
