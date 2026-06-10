import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ..core.config import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

# Vertex AI is imported and initialized lazily inside the endpoint. Initializing
# at module import would crash backend startup if the Vertex API is not enabled
# (and the AI feature is optional / hidden in the demo).
_model = None


def _get_model():
    global _model
    if _model is None:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location="us-central1")
        _model = GenerativeModel("gemini-1.5-flash-002")
    return _model


@router.post("/extract-employee")
async def extract_employee_data(file: UploadFile = File(...), user=Depends(get_current_user)):
    try:
        from vertexai.generative_models import Part

        content = await file.read()

        prompt = """
        Extract employee information from this document image/PDF.
        Return ONLY a JSON object with the following fields:
        first_name, last_name, cedula, email, salary, start_date (YYYY-MM-DD).
        If a field is not found, use null.
        """

        doc_part = Part.from_data(data=content, mime_type=file.content_type)

        response = _get_model().generate_content([prompt, doc_part])

        return {"extracted_data": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")
