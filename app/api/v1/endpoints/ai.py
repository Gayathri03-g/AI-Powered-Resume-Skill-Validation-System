"""
AI Endpoints
Handles AI-related operations (Health check, Skill Analysis, etc.)
"""

from fastapi import APIRouter
from app.core.ai import GeminiClient
from google import genai

router = APIRouter()

@router.get("/ai-health")
async def ai_health_check(model: str = "gemini-2.5-flash"):
    """
    Test connectivity to Gemini AI.
    Sends a simple 'Hello' prompt.
    """
    try:
        # Debug info
        GeminiClient.configure()
        lib_version = getattr(genai, '__version__', 'unknown')
        
        response = await GeminiClient.generate_content(
            "Say 'Gemini is online' in 3 words.",
            model_name=model
        )
        return {
            "status": "online" if "online" in str(response).lower() else "error",
            "message": response,
            "used_model": model,
            "lib_version": lib_version,
            "provider": "Google Gemini"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "used_model": model,
            "lib_version": getattr(genai, '__version__', 'unknown') if hasattr(genai, "__version__") else "unknown",
            "provider": "Google Gemini"
        }
