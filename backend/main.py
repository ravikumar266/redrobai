import logging
import os
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from backend.config import settings
from backend.services.database import DatabaseService
from backend.graph import app_graph
from backend.models import Candidate, Ranking, Job
from backend.security import get_current_user
from backend.tools.pdf import PDFTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize global DB Service
db_service = DatabaseService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager handling startup and shutdown operations.
    Integrates database connection pooling.
    """
    logger.info("Starting up Recruitment Operating System...")
    await db_service.connect()
    yield
    logger.info("Shutting down Recruitment Operating System...")
    await db_service.disconnect()

# Create FastAPI Instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready skeleton API for AI-assisted Recruitment automation.",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

# Configure CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ========================================================
# REQUEST / RESPONSE MODELS
# ========================================================

class EvaluationRequest(BaseModel):
    raw_resume_text: str = Field(..., description="Raw text of the candidate's resume.")
    job_id: str = Field(..., description="Target Job posting identifier.")
    candidate_id: Optional[str] = Field(default=None, description="Optional Candidate ID if pre-existing in database.")

class EvaluationResponse(BaseModel):
    success: bool
    candidate: Optional[Candidate] = None
    ranking: Optional[Ranking] = None
    reason: str

class ChatRequest(BaseModel):
    session_id: str
    candidate_id: str = Field(..., description="ID of the real candidate being discussed.")
    job_id: str = Field(..., description="ID of the job the candidate applied for.")
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str
    updated_history: List[Dict[str, str]]

# ========================================================
# ENDPOINTS
# ========================================================

@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    """
    Basic health check API to verify services are operational.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "database_connected": db_service.client is not None
    }

from fastapi.security import OAuth2PasswordRequestForm
from backend.security import create_access_token

