from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import List

from backend.app.models.engine import get_session
from backend.app.modules.surf.agents import ombak_nusantara_supervisor
from backend.app.models.database import User, SurfPlan, SurfReport
from backend.app.modules.surf.schema import UserCreateRequest, SurfPlanCreateRequest, UserLoginRequest, UserUpdateSkillRequest

router = APIRouter()
# ==========================================
# 0. ENDPOINT: Autocomplete Surf Spots
# ==========================================
@router.get("/spots/search")
async def search_surf_spots(q: str = ""):
    surf_spots = [
        "Uluwatu, Bali", "Padang Padang, Bali", "Kuta, Bali", "Canggu, Bali", 
        "Batu Bolong, Bali", "Echo Beach, Bali", "Medewi, Bali", "Balian, Bali", 
        "Keramas, Bali", "Bingin, Bali", "Dreamland, Bali", "Balangan, Bali", 
        "Sorake Beach, Nias", "Lances Right, Mentawai", "Macaronis, Mentawai", 
        "Playgrounds, Mentawai", "Cimaja, West Java", "Krui, Sumatra", 
        "Lakey Peak, Sumbawa", "G-Land (Plengkung), East Java", "Desert Point, Lombok",
        "Tanjung Setia, Krui", "Watu Karung, Pacitan", "Red Island (Pulau Merah), Banyuwangi",
        "Mentawai Islands, West Sumatra", "Nias, North Sumatra", "Sumbawa, NTB",
        "Rote Island, NTT", "T-Land, Rote"
    ]
    
    if not q:
        return []
        
    query = q.lower()
    matches = [spot for spot in surf_spots if query in spot.lower()]
    return matches[:10]  # Return top 10 matches

