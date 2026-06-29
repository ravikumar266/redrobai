import sys
import logging

# Configure basic console log output
logging.basicConfig(level=logging.INFO)

print("="*60)
print("STARTING SYSTEM SKELETON VERIFICATION")
print("="*60)

try:
    print("[1/4] Importing FastAPI configurations and Main entrypoint...")
    from backend.main import app
    print("      SUCCESS: main.py imported successfully.")

    print("[2/4] Importing Pydantic Models...")
    from backend.models import (
        Candidate, Job, Evidence, TechnicalEvaluation, 
        VerificationEvaluation, JobMatchEvaluation, Ranking
    )
    print("      SUCCESS: models.py imported successfully.")

    print("[3/4] Importing Services and Tools...")
    from backend.services import DatabaseService, LLMService
    from backend.tools import (
        GitHubTool, DriveTool, WebsiteTool, YouTubeTool,
        SearchTool, PDFTool, OCRTool, CertificateTool
    )
    print("      SUCCESS: Services and Tools imported successfully.")

    print("[4/4] Importing and Verifying LangGraph workflow...")
    from backend.graph import app_graph
    print("      SUCCESS: LangGraph workflow compiled and imported.")

    print("\n" + "="*60)
    print("VERIFIED LANGGRAPH CONNECTIVITY GRAPH")
    print("="*60)
    
    # Render ASCII graph structure to standard out to verify connections
    app_graph.get_graph().print_ascii()
    
    print("\n" + "="*60)
    print("SYSTEM VERIFICATION PASSED SUCCESSFULLY!")
    print("="*60)
    
except Exception as e:
    print(f"\nERROR: Verification failed with error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