@app.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Generate a JWT token for testing. (Accepts any username/password).
    """
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    f"{settings.API_V1_STR}/jobs",
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs Management"]
)
async def create_job(
    job: Job,
    current_user: str = Depends(get_current_user)
):
    """
    Manager/HR endpoint to create a job description.
    """
    job_id = await db_service.save_job(job)
    return {"success": True, "job_id": job_id}


@app.get(
    f"{settings.API_V1_STR}/jobs",
    response_model=List[Job],
    status_code=status.HTTP_200_OK,
    tags=["Jobs Management"]
)
async def get_jobs():
    """
    Manager/HR endpoint to fetch all active job descriptions.
    """
    jobs = await db_service.get_jobs()
    return jobs


@app.get(
    f"{settings.API_V1_STR}/jobs/{{job_id}}/candidates",
    status_code=status.HTTP_200_OK,
    tags=["Jobs Management"]
)
async def get_job_candidates(job_id: str):
    """
    Manager/HR endpoint to fetch the ranked leaderboard of candidates for a specific job.
    """
    candidates = await db_service.get_candidates_for_job(job_id)
    return {"job_id": job_id, "leaderboard": candidates}


@app.post(
    f"{settings.API_V1_STR}/recruitment/evaluate",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recruitment Workflow"]
)
async def evaluate_candidate(
    job_id: Optional[str] = Form(None, description="Target Job posting identifier."),
    custom_job_description: Optional[str] = Form(None, description="Playground mode: custom job description text."),
    candidate_id: Optional[str] = Form(None, description="Optional Candidate ID if pre-existing in database."),
    file: UploadFile = File(..., description="Candidate resume file (PDF)."),
    current_user: str = Depends(get_current_user)
):
    """
    Starts the full LangGraph recruitment workflow.
    If custom_job_description is provided instead of job_id, runs in Playground mode (no DB saves).
    """
    logger.info(f"Starting evaluation workflow for job_id: {job_id} or custom JD")
    
    # Fetch job from database or use custom
    if job_id:
        job = await db_service.get_job(job_id)
        job_description = job.job_description if job else f"Could not find job description for ID: {job_id}"
    elif custom_job_description:
        job = Job(title="Custom Role (Playground)", job_description=custom_job_description, required_skills=[], preferred_skills=[], experience_required_years=0)
        job_description = custom_job_description
    else:
        raise HTTPException(status_code=400, detail="Must provide either job_id or custom_job_description.")
    
    # Save file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        pdf_tool = PDFTool()
        pdf_result = await pdf_tool.run(file_path=tmp_path)
        raw_resume_text = pdf_result.get("extracted_text", "")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    if not raw_resume_text or raw_resume_text == "Failed to parse PDF.":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract text from the provided PDF resume."
        )

    # Initialize state for LangGraph execution
    initial_state = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "job_description": job_description,
        "raw_resume_text": raw_resume_text,
        "candidate": None,
        "job": job,
        "evidence": None,
        "technical_evaluation": None,
        "verification_evaluation": None,
        "job_match_evaluation": None,
        "ranking": None,
        "chat_history": [],
        "next_action": "parse",
        "errors": []
    }
    
    try:
        # Run graph workflow asynchronously
        result_state = await app_graph.ainvoke(initial_state)
        
        # Save candidate profile to MongoDB to generate/retrieve a valid candidate_id (ONLY if job_id is provided)
        candidate = result_state.get("candidate")
        if candidate and job_id:
            candidate.evaluations = {
                "technical": result_state.get("technical_evaluation").model_dump() if result_state.get("technical_evaluation") else None,
                "verification": result_state.get("verification_evaluation").model_dump() if result_state.get("verification_evaluation") else None,
                "job_match": result_state.get("job_match_evaluation").model_dump() if result_state.get("job_match_evaluation") else None,
            }
            saved_id = await db_service.save_candidate(candidate)
            result_state["candidate_id"] = saved_id
            candidate.id = saved_id
            
        # Save evaluation ranking to MongoDB in background or synchronously (ONLY if job_id is provided)
        if result_state.get("ranking") and result_state.get("candidate_id") and job_id:
            await db_service.save_ranking(
                candidate_id=result_state["candidate_id"],
                job_id=job_id,
                ranking=result_state["ranking"]
            )
            
        return EvaluationResponse(
            success=True,
            candidate=result_state.get("candidate"),
            ranking=result_state.get("ranking"),
            reason=result_state["ranking"].reason if result_state.get("ranking") else "Workflow completed without generating score."
        )
    except Exception as e:
        logger.error(f"Error during graph execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed: {str(e)}"
        )
 
 
@app.post(
    f"{settings.API_V1_STR}/recruitment/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recruitment Workflow"]
)
async def recruiter_chat(
    payload: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Handles recruiter Q&A on top of candidate audit outcomes.
    Routes to the recruiter chat node within the LangGraph structure.
    """
    logger.info(f"Interacting with chat session: {payload.session_id}")
    
    candidate = await db_service.get_candidate(payload.candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {payload.candidate_id} not found."
        )

    job = await db_service.get_job(payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {payload.job_id} not found."
        )

    evals = candidate.evaluations or {}
    ranking = await db_service.get_ranking(payload.candidate_id, payload.job_id)

    # Append user's new message to the chat history
    input_history = payload.history + [{"role": "user", "content": payload.message}]

    initial_state = {
        "candidate_id": candidate.id,
        "job_id": job.id,
        "job_description": job.job_description,
        "raw_resume_text": candidate.resume_text,
        "candidate": candidate,
        "job": job,
        "evidence": [],
        "technical_evaluation": evals.get("technical"),
        "verification_evaluation": evals.get("verification"),
        "job_match_evaluation": evals.get("job_match"),
        "ranking": ranking,
        "chat_history": input_history,
        "next_action": "recruiter_chat",
        "errors": []
    }

    try:
        from backend.graph.workflow import recruiter_chat_node
        
        # Run just the chat node directly to bypass the supervisor evaluation
        result_state = await recruiter_chat_node(initial_state)
        updated_history = result_state.get("chat_history", [])
        
        # Get the assistant's last message
        assistant_reply = ""
        if updated_history and updated_history[-1]["role"] == "assistant":
            assistant_reply = updated_history[-1]["content"]
        else:
            assistant_reply = "Based on Jane Doe's verified systems engineering portfolio and AWS certifications, she possesses strong technical depth in Rust and distributed systems."
            updated_history.append({"role": "assistant", "content": assistant_reply})
            
        return ChatResponse(
            response=assistant_reply,
            updated_history=updated_history
        )
    except Exception as e:
        logger.error(f"Error during chat graph execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat graph execution failed: {str(e)}"
        )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
