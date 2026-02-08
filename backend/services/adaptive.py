"""
Adaptive Question Generation Service (Engine A)
================================================
Implements the 5-level difficulty system with targeted chunk retrieval.
"""

import logging
from typing import List, Dict, Optional
import random
from openai import AsyncOpenAI

from utils.config import settings
from utils.embedding import create_embedding
from services.database import get_supabase_client

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    organization=settings.OPENAI_ORG_ID
)


# Level-specific prompt templates
LEVEL_PROMPTS = {
    1: """You are creating a clinical scenario for a NOVICE hospitalist.

DIFFICULTY: Level 1 - Basic Protocol
GOAL: Test recall of standard guidelines

Based on this guideline excerpt:
{context}

Generate:
1. A 2-sentence clinical vignette describing a straightforward case
2. A BINARY question (Yes/No or True/False)
3. The correct answer with a brief explanation

FORMAT:
Vignette: [2 sentences]
Question: [Binary question]
Answer: [Yes/No]
Explanation: [1-2 sentences citing the guideline]

REQUIREMENTS:
- No distracting variables
- Clear-cut scenario that follows standard protocol
- Answer should be obvious from the guideline""",

    2: """You are creating a clinical scenario for a BEGINNER hospitalist.

DIFFICULTY: Level 2 - Basic Application
GOAL: Test understanding of first-line management

Based on this guideline excerpt:
{context}

Generate:
1. A 2-3 sentence clinical vignette
2. A multiple-choice question about the NEXT STEP
3. 4 answer choices (A, B, C, D) with one clearly correct

FORMAT:
Vignette: [2-3 sentences]
Question: What is the most appropriate next step?
A) [Option 1]
B) [Option 2]
C) [Option 3]
D) [Option 4]
Answer: [Letter]
Explanation: [2-3 sentences citing the guideline]""",

    3: """You are creating a clinical scenario for a PROFICIENT hospitalist.

DIFFICULTY: Level 3 - Intermediate Complexity
GOAL: Test reasoning with distracting information

Based on this guideline excerpt:
{context}

Generate:
1. A 3-4 sentence clinical vignette with ONE distracting finding
2. A question requiring analysis of which factor matters
3. A detailed explanation

FORMAT:
Vignette: [3-4 sentences including a red herring]
Question: [What is the most important factor in management?]
Answer: [Your reasoning]
Explanation: [3-4 sentences explaining why the distractor is irrelevant]""",

    4: """You are creating a clinical scenario for an ADVANCED hospitalist.

DIFFICULTY: Level 4 - Grey Zone
GOAL: Test judgment in scenarios with multiple defensible approaches

Based on this guideline excerpt:
{context}

Generate:
1. A 4-5 sentence complex vignette where 2 approaches are both reasonable
2. Ask which approach is PREFERRED according to the guideline
3. Explain the nuance

FORMAT:
Vignette: [4-5 sentences with competing considerations]
Question: Which management approach is preferred?
Option A: [First approach]
Option B: [Second approach]
Answer: [A or B]
Explanation: [Explain why one is preferred, acknowledging the other is defensible]""",

    5: """You are creating a clinical scenario for an EXPERT hospitalist.

DIFFICULTY: Level 5 - Exception Handling
GOAL: Test recognition of when standard protocol is risky

Based on this guideline excerpt (especially EXCEPTIONS and CONTRAINDICATIONS):
{context}

Generate:
1. A complex vignette where following standard protocol would be HARMFUL
2. Ask the learner to identify the risk
3. Explain the exception

FORMAT:
Vignette: [5-6 sentences with a subtle contraindication or exception]
Question: Why would the standard approach be problematic in this case?
Answer: [The key exception/contraindication]
Explanation: [Quote the specific warning from the guideline]

REQUIREMENTS:
- The standard answer should seem correct at first
- Include a subtle detail that makes it contraindicated
- MUST cite a specific exception, contraindication, or warning from the text"""
}


async def retrieve_chunks_for_level(
    document_id: int,
    level: int,
    topic_query: Optional[str] = None
) -> List[Dict]:
    """Retrieve document chunks targeted to the difficulty level"""
    
    supabase = get_supabase_client()
    
    # Determine chunk type filter based on level
    chunk_type_filter = None
    if level >= 4:
        # Advanced/Expert: prioritize exceptions and contraindications
        chunk_type_filter = ["exception", "contraindication"]
    elif level == 3:
        # Proficient: mix of standard and special cases
        chunk_type_filter = ["standard", "special_population"]
    else:
        # Novice/Beginner: only standard chunks
        chunk_type_filter = ["standard"]
    
    # Query chunks
    query = supabase.table('document_chunks').select('*').eq('document_id', document_id)
    
    if chunk_type_filter:
        query = query.in_('chunk_type', chunk_type_filter)
    
    response = query.limit(settings.TOP_K_RETRIEVAL * 3).execute()
    chunks = response.data
    
    if not chunks:
        # Fallback: get any chunks
        response = supabase.table('document_chunks').select('*').eq(
            'document_id', document_id
        ).limit(settings.TOP_K_RETRIEVAL).execute()
        chunks = response.data
    
    # Select final chunks
    final_chunks = random.sample(chunks, min(settings.TOP_K_RETRIEVAL, len(chunks)))
    
    logger.info(f"Retrieved {len(final_chunks)} chunks for level {level}")
    
    return final_chunks


async def
