import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from backend.graph.state import GraphState
from backend.config import settings
from backend.models import (
    Candidate, 
    Job, 
    Evidence, 
    TechnicalEvaluation, 
    VerificationEvaluation, 
    JobMatchEvaluation, 
    Ranking
)
from backend.services.llm import LLMService
from backend.prompts import (
    SUPERVISOR_PROMPT,
    PARSER_PROMPT,
    INTELLIGENCE_PROMPT,
    TOOL_ROUTER_PROMPT,
    EVIDENCE_BUILDER_PROMPT,
    TECHNICAL_EVALUATOR_PROMPT,
    VERIFICATION_EVALUATOR_PROMPT,
    JOB_MATCH_EVALUATOR_PROMPT,
    RECRUITER_CHAT_PROMPT
)

# Import our independent tools for registry/execution details
from backend.tools import (
    GitHubTool, DriveTool, WebsiteTool, YouTubeTool,
    SearchTool, PDFTool, OCRTool, CertificateTool,
    GoogleDocsTool, EmailTool
)

logger = logging.getLogger(__name__)

# ========================================================
# GRAPH NODES IMPLEMENTATION
# ========================================================

async def supervisor_node(state: GraphState) -> Dict[str, Any]:
    """
    Supervisor Node: Controls workflow transitions dynamically using an LLM.
    """
    logger.info("Supervisor Node: Evaluating graph state...")
    
    # Critical failure catch to prevent infinite recursion before hitting LLM
    if state.get("errors") and not state.get("candidate"):
        logger.error("Supervisor halted workflow due to critical initialization errors.")
        return {"next_action": "__end__"}
        
    try:
        from backend.models import SupervisorDecision
        import json
        
        # Prepare a compressed state summary for the LLM
        state_summary = {
            "has_raw_resume_text": bool(state.get("raw_resume_text")),
            "has_parsed_candidate": bool(state.get("candidate")),
            "has_evidence": bool(state.get("evidence")),
            "has_evaluations": bool(state.get("technical_evaluation")),
            "has_ranking": bool(state.get("ranking")),
            "has_report_url": bool(state.get("report_url")),
            "chat_history_length": len(state.get("chat_history") or []),
            "errors": state.get("errors", [])
        }
        
        prompt = SUPERVISOR_PROMPT + f"\n\nCurrent Graph State Summary:\n{json.dumps(state_summary, indent=2)}"
        decision = await LLMService.generate_structured(prompt, response_model=SupervisorDecision)
        
        logger.info(f"Supervisor Decision: {decision.next_action} (Reasoning: {decision.reasoning})")
        return {"next_action": decision.next_action}
    except Exception as e:
        logger.error(f"Supervisor failed to decide: {e}")
        # Fallback static routing if LLM fails
        if not state.get("candidate"): return {"next_action": "parse"}
        if state.get("evidence") is None: return {"next_action": "tools"}
        if not state.get("technical_evaluation"): return {"next_action": "evaluate"}
        if not state.get("ranking"): return {"next_action": "consensus"}
        if not state.get("report_url"): return {"next_action": "report_generator"}
        return {"next_action": "__end__"}


async def resume_parser_node(state: GraphState) -> Dict[str, Any]:
    """
    Resume Parser Node: Extracts structured candidate details from raw text.
    """
    logger.info("Resume Parser Node: Parsing resume text...")
    
    try:
        prompt = PARSER_PROMPT + "\n\nResume Text:\n" + state.get("raw_resume_text", "")
        candidate = await LLMService.generate_structured(prompt, response_model=Candidate)
        return {"candidate": candidate}
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        return {"errors": state.get("errors", []) + [f"Parse error: {e}"]}


async def resume_intelligence_node(state: GraphState) -> Dict[str, Any]:
    """
    Resume Intelligence Node: Analyzes resume text to discover entities and targets.
    """
    logger.info("Resume Intelligence Node: Extracting metadata and targets...")
    # Mock update to candidate structure or custom flags
    return {}


