import json
from sqlmodel import Session
from celery.utils.log import get_task_logger

from backend.app.worker import celery_app
from backend.app.models.engine import engine
from backend.app.models.database import Post
from backend.app.modules.surf.agents import surf_report_subagent

logger = get_task_logger(__name__)

@celery_app.task
def fetch_weather_for_post(post_id: int):
    """
    Tugas background yang berjalan ketika Post dibuat.
    Menarik data live menggunakan AI dan menyimpannya ke tabel Post.
    """
    logger.warning(f"Memulai auto-sync cuaca untuk Post ID: {post_id}")
    
    with Session(engine) as db:
        post = db.get(Post, post_id)
        if not post:
            logger.error(f"Post ID {post_id} tidak ditemukan.")
            return

        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        prompt = f"""
        Please find live weather and marine data for today ({today_str}) for location: "{post.location}".
        CRITICAL: You MUST FIRST use the `get_real_marine_weather` tool to fetch actual satellite data using the exact GPS coordinates of '{post.location}' and the exact date '{today_str}'.
        Return this information ONLY in raw JSON format without markdown blocks (```json) or introductory text.
        IMPORTANT: Make it VERY CONCISE as data points, not sentences! Maximum 3-5 words per value.
        Use English language.
        
        CORRECT RESPONSE EXAMPLE:
        {{
            "wind": "Offshore, 10-15 knots",
            "swell": "1.5m, SW direction",
            "wave_height": "1.5m - 2.0m"
        }}
        
        Your task now, generate JSON like the example above for {post.location}:
        """
        
        try:
            res = surf_report_subagent.run(prompt)
            content = res.content if hasattr(res, 'content') else str(res)
            
            # Membersihkan tag markdown jika ada
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
                
            data = json.loads(content)
            
            post.wind_conditions = data.get("wind", "Data unavailable")
            post.swell_info = data.get("swell", "Data unavailable")
            post.tide_info = data.get("wave_height", data.get("tide", "Data unavailable")) # Save wave_height into tide_info field to avoid db schema changes
            post.ai_weather_synced = True
            
            db.add(post)
            db.commit()
            
            logger.warning(f"Auto-sync berhasil untuk Post ID {post_id}")
            
        except Exception as e:
            logger.error(f"Gagal auto-sync cuaca Post {post_id}: {str(e)}")
