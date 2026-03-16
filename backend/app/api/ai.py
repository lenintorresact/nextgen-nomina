import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ..core.config import get_current_user
import base64
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, Part

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/extract-employee")
async def extract_employee_data(file: UploadFile = File(...), user=Depends(get_current_user)):
    try:
        content = await file.read()

        # Initialize Vertex AI
        vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location="us-central1")
        model = GenerativeModel("gemini-1.5-flash-002")

        prompt = """
        Extract employee information from this document image/PDF.
        Return ONLY a JSON object with the following fields:
        first_name, last_name, cedula, email, salary, start_date (YYYY-MM-DD).
        If a field is not found, use null.
        """

        doc_part = Part.from_data(data=content, mime_type=file.content_type)

        response = model.generate_content([prompt, doc_part])

        return {"extracted_data": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")
