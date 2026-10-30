import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

app = FastAPI(title="ResumeIQ")

class ResumeRequest(BaseModel):
    resume_text: str = Field(min_length=80, max_length=25000)
    job_description: str = Field(min_length=40, max_length=15000)


@app.post("/api/analyze")
def analyze_resume(request: ResumeRequest):

    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is missing. Set GEMINI_API_KEY in PowerShell."
        )

    prompt = f"""
You are a professional resume reviewer.

Compare the resume with the job description.
Give honest, practical feedback. Never invent experience,
skills, certifications or achievements.

Return ONLY valid JSON in this exact format:

{{
  "match_score": 75,
  "ai_analysis": "A short overview of the resume match.",
  "strengths": ["Strength one", "Strength two"],
  "weaknesses": ["Area to improve"],
  "recommended_skills": ["Python", "SQL"],
  "suggestions": ["Actionable suggestion"],
  "summary_suggestion": "A suggested resume summary based only on the supplied resume."
}}

The score must be an integer from 0 to 100.
Keep all lists concise and useful.
Recommended skills are suggestions, not claims that the candidate already has them.

RESUME:
{request.resume_text}

JOB DESCRIPTION:
{request.job_description}
"""

    try:
        client = genai.Client(api_key=API_KEY)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        result = json.loads(response.text)

        score = max(0, min(100, int(result.get("match_score", 0))))

        return {
            "match_score": score,
            "ai_analysis": str(result.get("ai_analysis", "")),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "recommended_skills": result.get("recommended_skills", []),
            "suggestions": result.get("suggestions", []),
            "summary_suggestion": str(result.get("summary_suggestion", ""))
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid response. Please try again."
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Gemini analysis failed. Check your API key, model access and internet connection."
        )


@app.get("/")
def home():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory=".", html=True), name="static")