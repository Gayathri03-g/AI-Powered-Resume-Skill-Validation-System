"""
Report Endpoints
"""

import os
import json
import time
import logging
from fastapi import APIRouter, HTTPException
from app.services.report_generator import ReportGenerator
from app.models.report import ReportRequest, ReportResponse, FinalReport
from app.utils.file_handler import FileStorage as FileHandler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-report", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest):
    """
    Generate the final comprehensive candidate evaluation report.
    Synthesizes resume profile, quiz performance, and coding challenge scores.
    """
    
    start_time = time.time()
    
    try:
        filename = request.filename
        if not filename or not isinstance(filename, str):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        filename = filename.strip()
        if os.path.basename(filename) != filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Validate scores
        if not isinstance(request.quiz_score, int) or request.quiz_score < 0 or request.quiz_score > 100:
            raise HTTPException(status_code=400, detail="Quiz score must be between 0 and 100")
        
        if request.coding_score is not None:
            if not isinstance(request.coding_score, int) or request.coding_score < 0 or request.coding_score > 100:
                raise HTTPException(status_code=400, detail="Coding score must be between 0 and 100")
        
        print(f"\n⏳ Generating final evaluation report...")
        print(f"  Quiz Score: {request.quiz_score}/100")
        if request.coding_score is not None:
            print(f"  Coding Score: {request.coding_score}/100")

        upload_dir = FileHandler.get_upload_dir()
        file_path = os.path.join(upload_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Session file not found. Please upload your resume again.")

        # Validate profile exists
        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            raise HTTPException(
                status_code=422,
                detail="Resume analysis not found. Please analyze your resume before generating a report."
            )

        report = await ReportGenerator.generate_final_report(
            file_path=file_path,
            quiz_score=request.quiz_score,
            coding_score=request.coding_score,
            coding_feedback=request.coding_feedback,
            quiz_feedback=request.quiz_feedback
        )

        if not report:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate report. Please try again."
            )
        
        elapsed_time = time.time() - start_time
        print(f"✓ Report generated in {elapsed_time:.2f} seconds - Verdict: {report.recommendation.verdict}")

        return ReportResponse(
            success=True,
            report=report,
            message=f"Report generated successfully — Verdict: {report.recommendation.verdict}",
            processing_time_seconds=round(elapsed_time, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )
