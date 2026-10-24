from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str = "demo"
    salary: str = "Not listed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
