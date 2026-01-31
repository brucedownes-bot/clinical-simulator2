"""
Grading Router - Grading statistics and rubric
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/rubric")
async def get_rubric():
    """Return the grading rubric"""
    return {
        "total_points": 10,
        "categories": [
            {
                "name": "Clinical Accuracy",
                "max_points": 4,
                "weight": 0.40
            },
            {
                "name": "Risk Assessment",
                "max_points": 3,
                "weight": 0.30
            },
            {
                "name": "Communication",
                "max_points": 2,
                "weight": 0.20
            },
            {
                "name": "Efficiency",
                "max_points": 1,
                "weight": 0.10
            }
        ]
    }


@router.get("/statistics")
async def get_statistics():
    """Get aggregate grading statistics"""
    return {
        "total_answers": 0,
        "average_scores": {
            "total": 0.0,
            "clinical_accuracy": 0.0,
            "risk_assessment": 0.0,
            "communication": 0.0,
            "efficiency": 0.0
        }
    }
