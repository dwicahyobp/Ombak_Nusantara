from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.models.engine import get_session
from backend.app.models.database import ResearchJob
from backend.app.modules.planner.schema import CreateSurfingPlan
from backend.app.modules.planner.tasks import start_process_research

planner_router = APIRouter(tags=["Surf Planner Tasks"])

@planner_router.post("/", status_code=status.HTTP_202_ACCEPTED)
def create_research(payload: CreateSurfingPlan, db: Session = Depends(get_session)):

    job = ResearchJob(
        target_spot=payload.target_spot,
        skill_level=payload.skill_level,
        date=payload.date,
        region=payload.region,
        preferred_time=payload.preferred_time or "Sore",
    )
    db.add(job)
    db.commit()
    db.refresh(job)


    data = payload.model_dump(mode='json')
    data["job_id"] = job.id
    start_process_research.delay(data)
    
    return {
        "message": "Ombak Nusantara surf research job in-process!",
        "job_id": job.id,
        "status": job.status,
    }

@planner_router.get("/{job_id}", status_code=status.HTTP_200_OK)
def get_research_result(job_id: int, db: Session = Depends(get_session)):
    job = db.get(ResearchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research job {job_id} not found.")
    return job

@planner_router.get("/", status_code=status.HTTP_200_OK)
def get_all_research_jobs(db: Session = Depends(get_session)):
    statement = select(ResearchJob).order_by(ResearchJob.id.desc())
    jobs = db.exec(statement).all()
    return jobs