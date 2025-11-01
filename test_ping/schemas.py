from pydantic import BaseModel, ConfigDict, Field, UUID4
from typing import Optional, List
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

class PingProbeResponse(BaseModel):
    id: UUID4
    probe_time: datetime

    confirmed_shutdown: bool
    confirmed_shutdown_time: Optional[datetime] = None
    restored_time: Optional[datetime] = None
    duration: Optional[str] = None

    signal_strength: Optional[int] = Field(default=None, alias='signalStrength')
    signal_quality: Optional[str] = Field(default=None, alias='signalQuality')
    network_type: Optional[str] = Field(default=None, alias='networkType')
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



# Nested models matching the Java API JSON
class PingResult(BaseModel):
    timestamp: int
    success: bool
    responseTime: Optional[float] = None
    target: str
    packetLoss: float
    jitter: Optional[float] = None
    minResponseTime: Optional[float] = None
    maxResponseTime: Optional[float] = None
    avgResponseTime: Optional[float] = None
    totalPacketsSent: int
    totalPacketsReceived: int

class DeviceInfo(BaseModel):
    androidVersion: str
    deviceModel: str
    carrier: str
    signalStrength: int
    batteryLevel: Optional[int] = None

class PingReport(BaseModel):
    id: str  # UUID string
    timestamp: int
    district: str
    state: str
    latitude: float
    longitude: float
    networkType: str
    isConfirmed: bool
    userConfirmed: Optional[bool] = None
    status: str
    signalQuality: str
    pingResults: List[PingResult]
    deviceInfo: DeviceInfo

    model_config = ConfigDict(from_attributes=True)


# class PingProbeResponse(PingProbeBase):
#     id: int
#     probe_time: datetime

#     class Config:
#         orm_mode = True

class EmailTriggerRequest(BaseModel):
    to: str
    subject: str
    body: str


# Pydantic schema for response
class CoordinateDistrictResponse(BaseModel):
    latitude: float
    longitude: float
    district: str


class AnalyzeQueryResponse(BaseModel):
    query: str
    analysis: Optional[str] = None
    database_summary: Optional[str] = None
    internet_context: Optional[str] = None
    final_summary: Optional[str] = None
    retrieved_records: Optional[List[dict]] = None
