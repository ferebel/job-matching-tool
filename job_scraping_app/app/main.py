from fastapi import FastAPI
from app.api.endpoints import claimants as claimants_router

app = FastAPI(title="Job Scraping Application API")

app.include_router(claimants_router.router, prefix="/api/v1/claimants", tags=["Claimants"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Job Scraping Application API"}
