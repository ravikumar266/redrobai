import logging
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from backend.config import settings
from backend.models import Candidate, Job, Evidence, Ranking

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service layer class handling all database interactions with MongoDB.
    Uses 'motor' for asynchronous driver capabilities.
    """
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self) -> None:
        """
        Establishes connection to the MongoDB server using configured URI.
        """
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DB_NAME]
            logger.info(f"Database connection to database '{settings.MONGODB_DB_NAME}' established.")
            await self._ensure_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.db = None

    async def _ensure_indexes(self) -> None:
        """Create required indexes if they do not exist."""
        if self.db is not None:
            try:
                # Candidates: Unique index on email
                await self.db.candidates.create_index("email", unique=True)
                # Rankings: Compound unique index on candidate_id and job_id
                await self.db.rankings.create_index(
                    [("candidate_id", 1), ("job_id", 1)], unique=True
                )
                logger.info("MongoDB indexes verified.")
            except Exception as e:
                logger.error(f"Error creating indexes: {e}")

    async def disconnect(self) -> None:
        """
        Gracefully closes the database connection.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """
        Fetch a candidate record by its unique ID.
        """
        logger.debug(f"Fetching candidate {candidate_id}")
        if self.db is not None:
            try:
                query = {"_id": ObjectId(candidate_id) if ObjectId.is_valid(candidate_id) else candidate_id}
                doc = await self.db.candidates.find_one(query)
                if doc:
                    doc["id"] = str(doc["_id"])
                    return Candidate(**doc)
            except Exception as e:
                logger.error(f"Error fetching candidate {candidate_id}: {e}")
        return None

    async def save_candidate(self, candidate: Candidate) -> str:
        """
        Insert or update a candidate record in the database.
        """
        logger.debug(f"Saving candidate {candidate.name}")
        if self.db is not None:
            try:
                candidate_data = candidate.model_dump(exclude={"id"})
                if candidate.id:
                    query = {"_id": ObjectId(candidate.id) if ObjectId.is_valid(candidate.id) else candidate.id}
                    await self.db.candidates.replace_one(query, candidate_data, upsert=True)
                    return candidate.id
                else:
                    if candidate_data.get("email"):
                        query = {"email": candidate_data["email"]}
                        result = await self.db.candidates.update_one(query, {"$set": candidate_data}, upsert=True)
                        if result.upserted_id:
                            return str(result.upserted_id)
                        else:
                            existing = await self.db.candidates.find_one(query)
                            return str(existing["_id"]) if existing else "mock_candidate_id"
                    else:
                        result = await self.db.candidates.insert_one(candidate_data)
                        return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Error saving candidate: {e}")
        return "mock_candidate_id"

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Fetch a job description by ID.
        """
        logger.debug(f"Fetching job {job_id}")
        if self.db is not None:
            try:
                query = {"_id": ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id}
                doc = await self.db.jobs.find_one(query)
                if doc:
                    doc["id"] = str(doc["_id"])
                    return Job(**doc)
            except Exception as e:
                logger.error(f"Error fetching job {job_id}: {e}")
        return None

    async def get_jobs(self) -> List[Job]:
        """
        Fetch all job records.
        """
        logger.debug("Fetching all jobs")
        jobs = []
        if self.db is not None:
            try:
                cursor = self.db.jobs.find({})
                async for doc in cursor:
                    doc["id"] = str(doc["_id"])
                    jobs.append(Job(**doc))
            except Exception as e:
                logger.error(f"Error fetching jobs: {e}")
        return jobs

    async def save_job(self, job: Job) -> str:
        """
        Insert or update a job record in the database.
        """
        logger.debug(f"Saving job {job.title}")
        if self.db is not None:
            try:
                job_data = job.model_dump(exclude={"id"})
                if job.id:
                    query = {"_id": ObjectId(job.id) if ObjectId.is_valid(job.id) else job.id}
                    await self.db.jobs.replace_one(query, job_data, upsert=True)
                    return job.id
                else:
                    result = await self.db.jobs.insert_one(job_data)
                    return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Error saving job: {e}")
        return "mock_job_id"

    async def save_evidence(self, evidence: Evidence) -> str:
        """
        Insert or update an evidence record.
        """
        logger.debug(f"Saving evidence type: {evidence.evidence_type}")
        if self.db is not None:
            try:
                evidence_data = evidence.model_dump(exclude={"id"})
                if evidence.id:
                    query = {"_id": ObjectId(evidence.id) if ObjectId.is_valid(evidence.id) else evidence.id}
                    await self.db.evidence.replace_one(query, evidence_data, upsert=True)
                    return evidence.id
                else:
                    result = await self.db.evidence.insert_one(evidence_data)
                    return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Error saving evidence: {e}")
        return "mock_evidence_id"

    async def save_ranking(self, candidate_id: str, job_id: str, ranking: Ranking) -> bool:
        """
        Save the final consensus score and ranking for a candidate matching a job.
        """
        logger.debug(f"Saving ranking for candidate {candidate_id} and job {job_id}")
        if self.db is not None:
            try:
                ranking_data = {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "ranking": ranking.model_dump()
                }
                await self.db.rankings.update_one(
                    {"candidate_id": candidate_id, "job_id": job_id},
                    {"$set": ranking_data},
                    upsert=True
                )
                return True
            except Exception as e:
                logger.error(f"Error saving ranking: {e}")
                return False
        return True

    async def get_ranking(self, candidate_id: str, job_id: str) -> Optional[Ranking]:
        """
        Fetch the ranking for a specific candidate and job.
        """
        if self.db is not None:
            try:
                doc = await self.db.rankings.find_one({"candidate_id": candidate_id, "job_id": job_id})
                if doc and "ranking" in doc:
                    return Ranking(**doc["ranking"])
            except Exception as e:
                logger.error(f"Error fetching ranking: {e}")
        return None

    async def get_candidates_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all rankings for a given job and join with candidate info.
        """
        logger.debug(f"Fetching candidates for job {job_id}")
        results = []
        if self.db is not None:
            try:
                cursor = self.db.rankings.find({"job_id": job_id})
                async for ranking_doc in cursor:
                    candidate_id = ranking_doc.get("candidate_id")
                    if candidate_id:
                        candidate_doc = await self.db.candidates.find_one({"_id": ObjectId(candidate_id) if ObjectId.is_valid(candidate_id) else candidate_id})
                        if candidate_doc:
                            candidate_doc["id"] = str(candidate_doc["_id"])
                            results.append({
                                "candidate": Candidate(**candidate_doc).model_dump(mode='json'),
                                "ranking": ranking_doc.get("ranking", {})
                            })
            except Exception as e:
                logger.error(f"Error fetching candidates for job {job_id}: {e}")
        # Sort by final_score descending
        results.sort(key=lambda x: x.get("ranking", {}).get("final_score", 0), reverse=True)
        return results

