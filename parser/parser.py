# just example code from gemini abi

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class StateNode:
    name: str
    entry_action: Optional[str] = None
    exit_action: Optional[str] = None
    substates: List['StateNode'] = field(default_factory=list)
    # ... transitions etc.