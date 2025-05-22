import re
import string
import logging
from sqlalchemy.orm import Session

from app.models.claimant import SQLClaimant, SQLClaimantDocument # Assuming SQLClaimant is the one with relationships
from app.models.job_posting import SQLJobPosting
from app.models.matched_job import MatchedJobCreate
from app.db.crud_matched_jobs import create_matched_job
from app.db.crud_claimant import get_claimant # Using existing get_claimant
from app.db.crud_jobs import get_job_postings

logger = logging.getLogger(__name__)

DEFAULT_STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "can", "could", "may", "might", "must", "and", "but", "or", "nor",
    "for", "so", "yet", "in", "on", "at", "by", "from", "to", "with",
    "about", "above", "after", "again", "against", "all", "am", "as",
    "because", "before", "below", "between", "both", "during", "each",
    "few", "further", "here", "how", "i", "if", "into", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "not", "now", "of",
    "off", "once", "only", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "he", "they", "them", "their", "theirs", "themselves",
    "then", "there", "these", "this", "those", "through", "too", "under", "until",
    "up", "very", "we", "what", "when", "where", "which", "while", "who", "whom",
    "why", "you", "your", "yours", "yourself", "yourselves", "cv", "resume",
    # Added more common job-related but often noisy words
    "job", "role", "opportunity", "company", "experience", "work", "skills",
    "required", "responsibilities", "duties", "salary", "location", "contract",
    "permanent", "temporary", "full-time", "part-time", "london", "uk", "remote" 
    # Consider context: "london" is a stop word here, but might be a target location.
    # For keyword extraction from CV/Job, it's okay to remove generic location mentions if we do separate location matching.
])

def extract_keywords_from_text(text: str) -> set[str]:
    """
    Extracts a set of unique keywords from a given text string.
    Keywords are lowercased, punctuation is removed, and stop words are filtered out.
    """
    if not text:
        return set()

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    # Using regex to keep alphanumeric and spaces, then split. Handles hyphens better.
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text) # Replace punctuation with space
    
    words = text.split()
    
    # Filter out stop words and short words
    keywords = {
        word for word in words 
        if word not in DEFAULT_STOP_WORDS and len(word) >= 3
    }
    
    return keywords

