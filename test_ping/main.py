from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import test_ping.models as models
import test_ping.schemas as schemas
from test_ping.database import get_db, Base, engine
from pythonping import ping
import datetime
from pydantic import BaseModel
import logging

Base.metadata.create_all(bind=engine)

app = FastAPI()

class PingRequest(BaseModel):
    host: str

@app.post("/ping/", response_model=schemas.PingProbeResponse)
def create_ping_probe(ping_request: PingRequest, db: Session = Depends(get_db)):
    host = ping_request.host
    count = 4
    timeout = 2

    try:
        response = ping(host, count=count, timeout=timeout)
        packets_sent = count
        packets_received = sum(1 for r in response._responses if r.success)
        packet_loss = (packets_sent - packets_received) / float(packets_sent)
        rtt_min = response.rtt_min_ms
        rtt_max = response.rtt_max_ms
        rtt_avg = response.rtt_avg_ms
        probe_time = datetime.datetime.utcnow()

        db_probe = models.PingProbe(
            host=host,
            probe_time=probe_time,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss=packet_loss,
            rtt_min_ms=rtt_min,
            rtt_max_ms=rtt_max,
            rtt_avg_ms=rtt_avg
        )
        db.add(db_probe)
        db.commit()
        db.refresh(db_probe)
        return _with_duration(db_probe)

    except Exception as e:
        logging.error(f"Ping error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ping error: {str(e)}")

@app.post("/ping_report/", response_model=schemas.PingReport)
def receive_ping_report(report: schemas.PingReport, db: Session = Depends(get_db)):
    if report.pingResults:
        first_result = report.pingResults[0]

        db_probe = models.PingProbe(
            host=first_result.target,
            probe_time=datetime.datetime.utcfromtimestamp(report.timestamp / 1000),
            packets_sent=first_result.totalPacketsSent,
            packets_received=first_result.totalPacketsReceived,
            packet_loss=first_result.packetLoss,
            rtt_min_ms=first_result.minResponseTime or 0.0,
            rtt_max_ms=first_result.maxResponseTime or 0.0,
            rtt_avg_ms=first_result.avgResponseTime or 0.0,
            confirmed_shutdown=report.isConfirmed,
            confirmed_shutdown_time=None,
            restored_time=None
        )
        db.add(db_probe)
        db.commit()
        db.refresh(db_probe)

    return report

@app.get("/ping/", response_model=List[schemas.PingProbeResponse])
def get_ping_probes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.PingProbe).offset(skip).limit(limit).all()

@app.get("/ping/{probe_id}", response_model=schemas.PingProbeResponse)
def get_ping_probe(probe_id: int, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    return probe

@app.put("/ping/{probe_id}", response_model=schemas.PingProbeResponse)
def update_ping_probe(probe_id: int, probe_update: schemas.PingProbeCreate, db: Session = Depends(get_db)):
    db_probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not db_probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    for key, value in probe_update.dict().items():
        setattr(db_probe, key, value)
    db.commit()
    db.refresh(db_probe)
    return db_probe

@app.delete("/ping/{probe_id}")
def delete_ping_probe(probe_id: int, db: Session = Depends(get_db)):
    db_probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not db_probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    db.delete(db_probe)
    db.commit()
    return {"detail": "Probe deleted"}

@app.patch("/ping/{probe_id}/confirm", response_model=schemas.PingProbeResponse)
def confirm_shutdown(probe_id: int, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    probe.confirmed_shutdown = True
    probe.confirmed_shutdown_time = datetime.datetime.utcnow()
    db.commit()
    db.refresh(probe)
    return _with_duration(probe)

@app.patch("/ping/{probe_id}/restore", response_model=schemas.PingProbeResponse)
def mark_internet_restored(probe_id: int, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    probe.confirmed_shutdown = False
    probe.restored_time = datetime.datetime.utcnow()
    db.commit()
    db.refresh(probe)
    return _with_duration(probe)

@app.get("/ping/confirmed", response_model=List[schemas.PingProbeResponse])
def get_confirmed_shutdowns(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    probes = db.query(models.PingProbe).filter(models.PingProbe.confirmed_shutdown == True).offset(skip).limit(limit).all()
    return [_with_duration(p) for p in probes]

def _with_duration(probe: models.PingProbe) -> schemas.PingProbeResponse:
    duration = None
    if probe.confirmed_shutdown_time and probe.restored_time:
        diff = probe.restored_time - probe.confirmed_shutdown_time
        duration = str(diff)  
    schema_obj = schemas.PingProbeResponse.from_orm(probe)
    schema_obj.duration = duration
    return schema_obj

