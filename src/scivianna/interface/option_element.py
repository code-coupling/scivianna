from typing import Any, List
from dataclasses import dataclass

@dataclass
class OptionElement:
    name: str
    default: Any
    description: str

class FloatOption(OptionElement):
    pass

class BoolOption(OptionElement):
    pass

class IntOption(OptionElement):
    pass

class StringOption(OptionElement):
    pass

@dataclass
class SelectOption(OptionElement):
    options:List[str]
