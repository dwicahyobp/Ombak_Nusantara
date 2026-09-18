from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.tavily import TavilyTools
import httpx

from backend.app.core.settings import settings
from backend.app.modules.knowledge.vectordb import search_safety_rules

def get_real_marine_weather(lat: float, lng: float, date: str) -> str:
    """Gets real-time marine weather (wave height, swell, wind, temp) for a given GPS location and date (YYYY-MM-DD)."""
    try:
        weather_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lng}&hourly=wave_height,swell_wave_height,swell_wave_period&timezone=auto&start_date={date}&end_date={date}"
        weather_res = httpx.get(weather_url).json()
        
        wind_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&hourly=temperature_2m,wind_speed_10m&timezone=auto&start_date={date}&end_date={date}"
        wind_res = httpx.get(wind_url).json()
        
        waves = weather_res.get("hourly", {}).get("wave_height", [])
        swells = weather_res.get("hourly", {}).get("swell_wave_height", [])
        periods = weather_res.get("hourly", {}).get("swell_wave_period", [])
        winds = wind_res.get("hourly", {}).get("wind_speed_10m", [])
        temps = wind_res.get("hourly", {}).get("temperature_2m", [])
        
        if not waves: return "No marine data available."
        
        # Ambil rata-rata data siang hari (index 6 s.d 18)
        day_waves = waves[6:18]
        day_swells = swells[6:18]
        day_periods = periods[6:18]
        day_winds = winds[6:18]
        day_temps = temps[6:18]
        
        def avg(lst):
            clean = [x for x in lst if x is not None]
            return sum(clean) / len(clean) if clean else 0
            
        return (
            f"--- REAL SATELLITE DATA FOR {date} ---\n"
            f"Wave Height: {avg(day_waves):.1f}m - {max([x for x in day_waves if x is not None] or [0]):.1f}m\n"
            f"Swell: {avg(day_swells):.1f}m, Period: {avg(day_periods):.1f}s\n"
            f"Wind Speed: {avg(day_winds):.1f} km/h\n"
            f"Water/Air Temp: {avg(day_temps):.1f}°C\n"
            f"Use this EXACT data in your Quick Overview!"
        )
    except Exception as e:
        return f"Failed to fetch real data: {str(e)}"

# ==========================================
# 1. SUB-AGENTS DEFINITION (WORKERS)
# ==========================================

surf_report_subagent = Agent(
    name="Surf Report Sub-Agent",
    role=(
        "Search the live web to analyze current marine weather conditions, "
        "wave heights, swell direction, and wind speeds at the specified surfing locations."
    ),
    model=OpenAIChat(id="gpt-4o", api_key=settings.openai_api_key),
    tools=[get_real_marine_weather, TavilyTools(api_key=settings.tavily_api_key)],
    markdown=True,
    debug_mode=True,
)

surf_plan_subagent = Agent(
    name="Surf Plan Sub-Agent",
    role="Create personalized surf schedules, surfboard recommendations, and safety tips tailored to the user's profile.",
    model=OpenAIChat(id="gpt-4o", api_key=settings.openai_api_key),
    tools=[search_safety_rules],
    markdown=True,
    debug_mode=True,
)

# ==========================================
# 2. SUPERVISOR TEAM DEFINITION (MAIN AGENT)
# ==========================================

ombak_nusantara_supervisor = Team(
    name="Ombak Nusantara Main Supervisor",
    model=OpenAIChat(id="gpt-4o", api_key=settings.openai_api_key),
    members=[surf_report_subagent, surf_plan_subagent],
    description=(
        "You are the main manager of Ombak Nusantara. When a user makes a request, "
        "you must delegate the real-time live web search for marine data to the 'Surf Report Sub-Agent' "
        "and the trip planning task to the 'Surf Plan Sub-Agent'. "
        "Combine the insights from both sub-agents into a single, cohesive, and user-friendly final report."
    ),
    markdown=True,
    debug_mode=True,
)

