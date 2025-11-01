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
from test_ping.email_trigger import send_email_function
from test_ping.shutdown_label import get_shutdown_status
from test_ping.co_ordinator import get_district
from uuid import UUID
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
    db_probe = models.PingProbe(
        host=report.pingResults[0].target if report.pingResults else None,
        probe_time=datetime.datetime.utcfromtimestamp(report.timestamp / 1000),
        confirmed_shutdown=report.isConfirmed,
        signal_strength=report.deviceInfo.signalStrength,
        signal_quality=report.signalQuality,
        network_type=report.networkType,
        status=report.status,
        district=report.district,
        state=report.state,
        latitude=report.latitude,
        longitude=report.longitude
    )
    db.add(db_probe)
    db.commit()
    db.refresh(db_probe)

    for result in report.pingResults:
        db_result = models.PingResult(
            probe_id=db_probe.id,
            timestamp=result.timestamp,
            success=result.success,
            response_time=result.responseTime,
            target=result.target,
            packet_loss=result.packetLoss,
            jitter=result.jitter,
            min_response_time=result.minResponseTime,
            max_response_time=result.maxResponseTime,
            avg_response_time=result.avgResponseTime,
            total_packets_sent=result.totalPacketsSent,
            total_packets_received=result.totalPacketsReceived
        )
        db.add(db_result)
    db.commit()

    return report

@app.get("/ping/", response_model=List[schemas.PingProbeResponse])
def get_ping_probes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.PingProbe).offset(skip).limit(limit).all()

@app.get("/ping/{probe_id}", response_model=schemas.PingProbeResponse)
def get_ping_probe(probe_id: UUID, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    return probe

@app.put("/ping/{probe_id}", response_model=schemas.PingProbeResponse)
def update_ping_probe(probe_id: UUID, probe_update: schemas.PingProbeCreate, db: Session = Depends(get_db)):
    db_probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not db_probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    for key, value in probe_update.dict().items():
        setattr(db_probe, key, value)
    db.commit()
    db.refresh(db_probe)
    return db_probe

@app.delete("/ping/{probe_id}")
def delete_ping_probe(probe_id: UUID, db: Session = Depends(get_db)):
    db_probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not db_probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    db.delete(db_probe)
    db.commit()
    return {"detail": "Probe deleted"}

@app.patch("/ping/{probe_id}/confirm", response_model=schemas.PingProbeResponse)
def confirm_shutdown(probe_id: UUID, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    probe.confirmed_shutdown = True
    probe.confirmed_shutdown_time = datetime.datetime.utcnow()
    db.commit()
    db.refresh(probe)
    return _with_duration(probe)

@app.patch("/ping/{probe_id}/restore", response_model=schemas.PingProbeResponse)
def mark_internet_restored(probe_id: UUID, db: Session = Depends(get_db)):
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

@app.post("/send-email")
def trigger_email(request: schemas.EmailTriggerRequest):
    try:
        send_email_function([request.to], request.subject, request.body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Email sent to {request.to}"}

# @app.post("/ping/status/")
# def compute_shutdown_status(probe: schemas.PingProbeBase):
#     status = get_shutdown_status(probe)
#     return {"host": probe.host, "shutdown_status": status}

# @app.post("/district/")
# def find_district(payload: schemas.CoordinateDistrictResponse):
#     district = get_district(payload.latitude, payload.longitude)
#     return {
#         "latitude": payload.latitude,
#         "longitude": payload.longitude,
#         "district": district
#     }

@app.patch("/ping/{probe_id}/status", response_model=schemas.PingProbeResponse)
def compute_and_update_shutdown_status(probe_id: UUID, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")

    status = get_shutdown_status(probe)

    if status == "confirmed":
        probe.confirmed_shutdown = True
        probe.confirmed_shutdown_time = datetime.datetime.utcnow()
    elif status in ("not confirmed", "suspected"):
        probe.confirmed_shutdown = False
        probe.restored_time = datetime.datetime.utcnow()

    db.commit()
    db.refresh(probe)

    return _with_duration(probe)

@app.patch("/district/{probe_id}", response_model=schemas.CoordinateDistrictResponse)
def update_probe_district(probe_id: UUID, db: Session = Depends(get_db)):
    probe = db.query(models.PingProbe).filter(models.PingProbe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")

    if probe.latitude is None or probe.longitude is None:
        raise HTTPException(status_code=400, detail="Probe does not have coordinates")

    district = get_district(probe.latitude, probe.longitude)

    if not district:
        raise HTTPException(status_code=404, detail="District not found for given coordinates")

    probe.district = district
    db.commit()
    db.refresh(probe)

    return schemas.CoordinateDistrictResponse(
        latitude=probe.latitude,
        longitude=probe.longitude,
        district=probe.district
    )