async def tool_router_node(state: GraphState) -> Dict[str, Any]:
    """
    Tool Router Node: Decides which independent tools are required to verify the profile.
    Only routing decisions are made here; it triggers the actual tool execution.
    """
    logger.info("Tool Router Node: Analyzing required tool verifications...")
    
    # Mock deciding which tools need execution based on candidate details
    # Returns tool tasks to run
    candidate = state.get("candidate")
    tools_to_run = []
    if candidate:
        if candidate.github_url:
            tools_to_run.append("GitHubTool")
        if candidate.portfolio_url:
            tools_to_run.append("WebsiteTool")
            
    # Stash tool routing decisions in state metadata
    return {"next_action": "execute_tools", "errors": []}


async def evidence_builder_node(state: GraphState) -> Dict[str, Any]:
    """
    Evidence Builder Node: Executes tools independently and gathers all outputs into Evidence items.
    Tools never call each other; they are triggered here and outputs are consolidated.
    """
    logger.info("Evidence Builder Node: Executing tools and compiling evidence...")
    
    evidence_list: List[Evidence] = []
    candidate = state.get("candidate")
    
    if candidate:
        # 1. Run GitHubTool independently with dynamic username parsing
        if candidate.github_url:
            try:
                git_tool = GitHubTool()
                username = candidate.github_url.rstrip("/").split("/")[-1] or "janedoe"
                git_result = await git_tool.run(username=username)
                evidence_list.append(Evidence(
                    evidence_type="GitHub",
                    source_url=candidate.github_url,
                    verification_status="verified_active",
                    content_summary=f"GitHub profile for {username} with {git_result.get('stars_count', 0)} stars.",
                    extracted_metadata=git_result
                ))
            except Exception as e:
                logger.warning(f"GitHubTool failed: {e}")
                evidence_list.append(Evidence(
                    evidence_type="GitHub",
                    source_url=candidate.github_url,
                    verification_status="failed",
                    content_summary=f"Failed to fetch GitHub profile: {e}",
                    extracted_metadata={}
                ))
            
        # 2. Run GoogleDocsTool if portfolio is hosted on Google Docs, else run WebsiteTool
        is_gdoc = candidate.portfolio_url and "docs.google.com" in candidate.portfolio_url
        
        if is_gdoc:
            try:
                doc_tool = GoogleDocsTool()
                doc_result = await doc_tool.run(doc_url=candidate.portfolio_url)
                if doc_result.get("success"):
                    evidence_list.append(Evidence(
                        evidence_type="DriveFile",
                        source_url=candidate.portfolio_url,
                        verification_status="verified_active",
                        content_summary=f"Google Doc parsed successfully. Length: {doc_result.get('text_length')} characters.",
                        extracted_metadata=doc_result
                    ))
            except Exception as e:
                logger.warning(f"GoogleDocsTool failed: {e}")
        elif candidate.portfolio_url:
            try:
                web_tool = WebsiteTool()
                web_result = await web_tool.run(url=candidate.portfolio_url)
                evidence_list.append(Evidence(
                    evidence_type="WebsiteContent",
                    source_url=candidate.portfolio_url,
                    verification_status="verified_active",
                    content_summary=web_result.get("title", "Website content"),
                    extracted_metadata={"text_preview": web_result.get("content", "")[:200]}
                ))
            except Exception as e:
                logger.warning(f"WebsiteTool failed: {e}")
                evidence_list.append(Evidence(
                    evidence_type="WebsiteContent",
                    source_url=candidate.portfolio_url,
                    verification_status="failed",
                    content_summary=f"Failed to fetch website: {e}",
                    extracted_metadata={}
                ))
            
        # 3. Process extra extracted URLs (from PDF annotations)
        if getattr(candidate, "extra_urls", None):
            for extra_url in candidate.extra_urls:
                # Skip already processed URLs
                if extra_url in [candidate.github_url, candidate.portfolio_url, candidate.linkedin_url]:
                    continue
                try:
                    web_tool = WebsiteTool()
                    web_result = await web_tool.run(url=extra_url)
                    status_code = web_result.get("status_code", 0)
                    evidence_list.append(Evidence(
                        evidence_type="WebsiteContent",
                        source_url=extra_url,
                        verification_status="verified_active" if status_code == 200 else "failed",
                        content_summary=web_result.get("title", "Extracted Link"),
                        extracted_metadata={"text_preview": web_result.get("raw_text", "")[:300]}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fetch extra URL {extra_url}: {e}")
                    evidence_list.append(Evidence(
                        evidence_type="WebsiteContent",
                        source_url=extra_url,
                        verification_status="failed",
                        content_summary=f"Failed to fetch URL: {e}",
                        extracted_metadata={}
                    ))
            
    return {"evidence": evidence_list}


# ========================================================
# PARALLEL EVALUATORS
# ========================================================

async def technical_evaluator_node(state: GraphState) -> Dict[str, Any]:
    """
    Technical Evaluator Node (Runs in Parallel):
    Acts like a Senior Software Engineer evaluating technical skills, depth, coding profiles, and open source contributions.
    """
    logger.info("Technical Evaluator Node: Commencing technical audit...")
    
    try:
        candidate_data = state.get("candidate").model_dump_json() if state.get("candidate") else "{}"
        evidence_data = [e.model_dump_json() for e in state.get("evidence", [])]
        
        prompt = f"{TECHNICAL_EVALUATOR_PROMPT}\n\nCandidate Profile:\n{candidate_data}\n\nEvidence:\n{evidence_data}"
        tech_eval = await LLMService.generate_structured(prompt, response_model=TechnicalEvaluation)
        return {"technical_evaluation": tech_eval}
    except Exception as e:
        logger.error(f"Failed to generate technical evaluation: {e}")
        return {"errors": state.get("errors", []) + [f"Tech eval error: {e}"]}


async def verification_evaluator_node(state: GraphState) -> Dict[str, Any]:
    """
    Verification Evaluator Node (Runs in Parallel):
    Acts like an Auditor checking timeline consistency, authenticity, certificate checks, and broken links.
    """
    logger.info("Verification Evaluator Node: Commencing compliance audit...")
    
    try:
        candidate_data = state.get("candidate").model_dump_json() if state.get("candidate") else "{}"
        evidence_data = [e.model_dump_json() for e in state.get("evidence", [])]
        
        prompt = f"{VERIFICATION_EVALUATOR_PROMPT}\n\nCandidate Profile:\n{candidate_data}\n\nEvidence:\n{evidence_data}"
        verif_eval = await LLMService.generate_structured(prompt, response_model=VerificationEvaluation)
        return {"verification_evaluation": verif_eval}
    except Exception as e:
        logger.error(f"Failed to generate verification evaluation: {e}")
        return {"errors": state.get("errors", []) + [f"Verif eval error: {e}"]}


async def job_matching_evaluator_node(state: GraphState) -> Dict[str, Any]:
    """
    Job Matching Evaluator Node (Runs in Parallel):
    Acts like a Hiring Manager mapping candidate details against job requirements and identifying skill gaps.
    """
    logger.info("Job Matching Evaluator Node: Commencing job alignment evaluation...")
    
    try:
        candidate_data = state.get("candidate").model_dump_json() if state.get("candidate") else "{}"
        evidence_data = [e.model_dump_json() for e in state.get("evidence", [])]
        job_description = state.get("job_description", "No job description provided.")
        
        prompt = f"{JOB_MATCH_EVALUATOR_PROMPT}\n\nCandidate Profile:\n{candidate_data}\n\nEvidence:\n{evidence_data}\n\nJob Description:\n{job_description}"
        match_eval = await LLMService.generate_structured(prompt, response_model=JobMatchEvaluation)
        return {"job_match_evaluation": match_eval}
    except Exception as e:
        logger.error(f"Failed to generate job match evaluation: {e}")
        return {"errors": state.get("errors", []) + [f"Match eval error: {e}"]}


# ========================================================
# DETERMINISTIC CONSENSUS NODE
# ========================================================

async def consensus_node(state: GraphState) -> Dict[str, Any]:
    """
    Consensus Ranking Node: Merges parallel evaluation outputs using pure Python deterministic logic.
    Does NOT call an LLM. Calculates Final Score, Rank Tier, Confidence, and Detailed Explanation.
    """
    logger.info("Consensus Node: Evaluating scores and tiering deterministically...")
    
    tech = state.get("technical_evaluation")
    verif = state.get("verification_evaluation")
    match = state.get("job_match_evaluation")
    
    if not tech or not verif or not match:
        logger.error("Consensus node missing parallel evaluations. Returning error state.")
        return {"errors": state.get("errors", []) + ["Consensus node requires outputs from all parallel evaluation nodes."]}

    # --- DETERMINISTIC SCORING ALGORITHM ---
    
    # 1. Technical Capability Score (0-100)
    # Based on count of strengths and verified projects
    tech_base = len(tech.technical_strengths) * 20.0  # e.g., 3 strengths * 20 = 60
    tech_project_bonus = len(tech.projects) * 10.0     # e.g., 1 project * 10 = 10
    tech_score = min(tech_base + tech_project_bonus, 100.0)

    # 2. Verification Trust Score (0-100)
    # Calculated from auditor's confidence score, penalized by broken links
    verif_base = verif.confidence_score * 100.0
    broken_link_penalty = len(verif.broken_links) * 10.0
    verif_score = max(0.0, min(verif_base - broken_link_penalty, 100.0))

    # 3. Job Match Alignment Score (0-100)
    # Percent of required skills matching the requirement
    total_req = len(match.required_skills_match)
    matched_req = sum(1 for item in match.required_skills_match if (item.get("matched", False) if isinstance(item, dict) else getattr(item, "matched", False)))
    match_score = (matched_req / total_req * 100.0) if total_req > 0 else 100.0

    # 4. Final Weighted Scoring
    # Architecture weights: Tech (40%), Match (40%), Verification Trust (20%)
    final_score = (tech_score * 0.4) + (match_score * 0.4) + (verif_score * 0.2)

    # Determine Rank Tier
    if final_score >= 85.0:
        tier = "Tier 1 - Strong Fit"
    elif final_score >= 65.0:
        tier = "Tier 2 - Good Fit"
    else:
        tier = "Tier 3 - Not Recommended"

    # Compute overall confidence (audited confidence)
    overall_confidence = verif.confidence_score

    reason = (
        f"Consensus Score: {final_score:.1f}/100.0. "
        f"Calculated deterministically as: "
        f"Technical Score = {tech_score:.1f} (Weight 40%), "
        f"Job Match Score = {match_score:.1f} (Weight 40%), "
        f"Verification Trust = {verif_score:.1f} (Weight 20%)."
    )

    ranking = Ranking(
        final_score=final_score,
        rank_tier=tier,
        confidence=overall_confidence,
        reason=reason
    )
    
    return {"ranking": ranking}


async def report_generator_node(state: GraphState) -> Dict[str, Any]:
    """
    Report Generator Node: Creates a formal Google Doc summarizing the evaluation.
    """
    logger.info("Report Generator Node: Creating Google Doc...")
    
    candidate = state.get("candidate")
    ranking = state.get("ranking")
    
    if candidate and ranking:
        try:
            from backend.tools.google_docs import GoogleDocsWriterTool
            tool = GoogleDocsWriterTool()
            
            # Use 0 if verification_evaluation is missing
            verif_eval = state.get("verification_evaluation")
            trust = (verif_eval.confidence_score * 100) if verif_eval else 0.0
            
            result = await tool.run(
                candidate_name=candidate.name,
                score=ranking.final_score,
                tier=ranking.rank_tier,
                trust=trust
            )
            
            if result.get("success") and result.get("report_url"):
                return {"report_url": result.get("report_url")}
        except Exception as e:
            logger.error(f"Report generator failed: {e}")
            
    return {"report_url": None}


async def email_sender_node(state: GraphState) -> Dict[str, Any]:
    """
    Email Sender Node: Notifies recruiter of the evaluation consensus.
    """
    logger.info("Email Sender Node: Sending evaluation consensus report...")
    
    candidate = state.get("candidate")
    ranking = state.get("ranking")
    report_url = state.get("report_url")

    
    if candidate and ranking:
        try:
            email_tool = EmailTool()
            subject = f"Candidate Evaluation Report: {candidate.name} - {ranking.rank_tier}"
            
            body = (
                f"Evaluation Consensus Report\n"
                f"===========================\n"
                f"Candidate Name: {candidate.name}\n"
                f"Email: {candidate.email}\n"
                f"Experience: {candidate.experience_years} years\n\n"
                f"Consensus Score: {ranking.final_score:.1f}/100.0\n"
                f"Rank Tier: {ranking.rank_tier}\n"
                f"Confidence: {ranking.confidence * 100:.1f}%\n\n"
                f"Full Google Docs Report: {report_url if report_url else 'Not available'}\n\n"
                f"Calculation Details:\n{ranking.reason}\n\n"
                f"This notification was automatically sent by the AI Recruitment OS."
            )
            
            target_email = candidate.email
            await email_tool.run(to_email=target_email, subject=subject, body=body)
        except Exception as e:
            logger.error(f"Failed in email_sender_node node execution: {e}")
            
    return {}


async def recruiter_chat_node(state: GraphState) -> Dict[str, Any]:
    """
    Recruiter Chat Node: Generates conversational answers to recruiter queries.
    Uses LLMService to construct responses using state facts.
    """
    logger.info("Recruiter Chat Node: Answering recruiter questions...")
    
    candidate = state.get("candidate")
    name = candidate.name if candidate else "the candidate"
    skills = ", ".join(candidate.skills) if candidate and candidate.skills else "their skills"
    
    context = (
        f"Candidate Profile: {candidate.model_dump() if candidate else None}\n"
        f"Evaluations: Tech: {state.get('technical_evaluation')}, "
        f"Verification: {state.get('verification_evaluation')}, "
        f"Match: {state.get('job_match_evaluation')}\n"
        f"Consensus Ranking: {state.get('ranking')}\n"
        f"Chat History: {state.get('chat_history')}"
    )
    
    from backend.models import AgentAction
    from backend.tools.email import EmailTool
    
    prompt = f"""{RECRUITER_CHAT_PROMPT}

Context:
{context}

You have access to the following tools:
1. 'EmailTool': Use this to send an email to the candidate (e.g. to schedule an interview or ask for more info). 
   Arguments required: "to_email", "subject", "body".

If the user asks you to email the candidate, output a JSON with tool_name="EmailTool" and the required tool_args. 
Otherwise, just output your conversational response in the 'reply' field.
"""
    
    updated_history = list(state.get("chat_history") or [])
    
    try:
        action = await LLMService.generate_structured(prompt, response_model=AgentAction)
        if action.tool_name == "EmailTool":
            tool = EmailTool()
            tool_args = action.tool_args or {}
            logger.info(f"Agent decided to use EmailTool with args: {tool_args}")
            
            result = await tool.run(
                to_email=tool_args.get("to_email", candidate.email if candidate else ""),
                subject=tool_args.get("subject", "Follow up regarding your application"),
                body=tool_args.get("body", "Hello, we would like to schedule an interview.")
            )
            reply = f"I have used the EmailTool. Status: {result.get('sent_status')}. Message: {result.get('message')}"
        else:
            reply = action.reply or "I couldn't process that request properly."
            
    except Exception as e:
        logger.warning(f"Agent tool execution failed: {e}")
        reply = f"Sorry, I encountered an error while processing your request: {e}"
        
    updated_history.append({"role": "assistant", "content": reply})
    return {"chat_history": updated_history}


# ========================================================
# GRAPH COMPILATION & ROUTING CONFIGURATION
# ========================================================

def supervisor_router(state: GraphState) -> str:
    """
    Evaluates Supervisor decision to route flow.
    Returns a single string node name. For parallel evaluation,
    routes to 'evaluators_fan_out' which has edges to all three evaluators.
    """
    action = state.get("next_action")
    if action in ["parse", "resume_parser"]:
        return "resume_parser"
    elif action in ["tools", "tool_router", "evidence_builder"]:
        return "tool_router"
    elif action in ["evaluate", "evaluators", "evaluators_fan_out"]:
        return "evaluators_fan_out"
    elif action == "consensus":
        return "consensus"
    elif action == "report_generator":
        return "report_generator"
    elif action == "recruiter_chat":
        return "recruiter_chat"
    else:
        return "__end__"


async def evaluators_fan_out_node(state: GraphState) -> Dict[str, Any]:
    """
    Fan-out node: Runs all three evaluator nodes concurrently using asyncio.
    Collects their results and merges them into a single state update.
    """
    import asyncio
    logger.info("Evaluators Fan-Out: Running all three evaluators concurrently...")

    tech_task = technical_evaluator_node(state)
    verif_task = verification_evaluator_node(state)
    match_task = job_matching_evaluator_node(state)

    tech_result, verif_result, match_result = await asyncio.gather(tech_task, verif_task, match_task)

    # Merge all three results into one state update
    merged = {}
    merged.update(tech_result)
    merged.update(verif_result)
    merged.update(match_result)
    return merged

# Initialize the StateGraph
workflow = StateGraph(GraphState)

# Add Node implementations
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("resume_parser", resume_parser_node)
workflow.add_node("resume_intelligence", resume_intelligence_node)
workflow.add_node("tool_router", tool_router_node)
workflow.add_node("evidence_builder", evidence_builder_node)
workflow.add_node("evaluators_fan_out", evaluators_fan_out_node)
workflow.add_node("consensus", consensus_node)
workflow.add_node("report_generator", report_generator_node)
workflow.add_node("email_sender", email_sender_node)
workflow.add_node("recruiter_chat", recruiter_chat_node)

# Set Entrypoint
workflow.set_entry_point("supervisor")

# Configure Supervisor Routing (every return value maps to exactly one node)
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "resume_parser": "resume_parser",
        "tool_router": "tool_router",
        "evaluators_fan_out": "evaluators_fan_out",
        "consensus": "consensus",
        "report_generator": "report_generator",
        "recruiter_chat": "recruiter_chat",
        "__end__": END
    }
)

# Linear parsing: resume_parser -> resume_intelligence -> supervisor
workflow.add_edge("resume_parser", "resume_intelligence")
workflow.add_edge("resume_intelligence", "supervisor")

# Tool verification: tool_router -> evidence_builder -> supervisor
workflow.add_edge("tool_router", "evidence_builder")
workflow.add_edge("evidence_builder", "supervisor")

# Evaluation: evaluators_fan_out -> consensus -> report_generator -> email_sender -> supervisor
workflow.add_edge("evaluators_fan_out", "consensus")
workflow.add_edge("consensus", "report_generator")
workflow.add_edge("report_generator", "email_sender")
workflow.add_edge("email_sender", "supervisor")

# Chat: recruiter_chat -> supervisor
workflow.add_edge("recruiter_chat", "supervisor")

# Compile the graph into a runnable application
app_graph = workflow.compile()
