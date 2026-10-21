"""
API v1 Router
Consolidates all v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, connection, upload, ai, analysis, quiz, coding, report

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    connection.router,
    tags=["Connection"]
)

api_router.include_router(
    upload.router,
    tags=["Upload"]
)

api_router.include_router(
    analysis.router,
    tags=["Analysis"]
)

api_router.include_router(
    quiz.router,
    tags=["Quiz"]
)

api_router.include_router(
    coding.router,
    tags=["Coding"]
)

api_router.include_router(
    report.router,
    tags=["Report"]
)

api_router.include_router(
    ai.router,
    tags=["AI"]
)
