# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import create_react_agent
from utils import parse_trip_sentence  # new helper
import uvicorn

app = FastAPI(title="Multi-Agent Travel Planner")

agent = create_react_agent()

class TripRequest(BaseModel):
    query: str  # user enters the sentence

@app.post("/plan")
def plan_trip(req: TripRequest):
    try:
        # Parse natural language sentence
        parsed_input = parse_trip_sentence(req.query)

        # Run agent
        result = agent(parsed_input)

        # Return results with error info if any
        if result.get("meta", {}).get("errors"):
            return {"status": "partial", "result": result}
        return {"status": "ok", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
