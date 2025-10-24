from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import test_ping.models as models
import test_ping.schemas as schemas
from test_ping.database import get_db, Base, engine
from pythonping import ping
import datetime
from test_ping.email_trigger import send_email_function
from test_ping.shutdown_label import get_shutdown_status
from test_ping.co_ordinator import get_district


Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/ping/", response_model=schemas.PingProbeResponse)
def create_ping_probe(host: str, db: Session = Depends(get_db)):
    count = 4
    timeout = 2
    response = ping(host, count=count, timeout=timeout)
    packets_sent = count
    packets_received = response.success()
    packet_loss = (packets_sent - packets_received) / packets_sent
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
    return db_probe

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

################################# TO COMMIT #############################

@app.post("/send-email")
def trigger_email(request: schemas.EmailTriggerRequest):
    try:
        send_email_function([request.to], request.subject, request.body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Email sent to {request.to}"}

@app.post("/ping/status/")
def compute_shutdown_status(probe: schemas.PingProbeBase):
    status = get_shutdown_status(probe)
    return {"host": probe.host, "shutdown_status": status}

# @app.post("/district/", response_model=schemas.CoordinateDistrictResponse)
# def find_district(lat: float, lon: float):
#     district = get_district(lat, lon)
#     if not district:
#         raise HTTPException(status_code=404, detail="District not found for the given coordinates")
#     return schemas.CoordinateDistrictResponse(latitude=lat, longitude=lon, district=district)

# @app.post("/district/")
# def find_district(payload: schemas.CoordinateDistrictResponse):
#     district = get_district(payload.latitude, payload.longitude)
#     print(district)
#     return schemas.CoordinateDistrictResponse(
#         latitude=payload.latitude,
#         longitude=payload.longitude,
#         district= district
#     )
    # return {"latitude": payload.latitude, "longitude": payload.longitude,"district": district}
@app.post("/district/")
def find_district(payload: schemas.CoordinateDistrictResponse):
    district = get_district(payload.latitude, payload.longitude)
    return {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "district": district
    }
