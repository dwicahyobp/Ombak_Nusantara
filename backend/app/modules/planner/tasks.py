from datetime import datetime
from sqlmodel import Session

from backend.app.worker import celery_app
from backend.app.models.engine import engine
from backend.app.models.database import ResearchJob
from backend.app.modules.planner.services import generate_queries, search_internet, synthesize_answer

def _update_job(job_id: int, **kwargs):
    """Helper: update field ResearchJob di DB."""
    with Session(engine) as db:
        job = db.get(ResearchJob, job_id)
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            db.add(job)
            db.commit()

@celery_app.task
def start_process_research(surf_data: dict):
    spot = surf_data.get("target_spot")
    skill = surf_data.get("skill_level")
    date = surf_data.get("date")
    job_id = surf_data.get("job_id")
    
    print(f"Memproses riset Ombak Nusantara untuk spot: {spot} ({skill}) pada tanggal {date}")

    advanced_spots = ["uluwatu", "padang padang", "padang-padang"]
    
    if skill.lower() == "beginner" and spot.lower() in advanced_spots:
        print(f"⚠️ Safety Guardrail Terpicu: Peselancar {skill} dilarang ke {spot}!")
        
        import json
        warning_report_dict = {
            "status": "NO-GO",
            "safety_alert": f"⚠️ SAFETY GUARDRAIL TRIGGERED: {spot} is known for shallow, sharp reef breaks and strong currents. Highly hazardous for a {skill} surfer.",
            "live_marine_data": [
                "🌊 **Wave:** Extreme / Unsafe for current skill level",
                "🪸 **Bottom:** Shallow Sharp Reef",
                "⚠️ **Risk Level:** Severe"
            ],
            "trip_plan": [
                "**🛑 ACTION BLOCKED:**<br>Session cancelled by OmbakNusantara Safety Protocol.",
                "**🏄‍♂️ ALTERNATIVE 1:**<br>Please redirect your trip to **Kuta Beach** (Very safe for learning, sandy bottom).",
                "**🏄‍♂️ ALTERNATIVE 2:**<br>Please redirect your trip to **Batu Bolong, Canggu** (Slower, softer waves)."
            ],
            "local_logistics": [
                "🚫 **Transport:** Not Applicable (Trip Cancelled)"
            ],
            "gear_hazards": [
                "⚠️ **Critical Hazard:** Reef cuts, strong rip currents, hold-downs.",
                "🚑 **Safety Advice:** Do not paddle out here."
            ],
            "hotel_recommendations": [
                "ℹ️ **Info:** Please book accommodation near Kuta or Canggu instead for safer surfing conditions."
            ]
        }
        warning_report = json.dumps(warning_report_dict)
        with open("surf_report.md", "w") as file:
            file.write(warning_report)
        
        if job_id:
            _update_job(
                job_id,
                status="Rejected",
                result_md=warning_report,
                completed_at=datetime.utcnow(),
            )
        return f"Job dihentikan demi keselamatan: Peselancar {skill} dilarang ke {spot}."

    try:
        print("Generating queries for surf conditions...")
        preferred_time = surf_data.get("preferred_time", "Morning")
        topic_context = f"Current wave conditions, swell, tide, and wind at {spot} Indonesia on {date} for a {skill} surfer (Preferred Time: {preferred_time})."
        queries = generate_queries(topic_context)

        full_results_content = ""

        for query in queries:
            print("Searching internet for:", query)
            result = search_internet(query)
            if result is not None:
                full_results_content += result

        print("Fetching Open-Meteo satellite data...")
        from backend.app.modules.planner.services import get_open_meteo_marine_data
        marine_data = get_open_meteo_marine_data(spot, surf_data.get("region", ""), date)
        full_results_content += marine_data

        print("Synthesizing surf report answer...")
        raw_report = synthesize_answer(topic_context, full_results_content)
        if raw_report is None:
            raise ValueError("Failed to synthesize surf report")

        print("Saving surf report...")
        with open("surf_report.md", "w") as file:
            file.write(raw_report)

        # ✅ Simpan hasil ke DB
        if job_id:
            _update_job(
                job_id,
                status="Completed",
                result_md=raw_report,
                completed_at=datetime.utcnow(),
            )
        return "Surf research job successfully completed!"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Research task failed: {error_msg}")
        if job_id:
            _update_job(
                job_id,
                status="Failed",
                error_message=error_msg,
                completed_at=datetime.utcnow(),
            )
        raise