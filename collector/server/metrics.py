from typing import Dict, List, Union
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


class System(BaseModel):
    load1: float
    load5: float
    load15: float


class SystemMeasurement(BaseModel):
    name: str
    tags: Dict[str, str]
    timestamp: datetime.datetime
    fields: Union[CpuField, System]


class Metrics(BaseModel):
    metrics: List[SystemMeasurement]