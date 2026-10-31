
import os
import json
from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from google import genai
from pypdf import PdfReader
from docx import Document


# GEMINI CONFIGURATION

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-3.8-flash"

app = FastAPI(title="ResumeIQ AI Resume Analyzer")


# EXTRACT RESUME TEXT

def extract_resume_text(filename, file_bytes):

    extension = os.path.splitext(filename)[1].lower()

    try:

        if extension == ".txt":

            return file_bytes.decode(
                "utf-8-sig",
                errors="replace"
            )

        elif extension == ".pdf":

            reader = PdfReader(BytesIO(file_bytes))

            if reader.is_encrypted:

                raise ValueError(
                    "Password-protected PDF files are not supported."
                )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

            return text

        elif extension == ".docx":

            document = Document(BytesIO(file_bytes))

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
            ]

            return "\n".join(paragraphs)

        else:

            raise ValueError(
                "Unsupported format. Upload PDF, DOCX or TXT."
            )

    except ValueError:

        raise

    except Exception:

        raise ValueError(
            "Unable to read this file. Please upload a valid PDF, DOCX or TXT."
        )


# RESUME ANALYSIS API

@app.post("/api/analyze")
async def analyze_resume(

    job_description: str = Form(...),

    resume_file: UploadFile = File(None),

    resume_text: str = Form("")

):

    if not API_KEY:

        raise HTTPException(
            status_code=503,
            detail="Gemini API key is missing. Set GEMINI_API_KEY in PowerShell."
        )

    # GET RESUME TEXT

    if resume_file:

        if not resume_file.filename:

            raise HTTPException(
                status_code=400,
                detail="Please select a resume file."
            )

        file_bytes = await resume_file.read()

        if len(file_bytes) > 5 * 1024 * 1024:

            raise HTTPException(
                status_code=400,
                detail="File size must be less than 5 MB."
            )

        try:

            resume = extract_resume_text(
                resume_file.filename,
                file_bytes
            )

        except ValueError as error:

            raise HTTPException(
                status_code=400,
                detail=str(error)
            )

    else:

        resume = resume_text.strip()

    # VALIDATION

    if len(resume.strip()) < 80:

        raise HTTPException(
            status_code=400,
            detail="Not enough resume text was extracted. Try another file or paste the text manually."
        )

    if len(job_description.strip()) < 40:

        raise HTTPException(
            status_code=400,
            detail="Please provide a complete job description."
        )

    # GEMINI PROMPT

    prompt = f"""
You are a professional AI resume reviewer.

Compare the candidate's resume with the job description.

Provide honest, practical and useful feedback.

IMPORTANT:
- Never invent qualifications.
- Never invent work experience.
- Never invent certifications.
- Never invent skills.
- Base all feedback on the supplied resume.
- Recommended skills are suggestions, not claims that the candidate has them.

Return ONLY valid JSON in the following format:

{{
    "match_score": 75,
    "ai_analysis": "A short overview of the resume match.",
    "strengths": [
        "Strength one",
        "Strength two"
    ],
    "weaknesses": [
        "Area to improve"
    ],
    "recommended_skills": [
        "Python",
        "SQL"
    ],
    "suggestions": [
        "Actionable improvement suggestion"
    ],
    "summary_suggestion": "A professional resume summary based only on the supplied information."
}}

The match score must be an integer between 0 and 100.

Keep the feedback concise and professional.

RESUME:

{resume}

JOB DESCRIPTION:

{job_description}
"""

    # GEMINI API CALL

    try:

        client = genai.Client(api_key=API_KEY)

        response = client.models.generate_content(

            model=MODEL,

            contents=prompt,

            config={
                "response_mime_type": "application/json"
            }

        )

        result = json.loads(response.text)

        score = int(result.get("match_score", 0))

        score = max(0, min(100, score))

        return {

            "match_score": score,

            "ai_analysis": str(
                result.get("ai_analysis", "")
            ),

            "strengths": result.get(
                "strengths", []
            ),

            "weaknesses": result.get(
                "weaknesses", []
            ),

            "recommended_skills": result.get(
                "recommended_skills", []
            ),

            "suggestions": result.get(
                "suggestions", []
            ),

            "summary_suggestion": str(
                result.get("summary_suggestion", "")
            )

        }

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid response. Please try again."
        )

    except Exception as error:

        print("Gemini API error:", str(error))

        raise HTTPException(
            status_code=502,
            detail="Gemini analysis failed. Check your API key, model access and internet connection."
        )


# HOME PAGE

@app.get("/")
def home():

    return FileResponse("index.html")


# STATIC FILES

app.mount(
    "/",
    StaticFiles(directory=".", html=True),
    name="static"
)
