from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from test_ping.database import Base
import datetime
from sqlalchemy.orm import relationship

class PingProbe(Base):
    __tablename__ = "ping_probes"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    host = Column(String, index=True)
    probe_time = Column(DateTime, default=datetime.datetime.utcnow)
    packets_sent = Column(Integer)
    packets_received = Column(Integer)
    packet_loss = Column(Float)
    rtt_min_ms = Column(Float)
    rtt_max_ms = Column(Float)
    rtt_avg_ms = Column(Float)

    confirmed_shutdown = Column(Boolean, default=False)
    confirmed_shutdown_time = Column(DateTime, nullable=True)
    restored_time = Column(DateTime, nullable=True)

    signal_strength = Column(Integer, nullable=True)
    signal_quality = Column(String, nullable=True)
    network_type = Column(String, nullable=True)
    status = Column(String, nullable=True)

    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    ping_results = relationship("PingResult", back_populates="probe", cascade="all, delete")


class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True)
    probe_id = Column(UUID(as_uuid=True), ForeignKey("ping_probes.id", ondelete="CASCADE"), nullable=False)

    timestamp = Column(Integer)
    success = Column(Boolean)
    response_time = Column(Float, nullable=True)
    target = Column(String)
    packet_loss = Column(Float)
    jitter = Column(Float, nullable=True)
    min_response_time = Column(Float, nullable=True)
    max_response_time = Column(Float, nullable=True)
    avg_response_time = Column(Float, nullable=True)
    total_packets_sent = Column(Integer)
    total_packets_received = Column(Integer)

    probe = relationship("PingProbe", back_populates="ping_results")

