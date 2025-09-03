from typing import Any, NamedTuple


class OptionElement(NamedTuple):
    name: str
    option_type: type
    default: Any
    description: str