# ==========================================
# 1. ENDPOINT: Membuat User Baru (Helper)
# ==========================================
@router.post("/users", response_model=User)
async def create_user(request: UserCreateRequest, db: Session = Depends(get_session)):
    existing_user = db.exec(
        select(User).where((User.username == request.username) | (User.email == request.email))
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered.")
        
    new_user = User(
        username=request.username,
        email=request.email,
        password=request.password,
        skill_level=request.skill_level
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=User)
async def login_user(request: UserLoginRequest, db: Session = Depends(get_session)):
    user = db.exec(
        select(User).where(User.username == request.username, User.password == request.password)
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user_skill(user_id: int, request: UserUpdateSkillRequest, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.skill_level = request.skill_level
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ==========================================
# 1b. ENDPOINT: Melihat Semua User (Helper)
# ==========================================
@router.get("/users", response_model=list[User])
async def get_all_users(limit: int = 100, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(User).offset(offset).limit(limit)
    users = db.exec(statement).all()
    return users

@router.get("/users/search")
async def search_users(q: str = "", db: Session = Depends(get_session)):
    if not q:
        return []
    statement = select(User).where(User.username.ilike(f"%{q}%")).limit(5)
    users = db.exec(statement).all()
    return [{"id": u.id, "username": u.username, "profile_pic_url": u.profile_pic_url} for u in users]

# ==========================================
# 1c. ENDPOINT V2: Profil & Garasi Papan
# ==========================================
from backend.app.modules.surf.schema import UserProfileResponse, UserUpdateBioRequest, UserUpdateProfilePicRequest, SurfboardCreateRequest, SurfboardResponse
from backend.app.models.database import Surfboard

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@router.put("/users/{user_id}/bio", response_model=User)
async def update_user_bio(user_id: int, request: UserUpdateBioRequest, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.bio = request.bio
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/users/{user_id}/profile_pic", response_model=User)
async def update_user_profile_pic(user_id: int, request: UserUpdateProfilePicRequest, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.profile_pic_url = request.profile_pic_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/users/{user_id}/surfboards", response_model=SurfboardResponse)
async def add_surfboard(user_id: int, request: SurfboardCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    new_board = Surfboard(
        user_id=user_id,
        name=request.name,
        brand=request.brand,
        length=request.length,
        caption=request.caption,
        image_url=request.image_url
    )
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    return new_board



# ==========================================
# 2. ENDPOINT UMA (POST /analyze) dengan Cache
# ==========================================
@router.post("/analyze")
async def create_surf_plan_and_analyze(
    request: SurfPlanCreateRequest,
    db: Session = Depends(get_session)
):
    # 1. Ambil data User dari DB berdasarkan ID
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=404, 
            detail=f"User with ID {request.user_id} not found. Create a user first at POST /api/surf/users"
        )

    # 2. ⚡ SMART CACHING LAYER ⚡
    # Periksa apakah ada laporan valid untuk lokasi & tanggal yang sama dalam 6 jam terakhir
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    
    cached_report = db.exec(
        select(SurfReport)
        .join(SurfPlan)
        .where(
            SurfPlan.target_spot == request.target_spot,
            SurfPlan.planned_date == request.planned_date,
            SurfReport.generated_at >= six_hours_ago,
            SurfReport.safety_status != "Danger"  # Jangan cache status bahaya karena cuaca ekstrem cepat berubah
        )
    ).first()

    if cached_report:
        # Jika cache ditemukan, buat SurfPlan baru tapi pasangkan langsung ke laporan lama
        new_plan = SurfPlan(
            user_id=request.user_id,
            target_spot=request.target_spot,
            planned_date=request.planned_date,
            status="Approved"
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        return {
            "status": "success_cached",
            "message": "Optimized response fetched from cache.",
            "plan_id": new_plan.id,
            "plan_status": new_plan.status,
            "safety_status": cached_report.safety_status,
            "summary": cached_report.summary,
            "report_markdown": cached_report.content_md
        }

    # 3. KONDISI CACHE MISS: Jalankan Live Agent Swarm
    try:
        new_plan = SurfPlan(
            user_id=request.user_id,
            target_spot=request.target_spot,
            planned_date=request.planned_date,
            status="Pending"
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        # Lempar data profile dinamis ke Agent Swarm
        # Tambahan instruksi khusus untuk Beginner (AI Smart Matching)
        instructor_prompt = ""
        import random
        local_names = ["Bli Wayan (Bali)", "Kang Asep (West Java)", "Mas Joko (East Java)", "Pak Budi (Sumatra)", "Bli Ketut (Bali)", "Mas Yanto (Central Java)", "Bang Jali (Jakarta)"]
        random_name = random.choice(local_names).split(" (")[0]
        random_price = random.choice([250, 300, 350, 400, 450])
        
        if user.skill_level.lower() == "beginner":
            instructor_prompt = (
                "**🏄‍♂️ AI Smart Match (Beginner):**\\n"
                f"- 🥇 **Instructor:** {random_name} (Certified ISA)\\n"
                f"- 💵 **Rate:** IDR {random_price}k / 2-hour lesson\\n\\n"
            )

        prompt = (
            f"Analyze surfing conditions for location: '{request.target_spot}' on Date: '{request.planned_date}'.\n"
            f"USER'S PREFERRED TIME: '{request.preferred_time}'. CRITICAL: The Comprehensive Surf Itinerary MUST be strictly aligned with this time of day!\n"
            f"CRITICAL: You MUST FIRST use the `get_real_marine_weather` tool to fetch actual satellite marine data using the exact GPS coordinates of '{request.target_spot}' and date '{request.planned_date}'.\n"
            f"CRITICAL: You MUST use web search tools (if available) or your deep geographical knowledge to find ACTUAL, REAL-WORLD local businesses, restaurants, homestays, and transport services in '{request.target_spot}'. Do not hallucinate generic names.\n"
            f"Tailor the trip plan based on this REAL DATA and the user profile: '{user.skill_level} surfer'.\n\n"
            f"IMPORTANT FORMAT RULES: You MUST return ONLY a valid JSON object. Do not wrap it in ```json. You MUST write EVERYTHING entirely in ENGLISH. The content must be extremely detailed, professional, and rich in context. Follow this exact structure, but REPLACE all bracketed [placeholders] with REALISTIC LOCAL DATA and REAL WEATHER DATA:\n"
            f"{{\n"
            f"  \"status\": \"APPROVED\",\n"
            f"  \"coordinates\": {{\"lat\": [Latitude_Number_Only], \"lng\": [Longitude_Number_Only]}},\n"
            f"  \"surf_conditions\": \"### 🚀 Quick Overview\\n- **🌊 Waves:** 1.5 - 2.0m\\n- **💨 Wind:** 10 knots, Offshore\\n- **🌊 Swell:** SW, 12s period\\n- **🌡️ Temp:** 28°C Water / 30°C Air\\n- **📈 Tide:** High @ 08:30 AM (1.8m)\\n- **⛅ Weather:** Sunny, Light Breeze\\n- **🌅 Sunlight:** Sunrise 06:15 AM | Sunset 06:30 PM\\n- **🕶️ UV Index:** 8 (High)\",\n"
            f"  \"trip_plan\": \"### 📅 Comprehensive Surf Itinerary\\n\\nWrite a highly detailed, professional, and exhaustive minute-by-minute itinerary for the surfer strictly aligned with their preferred time: {request.preferred_time}. Describe exact time blocks, specific physical preparations (e.g. dynamic stretching, muscle warm-ups), the precise strategy to paddle out (e.g. channel mapping, avoiding reef hazards), positioning in the lineup, wave selection strategies based on the pushing/dropping tide, and post-surf recovery protocols. Make it read like a premium surf coaching guide.\\n\\n**⏰ [Exact Time {request.preferred_time}] | Pre-Surf Protocol & Ocean Observation:**\\n- Detail 3-4 specific actions. (e.g., observing the set intervals, analyzing wind texture, specific warm-ups).\\n\\n**🏄‍♂️ [Exact Time {request.preferred_time}] | The Paddle Out & Lineup Positioning:**\\n- Provide an exact tactical breakdown of how to enter the water safely and where to sit in the lineup relative to the peak and local landmarks.\\n\\n**🌊 [Exact Time {request.preferred_time}] | Peak Session Strategy:**\\n- Give highly technical advice on wave selection. Discuss inside vs outside sets, priority rules, and how to execute maneuvers based on the specific wave shape at this beach.\\n\\n**🔄 Plan B Tactical Shift:**\\n- Detail a highly specific alternative break or strategy if the main peak is crowded or blown out. Explain exactly where to walk/paddle.\\n\\n**🍛 [Exact Time {request.preferred_time}] | Post-Surf Recovery:**\\n- Recommend specific local warungs, exact dishes for protein recovery, and specific cool-down stretches. BE EXTREMELY DETAILED AND ELABORATIVE. WRITE AT LEAST 400 WORDS FOR THIS ENTIRE SECTION.\",\n"
            f"  \"local_ecosystem\": \"### 💼 Local Logistics\\n\\n#### 🛵 Transport Options:\\n**Scooter (with board rack)**\\nPrice: Est. IDR [Price Range]/day\\n\\n**Car / SUV (with driver)**\\nPrice: Est. IDR [Price Range]/day\\n\\n**Ride-Hailing (Gojek/Grab)**\\n_([Availability])_\\nPrice: Est. IDR [Price per short trip]\\n\\n{instructor_prompt}#### 🏄‍♂️ Surf Shops & Rentals:\\n**[Actual Surf Shop/Rental Name in area]**\\n_([Brief description or board types])_\\nPrice: Est. IDR [Price Range X to Y]/2hrs\\n\\n#### 🍛 Food & Dining:\\n**[Actual Local Eatery/Restaurant Name]**\\n_([Category - Brief description])_\\nPrice: Est. IDR [Price Range]\\n\\n**[Another Actual Eatery Name]**\\n_([Category - Brief description])_\\nPrice: Est. IDR [Price Range]\\n\\n#### 🎁 Local Souvenirs:\\n**[Actual Market/Shop Name nearby]**\\n[What to buy: e.g. local crafts, surf tees]\\n\\n#### ♻️ Eco-Note:\\n1 tip to protect this beach\",\n"
            f"  \"gear_hazards\": \"### 🎒 Gear & Hazards\\n\\n#### 🏄‍♀️ Board Choice:\\n**[Specific Board Type/Model]**\\n_([Brief explanation based on current {request.target_spot} conditions])_\\n\\n#### 🕯️ Essentials:\\n[Specific Wax Temp], [Sunscreen Type], [Booties/Rashguard needed?]\\n\\n#### ⚠️ Hazards:\\n[Actual local hazards, e.g. specific reef names, local rip currents, urchins]\\n\\n#### 🚑 Nearest Med:\\n[Actual Name of the Nearest Clinic/Hospital to {request.target_spot}]\",\n"
            f"  \"hotel_recommendations\": \"### 🏨 Where to Stay\\n\\n#### ⭐ Premium Resort / Hotel 1:\\n**[Actual Hotel Name]**\\n_([Brief vibe description])_\\nPrice: Est. IDR [Market Price]/night\\n\\n📍 _Distance: [X] minutes walk/ride to {request.target_spot}_\\n\\n#### ⭐ Premium Resort / Hotel 2:\\n**[Another Actual Hotel Name]**\\n_([Brief vibe description])_\\nPrice: Est. IDR [Market Price]/night\\n\\n📍 _Distance: [X] minutes walk/ride to {request.target_spot}_\\n\\n#### 🏨 Mid-Range / Boutique Hotel:\\n**[Actual Hotel Name]**\\n_([Brief description])_\\nPrice: Est. IDR [Market Price]/night\\n\\n📍 _Distance: [X] minutes walk/ride to {request.target_spot}_\\n\\n#### 🏄‍♂️ Local Surf Homestay:\\n**[Actual Homestay Name]**\\n_([Brief description])_\\nPrice: Est. IDR [Market Price]/night\\n\\n📍 _Distance: [X] minutes walk/ride to {request.target_spot}_\"\n"
            f"}}\n\n"
            f"CRITICAL JSON RULES:\n"
            f"1. You MUST NOT use double quotes (\") inside any of the text values. DO NOT wrap names of places/hotels/restaurants in single quotes ('). Just use bold text.\n"
            f"2. You MUST strictly use Markdown italics (underscore formatting: _(description)_) for descriptions, exactly as templated.\n"
            f"3. You MUST ESCAPE ALL NEWLINES as \\n within the string values. DO NOT output raw/literal newline characters, as this will break JSON parsing.\n"
            f"4. DO NOT add any introductory or concluding text outside the JSON object. Return strictly JSON starting with {{ and ending with }}.\n"
            f"5. Ensure the JSON is completely valid without trailing commas.\n"
            f"6. If dangerous, change status to REJECTED."
        )
        
        agent_response = ombak_nusantara_supervisor.run(prompt)
        final_report_md = agent_response.content if hasattr(agent_response, 'content') else str(agent_response)
        
        # Bersihkan pembungkus code block markdown jika AI membandel
        final_report_md = final_report_md.replace("```json", "").replace("```", "").strip()
        
        # Tentukan Safety Status berdasarkan laporan teks Agen
        safety_status = "Safe"
        if "\"status\": \"REJECTED\"" in final_report_md.upper() or "\"STATUS\":\"REJECTED\"" in final_report_md.upper():
            safety_status = "Danger"
            new_plan.status = "Rejected"
        else:
            new_plan.status = "Approved"

        summary_text = f"Live swarm analysis for {request.target_spot} on {request.planned_date} tailored for {user.skill_level} skill level."

        # Simpan analisis baru ke tabel SurfReport
        surf_report = SurfReport(
            surf_plan_id=new_plan.id,
            safety_status=safety_status,
            summary=summary_text,
            content_md=final_report_md
        )
        
        db.add(surf_report)
        db.commit()
        db.refresh(new_plan)
        
        return {
            "status": "success_live",
            "plan_id": new_plan.id,
            "plan_status": new_plan.status,
            "safety_status": surf_report.safety_status,
            "summary": surf_report.summary,
            "report_markdown": surf_report.content_md
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process plan or execute agent swarm: {str(e)}"
        )


# ==========================================
# 3. ENDPOINT: Cek Riwayat Rencana User
# ==========================================
@router.get("/users/{user_id}/plans")
async def get_user_surf_plans(user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "username": user.username,
        "skill_level": user.skill_level,
        "total_plans": len(user.surf_plans),
        "plans": [
            {
                "plan_id": plan.id,
                "target_spot": plan.target_spot,
                "planned_date": plan.planned_date,
                "status": plan.status,
                "report": {
                    "safety_status": plan.report.safety_status,
                    "summary": plan.report.summary,
                    "content_md": plan.report.content_md
                } if plan.report else None
            } for plan in user.surf_plans
        ]
    }

# ==========================================
# 4. ENDPOINT: Delete Riwayat Rencana User
# ==========================================
@router.delete("/plans/{plan_id}")
async def delete_surf_plan(plan_id: int, user_id: int, db: Session = Depends(get_session)):
    plan = db.get(SurfPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    if plan.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this plan")
        
    # Delete associated report first (SQLModel doesn't cascade by default without sa_relationship_kwargs)
    if plan.report:
        db.delete(plan.report)
        
    db.delete(plan)
    db.commit()
    return {"message": "Surf plan deleted successfully"}