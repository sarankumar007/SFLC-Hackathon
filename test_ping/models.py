from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from test_ping.database import Base
import datetime
from typing import Optional


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

    # Add these new columns to match your extended schemas.py and JSON structure
    signal_strength = Column(Integer, nullable=True)
    signal_quality = Column(String, nullable=True)
    network_type = Column(String, nullable=True)
    status = Column(String, nullable=True)

    # Add location and district info if storing these
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
