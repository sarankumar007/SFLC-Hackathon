from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PingProbeBase(BaseModel):
    host: str
    packets_sent: int
    packets_received: int
    packet_loss: float
    rtt_min_ms: float
    rtt_max_ms: float
    rtt_avg_ms: float

class PingProbeCreate(PingProbeBase):
    pass

class PingProbeResponse(PingProbeBase):
    id: int
    host: str
    probe_time: datetime
    packets_sent: int
    packets_received: int
    packet_loss: float
    rtt_min_ms: float
    rtt_max_ms: float
    rtt_avg_ms: float
    confirmed_shutdown: bool
    confirmed_shutdown_time: Optional[datetime]
    restored_time: Optional[datetime]
    duration: Optional[str]

    class Config:
        orm_mode = True
