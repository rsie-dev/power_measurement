from typing import Dict
import datetime

from pydantic import BaseModel


class CpuField(BaseModel):
    usage_guest: float
    usage_guest_nice: float
    usage_idle: float
    usage_iowait: float
    usage_irq: float
    usage_nice: float
    usage_softirq: float
    usage_steal: float
    usage_system: float
    usage_user: float


class MeasurementSingle(BaseModel):
    name: str
    tags: Dict[str, str]
    timestamp: datetime.datetime
    fields: CpuField
