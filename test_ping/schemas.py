from pydantic import BaseModel, ConfigDict
from typing import Optional, List
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
    confirmed_shutdown: bool
    confirmed_shutdown_time: Optional[datetime] = None
    restored_time: Optional[datetime] = None
    duration: Optional[str] = None

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
