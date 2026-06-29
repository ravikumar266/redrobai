from typing import TypedDict, List, Dict, Any, Optional
from backend.models import (
    Candidate, 
    Job, 
    Evidence, 
    TechnicalEvaluation, 
    VerificationEvaluation, 
    JobMatchEvaluation, 
    Ranking
)

class GraphState(TypedDict):
    """
    TypedDict representing the shared workflow state.
    Strictly holds models and execution metadata.
    """
    # Inputs
    candidate_id: Optional[str]
    job_id: Optional[str]
    job_description: Optional[str]
    raw_resume_text: Optional[str]
    
    # Structured representations
    candidate: Optional[Candidate]
    job: Optional[Job]
    
    # Gathered and verified items
    evidence: Optional[List[Evidence]]
    
    # Evaluation outputs (populated by the parallel evaluator nodes)
    technical_evaluation: Optional[TechnicalEvaluation]
    verification_evaluation: Optional[VerificationEvaluation]
    job_match_evaluation: Optional[JobMatchEvaluation]
    
    # Consensus output
    ranking: Optional[Ranking]
    report_url: Optional[str]
    
    # Chat conversation history for query endpoints
    chat_history: List[Dict[str, str]]
    
    # Routing controller states
    next_action: str
    errors: List[str]
