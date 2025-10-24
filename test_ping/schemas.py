from pydantic import BaseModel
from datetime import datetime

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
    probe_time: datetime

    class Config:
        orm_mode = True

class EmailTriggerRequest(BaseModel):
    to: str
    subject: str
    body: str



# Pydantic schema for response
class CoordinateDistrictResponse(BaseModel):
    latitude: float
    longitude: float
