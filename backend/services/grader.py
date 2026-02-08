"""
Answer Grading Service (Engine B)
==================================
Implements the "Persona Grader" with structured rubric evaluation.
"""

import logging
from typing import Dict
import json
from openai import AsyncOpenAI

from utils.config import settings
from services.database import get_supabase_client

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    organization=settings.OPENAI_ORG_ID
)


GRADING_SYSTEM_PROMPT = """You are a Senior Mentor Hospitalist evaluating a colleague's clinical reasoning.

You grade based on the COMPLETE JOB DESCRIPTION of a hospitalist, not just medical accuracy:

1. CLINICAL ACCURACY (0-4 points)
   - Correct diagnosis and treatment per guidelines
   - Evidence-based decision making
   - Appropriate risk stratification

2. RISK ASSESSMENT (0-3 points)
   - Identifies potential complications
   - Considers contraindications
   - Appropriate safety measures

3. COMMUNICATION (0-2 points)
   - Clear explanation of reasoning
   - Addresses patient/family communication needs
   - Appropriate consultation planning

4. RESOURCE STEWARDSHIP (0-1 point)
   - Cost-effective approach
   - Appropriate discharge planning
   - Avoids unnecessary tests/interventions

CRITICAL RULE: Even if clinically correct, if the answer fails in risk assessment, communication, or efficiency, you must mark it down.

Your response MUST be valid JSON in this exact format:
{
  "clinical_accuracy_score": <0-4>,
  "risk_assessment_score": <0-3>,
  "communication_score": <0-2>,
  "efficiency_score": <0-1>,
  "total_score": <0-10>,
  "feedback": "<2-3 sentences explaining the scores>",
  "level_change": <-1, 0, or 1>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "areas_for_improvement": ["<area 1>", "<area 2>"]
}

The level_change should be:
- +1 if total_score >= 8.0 (excellent performance)
- -1 if total_score < 5.0 (needs review)
- 0 otherwise (adequate performance)
"""


