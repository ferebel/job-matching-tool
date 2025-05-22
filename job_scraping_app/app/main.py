from fastapi import FastAPI
from app.api.endpoints import claimants as claimants_router
from app.api.endpoints import scraper_trigger as scraper_trigger_router
from app.api.endpoints import matching as matching_router # New import for matching router

app = FastAPI(title="Job Scraping Application API")

# Include existing routers
app.include_router(claimants_router.router, prefix="/api/v1/claimants", tags=["Claimants"])
app.include_router(scraper_trigger_router.router, prefix="/api/v1/scraper", tags=["Scraper"])

# Include the new AI matching router
# The tag "Matching" is defined within the matching_router.py, so we can use that.
# Or override with tags=["AI Matching Service"] here if preferred.
app.include_router(matching_router.router, prefix="/api/v1", tags=["Matching"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Job Scraping Application API"}
