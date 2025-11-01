from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime

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

    class Config:
        orm_mode = True

class PingProbeCreate(PingProbeBase):
    pass

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

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True
