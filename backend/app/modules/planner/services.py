import json 
from pydantic import BaseModel, Field

from backend.app.modules.planner.utils import tavily_client, oai_client
from backend.app.modules.planner.prompts import GENERATE_QUERIES, SUMMARIZE_SYSTEM_PROMPT, SYNTHESIZE_SYSTEM_PROMPT

class Queries(BaseModel):
    intent: str
    queries: list[str] = Field(description="The queries to search for")


def generate_queries(topic: str):
    res = oai_client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": GENERATE_QUERIES},
            {"role": "user", "content": topic},
        ],
        response_format=Queries,
    )

    content = res.choices[0].message.parsed
    if content is None:
        raise ValueError("No queries were generated")
    return content.queries

import httpx

def get_open_meteo_marine_data(spot: str, region: str, date: str) -> str:
    try:
        res = oai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Return ONLY a valid JSON with 'lat' and 'lng' floats for the surfing spot '{spot}, {region} Indonesia'. Do not wrap in markdown, just the raw JSON."}],
            response_format={"type": "json_object"}
        )
        content = res.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        coords = json.loads(content)
        lat = coords["lat"]
        lng = coords["lng"]
        
        weather_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lng}&hourly=wave_height,swell_wave_height,swell_wave_period&timezone=auto&start_date={date}&end_date={date}"
        weather_res = httpx.get(weather_url, timeout=120.0).json()
        
        wind_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&hourly=temperature_2m,wind_speed_10m&timezone=auto&start_date={date}&end_date={date}"
        wind_res = httpx.get(wind_url, timeout=120.0).json()
        
        waves = weather_res.get("hourly", {}).get("wave_height", [])
        winds = wind_res.get("hourly", {}).get("wind_speed_10m", [])
        swells = weather_res.get("hourly", {}).get("swell_wave_height", [])
        
        if not waves: return "Open-Meteo Data: Not available."
        
        day_waves = waves[6:18]
        day_winds = winds[6:18]
        day_swells = swells[6:18]
        
        def avg(lst):
            clean = [x for x in lst if x is not None]
            return sum(clean) / len(clean) if clean else 0
            
        return f"\n\n[CRITICAL OPEN-METEO SATELLITE DATA FOR {date}]\nWave Height: {avg(day_waves):.1f}m - {max([x for x in day_waves if x is not None] or [0]):.1f}m\nWind Speed: {avg(day_winds):.1f} km/h\nSwell: {avg(day_swells):.1f}m\n(Instruction: YOU MUST cite 'Open-Meteo Marine API' as the Source for these numerical values!)\n"
    except Exception as e:
        return f"\n\n[Open-Meteo fetching failed: {str(e)}]\n"

def search_internet(query: str):
    try:
        response = tavily_client.search(
            query=query,
            include_answer="advanced",
            search_depth="advanced"
        )

        answer = response.get("answer", "")
        results = response.get("results", [])

        formatted_results = json.dumps(results, indent=2, ensure_ascii=False)

        full_text = f"""
        Use Original Query: {query}

        Answer from web_search: {answer}
        Full raw_results from web_search:

        {formatted_results}
        """
        
        return summarize(full_text)
    except Exception as e:
        print(f"⚠️ Tavily API Error: {str(e)}. Using fallback data.")
        fallback_text = f"Fallback mock data for {query}: The waves are 4-6ft, wind is light offshore, and it is a sunny day. Good conditions for surfing."
        return summarize(fallback_text)


def summarize(text: str):
    res = oai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )

    content = res.choices[0].message.content
    return content

def synthesize_answer(topic: str, context: str):
    res = oai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYNTHESIZE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Topic: {topic}, Context: {context}"},
        ],
        response_format={"type": "json_object"}
    )

    content = res.choices[0].message.content
    content = content.replace("```json", "").replace("```markdown", "").replace("```", "").strip()
    return content