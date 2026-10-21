"""
Gemini AI Client Wrapper
Handles all interactions with Google's Gemini Models.
Updated for google-genai
"""

from google import genai
from google.genai.errors import APIError
from app.core.config import settings
from typing import Optional, Any
import logging
import asyncio
import random

# Configure logging
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Wrapper for Google's Gemini AI.
    Features:
    - Singleton configuration
    - Safe API key handling
    - Error wrapping
    """
    
    _client: Optional[genai.Client] = None

    @classmethod
    def configure(cls):
        """Initialize the Gemini SDK with API key from settings."""
        if cls._client is not None:
            return
            
        if not settings.GEMINI_API_KEY or "your-gemini-api-key" in settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            logger.warning("GEMINI_API_KEY is not set or is using default value. AI features may fail.")
            # Even if API Key is not set, we create a client so it can bubble errors cleanly.
            try:
                cls._client = genai.Client()
            except Exception as e:
                logger.error(f"Failed to auto-configure Gemini Client: {e}")
        else:
            try:
                cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Gemini AI successfully configured.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini Client: {e}")
                raise

    @classmethod
    def get_client(cls) -> Optional[genai.Client]:
        """Get the configured client instance."""
        cls.configure()
        return cls._client

    @staticmethod
    async def generate_content(prompt: str, model_name: str = "gemini-2.5-flash") -> Optional[str]:
        """
        Generate content from a text prompt with automatic retries for rate limits.
        """
        client = GeminiClient.get_client()
        if not client:
            return "Error: Gemini API Key not configured correctly."

        max_retries = 2
        base_delay = 2
        
        models_to_try = []
        if model_name:
            models_to_try.append(model_name)
        models_to_try.extend(["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"])
        
        # Remove duplicates preserving order
        models_to_try = list(dict.fromkeys(models_to_try))
        
        for model_id in models_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting generation with {model_id} (Attempt {attempt+1}/{max_retries})")
                    response = await client.aio.models.generate_content(
                        model=model_id,
                        contents=prompt
                    )
                    return response.text
                except APIError as e:
                    if e.code in {429, 500, 503}:
                        wait_time = base_delay * (2 ** attempt) + random.uniform(0, 0.75)
                        logger.warning(
                            f"Retryable API error ({e.code}) on {model_id}. Retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                    elif e.code == 404:
                        logger.warning(f"Model {model_id} not found (404).")
                        break
                    else:
                        logger.warning(f"API Error on {model_id}: {str(e)}")
                        break
                except Exception as e:
                    logger.warning(f"Unhandled exception on {model_id}: {str(e)}")
                    break

        return "AI Error: All models and retries failed due to quota, limits, or configuration issues."

# Default global accessor
ai_client = GeminiClient()
