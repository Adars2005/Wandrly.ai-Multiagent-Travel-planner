🧭 Wandrly-AI: 
AI Agentic Travel Planner — Multi-Agent LangGraph System
This repository contains a LangGraph-inspired AI Travel Planner that dynamically plans trips based on natural language input. The system integrates weather, points of interest (POIs), and itinerary generation using a multi-agent architecture powered by a large language model (Gemini API).
1. Features 
           •	Accepts natural language trip descriptions, e.g.,
  "Plan a 2-day trip to New Delhi starting tomorrow".
  •	Dynamically decides which agents/tools to call using LLM.
  •	Returns:
  o	Weather forecast for the trip dates.
  o	Points of interest (POIs) with coordinates and categories.
  o	Day-by-day itinerary (morning, afternoon, evening) considering weather and preferences.
  •	Handles API errors gracefully and provides fallback itineraries.

2. Setup Instructions
Prerequisites
•	Python 3.10+
•	Pip
•	Streamlit
•	Gemini API key

Clone Repository
git clone https://github.com/yourusername/ai-travel-planner.git

cd ai-travel-planner
Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Install Dependencies
pip install -r requirements.txt
pip install streamlit

Environment Variables
Create a .env file with your Gemini API key:
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
Optional: define backend URL for Streamlit:
BACKEND_URL=http://localhost:8000
Run Backend (FastAPI)
cd backend
uvicorn main:app –reload
The API will run on http://localhost:8000.
Run Frontend (Streamlit)
cd frontend
streamlit run streamlit_app.py

3. LangGraph Design
Nodes (Agents):
Node	Function
Input Handler	Parses user query into structured input (city, dates, preferences).
POI Agent	Fetches city points of interest using OpenStreetMap APIs.
Weather Agent	Retrieves daily weather for trip dates from Open-Meteo API.
Itinerary Creator	Generates a day-by-day travel itinerary combining POIs, weather, and preferences.

Flow Diagram :
User Input
    ↓
Input Handler
    ↓
Gemini LLM → Decides dynamic plan → Calls necessary agents
    ↓
+-------------------+
| POI Agent         |
+-------------------+
    ↓
+-------------------+
| Weather Agent     |
+-------------------+
    ↓
+-------------------+
| Itinerary Creator |
+-------------------+
    ↓
JSON Output → Streamlit Frontend

4. Example Runs
Input:
Plan a 2-day trip to New Delhi starting tomorrow
Output (simplified):
Weather Info
•	Day 1 (2025-10-27): Clear, max 34°C, min 23°C
•	Day 2 (2025-10-28): Partly cloudy, max 32°C, min 22°C
Points of Interest (POIs)
Name	Category	Lat	Lon
India Gate	historic	28.6129	77.2295
Lotus Temple	tourism	28.5535	77.2588
Connaught Place	shop	28.6324	77.2197

Itinerary
Day	Morning	Afternoon	Evening	Notes
1	India Gate	Connaught Place	Free	Check weather: Clear
2	Lotus Temple	Free	Free	Check weather: Partly cloudy

AI Reasoning / Tools Called
•	POI Agent → retrieved 3 POIs
•	Weather Agent → retrieved 2-day forecast
•	Itinerary Creator → generated day-by-day plan

5. Assumptions, Limitations, and Improvements
Assumptions:
•	User inputs are in natural language and contain city and duration.
•	Gemini API is available and can generate tool call plans.
•	OpenStreetMap and Open-Meteo APIs are accessible and provide data.

Limitations:
•	Limited weather code mapping; unusual weather may not be described well.
•	POI parsing may miss certain attractions due to Overpass query limitations.
•	Single-city trips only; multi-city planning not supported yet.
•	Streamlit map is basic (no tooltips or interactive markers).

Possible Improvements:
•	Multi-city itinerary planning.
•	Budget and transport optimization.
•	Enhanced POI recommendations based on user preferences (e.g., museums, nightlife).
•	Interactive maps with tooltips and route planning.
•	Integration with hotel and ticket booking API

