# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")

st.title("🧭 Multi-Agent Travel Planner")
st.markdown("Describe your trip in a single sentence, e.g., 'Plan a 2-day trip to New Delhi starting tomorrow'")

# --- Input ---
trip_sentence = st.text_input(
    "Your trip plan",
    value="Plan a 2-day trip to New Delhi starting tomorrow"
)

if st.button("Plan trip"):
    payload = {"query": trip_sentence}
    with st.spinner("Assembling plan..."):
        try:
            resp = requests.post(f"{BACKEND_URL}/plan", json=payload, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as e:
            st.error(f"Error contacting backend: {e}")
            st.stop()

    data = resp.json().get("result", {})

    # --- Weather ---
    if data.get("weather"):
        st.header("☀️ Weather Info")
        for i, d in enumerate(data["weather"]["daily"], start=1):
            st.write(f"• Day {i} ({d['date']}): {d['summary']}")

    # --- Points of Interest Map ---
    if data.get("pois"):
        st.header("📍 Points of Interest Map")

        # Extract valid coordinates
        map_points = []
        for poi in data["pois"]["pois"]:
            lat = poi.get("lat")
            lon = poi.get("lon")
            if lat is not None and lon is not None:
                map_points.append({"lat": lat, "lon": lon, "name": poi.get("name", ""), "category": poi.get("category","")})

        if map_points:
            df_map = pd.DataFrame(map_points)
            st.map(df_map)  # Basic map

            # Creative: Show POI names with category in a table next to map
            st.subheader("POI Details")
            st.dataframe(df_map[["name", "category", "lat", "lon"]])

        else:
            st.info("No valid coordinates found for POIs to display on map.")

    # --- Travel Itinerary ---
    if data.get("itinerary"):
        st.header("🧳 Travel Itinerary")
        rows = []
        for i, day in enumerate(data["itinerary"]["days"], start=1):
            rows.append({
                "Day": i,
                "Morning": day.get("morning",""),
                "Afternoon": day.get("afternoon",""),
                "Evening": day.get("evening",""),
                "Notes": day.get("notes","")
            })
        df = pd.DataFrame(rows)
        st.dataframe(df)

    # --- AI Reasoning / Explainability ---
    if data.get("meta", {}).get("tools_called"):
        with st.expander("🧠 How AI planned this trip"):
            st.write("### Reasoning Steps")
            for step in data["meta"]["tools_called"]:
                tool_name = step.get("tool")
                st.markdown(f"**Tool Used:** `{tool_name}`")
                result = step.get("result", {})
                if isinstance(result, dict) and "pois" in result:
                    st.write(f"- Retrieved {len(result['pois'])} POIs.")
                elif isinstance(result, dict) and "daily" in result:
                    st.write(f"- Retrieved {len(result['daily'])} weather entries.")
                else:
                    st.json(result)
                st.markdown("---")

    # --- Errors ---
    if data.get("meta", {}).get("errors"):
        st.warning("⚠️ Some tools encountered errors. Expand reasoning above for context.")