async def grade_answer(
    question_id: str,
    user_id: str,
    user_answer: str
) -> Dict:
    """Grade a user's answer and update their mastery level"""
    
    logger.info(f"Grading answer for question {question_id}, user {user_id}")
    
    supabase = get_supabase_client()
    
    # Retrieve question context
    question_response = supabase.table('questions').select(
        'question_text, source_chunk_ids, document_id, difficulty_level'
    ).eq('id', question_id).execute()
    
    if not question_response.data:
        raise ValueError(f"Question {question_id} not found")
    
    question_data = question_response.data[0]
    
    # Retrieve source chunks
    chunk_ids = question_data['source_chunk_ids']
    chunks_response = supabase.table('document_chunks').select(
        'content, page_number'
    ).in_('id', chunk_ids).execute()
    
    guideline_context = "\n\n".join([
        f"[Page {c['page_number']}] {c['content']}"
        for c in chunks_response.data
    ])
    
    # Build grading prompt
    grading_prompt = f"""CLINICAL SCENARIO:
{question_data['question_text']}

USER'S ANSWER:
{user_answer}

GUIDELINE REFERENCE:
{guideline_context}

Evaluate this answer using the 4-domain rubric. Remember: clinical correctness alone is not enough.

Respond with JSON only, no additional text."""
    
    # Call OpenAI for grading
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": GRADING_SYSTEM_PROMPT},
                {"role": "user", "content": grading_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        ai_response = response.choices[0].message.content
        grading_result = json.loads(ai_response)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse grading JSON: {e}")
        raise ValueError("Grading system returned invalid format")
    except Exception as e:
        logger.error(f"OpenAI grading error: {e}")
        raise ValueError(f"Failed to grade answer: {str(e)}")
    
    # Validate scores
    grading_result = validate_scores(grading_result)
    
    # Get user's current level
    mastery_response = supabase.table('user_document_mastery').select(
        'current_level, questions_answered'
    ).eq('user_id', user_id).eq('document_id', question_data['document_id']).execute()
    
    if mastery_response.data:
        current_level = mastery_response.data[0]['current_level']
        questions_answered = mastery_response.data[0]['questions_answered']
    else:
        current_level = 1
        questions_answered = 0
    
    # Calculate level change
    level_change = calculate_level_change(
        grading_result['total_score'],
        current_level,
        questions_answered,
        grading_result['level_change']
    )
    
    new_level = max(1, min(5, current_level + level_change))
    
    # Store answer record
    answer_record = supabase.table('answers').insert({
        'question_id': question_id,
        'user_id': user_id,
        'answer_text': user_answer,
        'total_score': grading_result['total_score'],
        'clinical_accuracy_score': grading_result['clinical_accuracy_score'],
        'risk_assessment_score': grading_result['risk_assessment_score'],
        'communication_score': grading_result['communication_score'],
        'efficiency_score': grading_result['efficiency_score'],
        'ai_feedback': grading_result['feedback'],
        'ai_model_used': settings.OPENAI_MODEL,
        'level_before': current_level,
        'level_after': new_level,
        'level_change': level_change
    }).execute()
    
    # Update user mastery
    update_mastery(
        supabase, user_id, question_data['document_id'],
        grading_result, level_change, new_level
    )
    
    # Mark question as answered
    supabase.table('questions').update({'was_answered': True}).eq('id', question_id).execute()
    
    logger.info(f"Graded answer: {grading_result['total_score']}/10, level {current_level} → {new_level}")
    
    return {
        'answer_id': answer_record.data[0]['id'],
        'scores': {
            'clinical_accuracy': grading_result['clinical_accuracy_score'],
            'risk_assessment': grading_result['risk_assessment_score'],
            'communication': grading_result['communication_score'],
            'efficiency': grading_result['efficiency_score'],
            'total': grading_result['total_score']
        },
        'feedback': grading_result['feedback'],
        'strengths': grading_result.get('strengths', []),
        'areas_for_improvement': grading_result.get('areas_for_improvement', []),
        'level_change': {
            'before': current_level,
            'after': new_level,
            'change': level_change,
            'reason': get_level_change_message(level_change, grading_result['total_score'])
        },
        'guideline_references': [
            {'content': c['content'][:200], 'page': c['page_number']}
            for c in chunks_response.data
        ]
    }


def validate_scores(grading_result: Dict) -> Dict:
    """Ensure scores are within valid ranges"""
    grading_result['clinical_accuracy_score'] = max(0, min(4, grading_result.get('clinical_accuracy_score', 0)))
    grading_result['risk_assessment_score'] = max(0, min(3, grading_result.get('risk_assessment_score', 0)))
    grading_result['communication_score'] = max(0, min(2, grading_result.get('communication_score', 0)))
    grading_result['efficiency_score'] = max(0, min(1, grading_result.get('efficiency_score', 0)))
    
    calculated_total = (
        grading_result['clinical_accuracy_score'] +
        grading_result['risk_assessment_score'] +
        grading_result['communication_score'] +
        grading_result['efficiency_score']
    )
    
    grading_result['total_score'] = calculated_total
    grading_result['level_change'] = max(-1, min(1, grading_result.get('level_change', 0)))
    
    return grading_result


def calculate_level_change(
    current_score: float,
    current_level: int,
    questions_answered: int,
    raw_level_change: int
) -> int:
    """Calculate level change with consistency requirement"""
    
    consistency_requirement = {1: 1, 2: 2, 3: 3, 4: 3, 5: 5}
    required_questions = consistency_requirement.get(current_level, 3)
    
    if current_score < settings.LEVEL_DOWN_THRESHOLD:
        return -1
    
    if raw_level_change > 0:
        if questions_answered >= required_questions and current_score >= settings.LEVEL_UP_THRESHOLD:
            return 1
        else:
            return 0
    
    return 0


def update_mastery(supabase, user_id, document_id, grading_result, level_change, new_level):
    """Update user mastery record"""
    
    # Get current stats
    response = supabase.table('user_document_mastery').select('*').eq(
        'user_id', user_id
    ).eq('document_id', document_id).execute()
    
    if response.data:
        current = response.data[0]
        q_count = current['questions_answered']
        
        # Calculate new averages
        new_avg = ((current['avg_score'] * q_count) + grading_result['total_score']) / (q_count + 1)
        
        supabase.table('user_document_mastery').update({
            'current_level': new_level,
            'questions_answered': q_count + 1,
            'questions_correct': current['questions_correct'] + (1 if grading_result['total_score'] >= 7 else 0),
            'avg_score': new_avg,
            'last_active': 'now()'
        }).eq('user_id', user_id).eq('document_id', document_id).execute()


def get_level_change_message(level_change: int, score: float) -> str:
    """Generate user-friendly message"""
    if level_change > 0:
        return f"🎉 Excellent work! Score: {score:.1f}/10. You've advanced a level!"
    elif level_change < 0:
        return f"⚠️ Score: {score:.1f}/10. Let's review this topic before advancing."
    else:
        if score >= 7:
            return f"✓ Good work! Score: {score:.1f}/10. Keep practicing to advance."
        else:
            return f"Score: {score:.1f}/10. Review the feedback to improve."
