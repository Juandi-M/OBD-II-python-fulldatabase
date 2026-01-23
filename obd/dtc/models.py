from dataclasses import dataclass


@dataclass(frozen=True)
class DTCInfo:
    code: str
    description: str
    source: str = ""
