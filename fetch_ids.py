import asyncio
from backend.services.database import DatabaseService

async def get_latest_ids():
    db = DatabaseService()
    await db.connect()
    
    jobs = await db.db.jobs.find().sort([('_id', -1)]).limit(1).to_list(1)
    cands = await db.db.candidates.find().sort([('_id', -1)]).limit(1).to_list(1)
    
    print("----- DATABASE RESULTS -----")
    print("JOB_ID:", str(jobs[0]['_id']) if jobs else None)
    print("CANDIDATE_ID:", str(cands[0]['_id']) if cands else None)
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(get_latest_ids())
