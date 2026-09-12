from dataclasses import dataclass, field
from typing import Any


@dataclass
class Offer:
    source: str
    external_id: str
    asset: str
    apr: float
    status: str
    product_type: str = "staking"
    duration_days: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)
