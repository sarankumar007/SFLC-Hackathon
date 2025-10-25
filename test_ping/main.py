from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import test_ping.models as models
import test_ping.schemas as schemas
from test_ping.database import get_db, Base, engine
from pythonping import ping
import datetime

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_ping.main:app", host="127.0.0.1", port=8000, reload=True, workers=1)