def match_jobs_for_claimant(db: Session, claimant_id: int) -> list[SQLMatchedJob]:
    """
    Matches a claimant to available job postings based on CV keywords and job descriptions.
    """
    logger.info(f"Starting job matching process for claimant ID: {claimant_id}")

    claimant = get_claimant(db=db, claimant_id=claimant_id)
    if not claimant:
        logger.warning(f"Claimant with ID {claimant_id} not found. Cannot perform matching.")
        return []

    # Aggregate CV Text
    cv_text = ""
    if claimant.documents: # Accessing the relationship
        for doc in claimant.documents:
            if doc.document_type and doc.document_type.lower() == 'cv' and doc.raw_text_content:
                cv_text += " " + doc.raw_text_content
    
    cv_text = cv_text.strip()
    
    cv_keywords = set()
    if cv_text:
        cv_keywords = extract_keywords_from_text(cv_text)
        logger.info(f"Extracted {len(cv_keywords)} keywords from CV for claimant ID: {claimant_id}. Sample: {list(cv_keywords)[:10]}")
    else:
        logger.info(f"No CV text found for claimant ID: {claimant_id}. Proceeding with explicit keywords if available.")

    # Keyword Enhancement: Incorporate explicit keywords from claimant profile
    claimant_target_location = claimant.target_location
    claimant_explicit_keywords_str = claimant.search_keywords
    
    explicit_keyword_set = set()
    if claimant_explicit_keywords_str:
        explicit_keyword_set = set([kw.strip().lower() for kw in claimant_explicit_keywords_str.split(',') if kw.strip()])
        logger.info(f"Found {len(explicit_keyword_set)} explicit keywords for claimant ID: {claimant_id}. Sample: {list(explicit_keyword_set)[:10]}")

    final_claimant_keywords = cv_keywords.union(explicit_keyword_set)

    if not final_claimant_keywords:
        logger.info(f"No keywords (CV or explicit) available for claimant ID: {claimant_id}. No keyword-based matching possible.")
        # Depending on desired behavior, could still proceed if location matching is primary,
        # but for now, if no keywords, no match.
        return []
    
    logger.info(f"Total unique keywords for matching for claimant ID {claimant_id}: {len(final_claimant_keywords)}. Sample: {list(final_claimant_keywords)[:10]}")


    # Fetch all active job postings (assuming is_active=True is default or handled by get_job_postings)
    # A more optimized query would filter for active jobs if the flag is reliably set and used.
    # For now, get_job_postings fetches all. We might need to add an active filter there.
    all_jobs = get_job_postings(db=db, limit=10000) # High limit to get most jobs
    logger.info(f"Fetched {len(all_jobs)} total job postings for potential matching against claimant ID: {claimant_id}")

    created_matches = []
    for job in all_jobs:
        if not job.is_active: # Explicitly skip inactive jobs if not filtered by DB query
            # logger.debug(f"Skipping inactive job ID: {job.id} - '{job.title}'")
            continue

        # Location Matching Logic
        if claimant_target_location:
            job_location_lower = (job.location or "").lower()
            # Simple substring check. Could be enhanced (e.g., city matching, postcode proximity)
            if claimant_target_location.lower() not in job_location_lower:
                # logger.debug(f"Skipping job ID {job.id} ('{job.title}') due to location mismatch. Claimant target: '{claimant_target_location}', Job location: '{job.location}'")
                continue # Skip this job if location doesn't match

        job_text_for_matching = (job.title + " " + (job.description or "")).lower() # Ensure description is not None
        job_keywords = extract_keywords_from_text(job_text_for_matching)

        common_keywords = final_claimant_keywords.intersection(job_keywords)
        score = len(common_keywords)

        # Match threshold - adjust as needed
        MIN_MATCH_SCORE = 2 
        if score >= MIN_MATCH_SCORE:
            notes = f"Automatic match. Score: {score}. Common keywords: {', '.join(list(common_keywords)[:5])}..."
            if claimant_target_location:
                notes += f" Location matched: '{claimant_target_location}'."
            
            logger.info(f"Match found for Claimant ID {claimant_id} and Job ID {job.id} ('{job.title}') with score: {score}. Common: {list(common_keywords)}")
            match_data = MatchedJobCreate(
                claimant_id=claimant_id,
                job_posting_id=job.id,
                match_score=float(score),
                status='new', # Default status
                notes_for_advisor=notes
            )
            try:
                # create_matched_job handles duplicates by updating
                new_or_updated_match = create_matched_job(db=db, match=match_data)
                created_matches.append(new_or_updated_match)
            except Exception as e:
                logger.error(f"Error creating/updating matched job for Claimant ID {claimant_id}, Job ID {job.id}: {e}", exc_info=True)
        # else:
            # logger.debug(f"No significant match (score {score} < {MIN_MATCH_SCORE}) for Claimant {claimant_id} and Job {job.id} ('{job.title}')")


    logger.info(f"Completed matching for claimant ID: {claimant_id}. Found/Updated {len(created_matches)} matches.")
    return created_matches

# Example of how to test this service (simplified, ideally in a test file)
if __name__ == "__main__":
    # This requires a DB session and data.
    # For standalone testing, you'd mock the DB session and CRUD calls,
    # or set up a test DB.
    logging.basicConfig(level=logging.INFO)
    logger.info("AI Matcher Service - CLI Test (Conceptual)")
    
    # --- Mocking for conceptual test ---
    class MockSession:
        def query(self, *args): return self # chain
        def filter(self, *args): return self # chain
        def first(self): return None # chain
        def all(self): return [] # chain
        def add(self, *args): pass
        def commit(self): pass
        def refresh(self, *args): pass

    mock_db_session = MockSession()

    # Example:
    # test_claimant_id = 1
    # logger.info(f"Simulating match_jobs_for_claimant for claimant ID: {test_claimant_id}")
    # results = match_jobs_for_claimant(db=mock_db_session, claimant_id=test_claimant_id)
    # logger.info(f"Simulation results for claimant ID {test_claimant_id}: {len(results)} matches found (mocked).")

    text1 = "Experienced python developer with skills in FastAPI, SQL, and data analysis. Looking for a challenging role."
    keywords1 = extract_keywords_from_text(text1)
    logger.info(f"Keywords from '{text1}': {keywords1}")

    text2 = "Job: Python Engineer. Requirements: Python, Django, REST APIs. Nice to have: Docker, Kubernetes."
    keywords2 = extract_keywords_from_text(text2)
    logger.info(f"Keywords from '{text2}': {keywords2}")

    if keywords1 and keywords2:
        common = keywords1.intersection(keywords2)
        logger.info(f"Common keywords: {common}, Score: {len(common)}")

    logger.info("AI Matcher Service - CLI Test Finished")
