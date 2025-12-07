# backend/agents.py
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import os

load_dotenv()

# --- Using Google Gemini API client ---
import google.generativeai as genai
from tools import find_pois_osm, get_weather_open_meteo, POIToolError, WeatherToolError

# --- Set your Gemini API key here ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


def create_react_agent():
    """
    Returns a callable agent function `agent_run(input_dict) -> output_dict`.
    The agent uses an LLM 'planner' to decide tool usage dynamically.
    """
    def agent_run(user_input: Dict[str, Any]) -> Dict[str, Any]:
        city = user_input.get("city")
        start_date = user_input.get("start_date")
        end_date = user_input.get("end_date")
        if not city or not start_date or not end_date:
            return {"error": "Missing city or dates"}

        tool_desc = [
            {
                "name": "POI_TOOL",
                "description": "Returns a list of points of interest for a city. Call with: {city: <city>, limit: <int>}. Returns JSON: {city, center:{lat,lon}, pois:[{name,category,lat,lon,short_desc}, ...]}."
            },
            {
                "name": "WEATHER_TOOL",
                "description": "Returns daily weather data for latitude/longitude & date range. Call with: {lat, lon, start_date, end_date}. Returns JSON: {lat,lon,daily:[{date,summary,max_temp,min_temp,weathercode}, ...]}."
            },
            {
                "name": "ITINERARY_CREATOR",
                "description": "Takes POIs, weather, preferences, and date range and returns a day-by-day itinerary JSON table. Call with: {pois, weather_daily, start_date, end_date, preferences}."
            }
        ]

        prompt = f"""
You are a planner agent. User requested travel plan:
{json.dumps(user_input)}

You have access to these tools:
{json.dumps(tool_desc, indent=2)}

Produce a JSON 'plan' listing steps. Each step is an object:
{{"action": "<TOOL_NAME>", "args": {{...}}}}
Only use the tool names above. The plan should be minimal and only call what is needed.
Respond with ONLY JSON: {{ "plan": [ ... ] }}
"""

        # --- Gemini API call using latest SDK ---
        try:
            resp = genai.ChatCompletion.create(
                model="chat-bison-001",
                messages=[{"role": "user", "content": prompt}]
            )
            content = resp.choices[0].message.content
            parsed = json.loads(content)
            plan = parsed.get("plan", [])
        except Exception:
            # fallback plan
            plan = [
                {"action": "POI_TOOL", "args": {"city": city, "limit": 8}},
                {"action": "WEATHER_TOOL", "args": {"lat": None, "lon": None, "start_date": start_date, "end_date": end_date}},
                {"action": "ITINERARY_CREATOR", "args": {"start_date": start_date, "end_date": end_date, "preferences": user_input.get("preferences", {})}}
            ]

        state = {"user_input": user_input, "tools_called": []}

        # Execute plan steps
        for step in plan:
            action = step.get("action")
            args = step.get("args", {})
            try:
                if action == "POI_TOOL":
                    city_arg = args.get("city", city)
                    limit = args.get("limit", 8)
                    poi_res = find_pois_osm(city_arg, limit=limit)
                    state["pois"] = poi_res
                    state["tools_called"].append({"tool": "poi", "result": poi_res})

                elif action == "WEATHER_TOOL":
                    lat = args.get("lat")
                    lon = args.get("lon")
                    if not lat or not lon:
                        center = state.get("pois", {}).get("center")
                        if center:
                            lat = center["lat"]
                            lon = center["lon"]
                        else:
                            poi_res = find_pois_osm(city, limit=1)
                            center = poi_res["center"]
                            lat = center["lat"]
                            lon = center["lon"]
                            state["pois"] = poi_res
                    weather_res = get_weather_open_meteo(lat, lon, args.get("start_date"), args.get("end_date"))
                    state["weather"] = weather_res
                    state["tools_called"].append({"tool": "weather", "result": weather_res})

                elif action == "ITINERARY_CREATOR":
                    itinerary = create_itinerary_from_state(state, args.get("start_date"), args.get("end_date"), args.get("preferences", {}))
                    state["itinerary"] = itinerary
                    state["tools_called"].append({"tool": "itinerary", "result": itinerary})

                else:
                    state.setdefault("errors", []).append({"step": step, "error": "unknown action"})

            except POIToolError as e:
                state.setdefault("errors", []).append({"tool": "POI_TOOL", "error": str(e)})
            except WeatherToolError as e:
                state.setdefault("errors", []).append({"tool": "WEATHER_TOOL", "error": str(e)})
            except Exception as e:
                state.setdefault("errors", []).append({"tool": action, "error": str(e)})

        return {
            "weather": state.get("weather"),
            "pois": state.get("pois"),
            "itinerary": state.get("itinerary"),
            "meta": {"tools_called": state.get("tools_called"), "errors": state.get("errors", [])}
        }

    return agent_run


def create_itinerary_from_state(state: dict, start_date: str, end_date: str, preferences: dict):
    pois = state.get("pois", {}).get("pois", [])
    weather_daily = state.get("weather", {}).get("daily", [])
    prompt_payload = {
        "instruction": "Create a logical day-by-day itinerary for the given date range.",
        "pois": pois,
        "weather_daily": weather_daily,
        "preferences": preferences,
        "start_date": start_date,
        "end_date": end_date
    }

    llm_prompt = f"Create an itinerary JSON using this payload:\n{json.dumps(prompt_payload, indent=2)}\n\nReturn JSON: {{'days': [{{'date','morning','afternoon','evening','notes'}}]}}"

    # --- Gemini API call ---
    try:
        resp = genai.ChatCompletion.create(
            model="chat-bison-001",
            messages=[{"role": "user", "content": llm_prompt}]
        )
        content = resp.choices[0].message.content
        out = json.loads(content)
    except Exception:
        # Fallback itinerary generation
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        days = (end - start).days + 1
        days_list = []
        for i in range(days):
            d = (start + timedelta(days=i)).date().isoformat()
            morning = pois[i * 3]["name"] if i * 3 < len(pois) else None
            afternoon = pois[i * 3 + 1]["name"] if i * 3 + 1 < len(pois) else None
            evening = pois[i * 3 + 2]["name"] if i * 3 + 2 < len(pois) else "Free"
            notes = "Check weather: " + (weather_daily[i]["summary"] if i < len(weather_daily) else "")
            days_list.append({"date": d, "morning": morning, "afternoon": afternoon, "evening": evening, "notes": notes})
        out = {"days": days_list}

    return out
