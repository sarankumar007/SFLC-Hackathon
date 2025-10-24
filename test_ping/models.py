from sqlalchemy import Column, Integer, String, Float, DateTime
from test_ping.database import Base
import datetime

class PingProbe(Base):
    __tablename__ = "ping_probes"

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String, index=True)
    probe_time = Column(DateTime, default=datetime.datetime.utcnow)
    packets_sent = Column(Integer)
    packets_received = Column(Integer)
    packet_loss = Column(Float)
    rtt_min_ms = Column(Float)
    rtt_max_ms = Column(Float)
    rtt_avg_ms = Column(Float)
