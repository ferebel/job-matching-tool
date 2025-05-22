import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings # Assuming settings can provide a DATABASE_URL
from app.db.base_class import Base
from app.main import app # FastAPI app
from app.db.session import get_db # Original get_db
from httpx import AsyncClient

# Use a different database URL for testing
# Ensure DATABASE_URL is loaded, otherwise, this will fail.
# In a real CI setup, DATABASE_URL (and TEST_DATABASE_URL) should be environment variables.
if not settings.DATABASE_URL:
    # Fallback for CI or environments where .env might not be loaded by default for tests
    # This is a basic fallback, a more robust solution is needed for complex setups
    # e.g. using a default SQLite in-memory for tests if no URL is found
    print("Warning: DATABASE_URL not found in settings. Using default SQLite for testing.")
    TEST_DATABASE_URL = "sqlite:///./test.db" 
else:
    TEST_DATABASE_URL = settings.DATABASE_URL + "_test"
    # Ensure we are not using the exact same URL for safety, though _test suffix helps
    if TEST_DATABASE_URL == settings.DATABASE_URL:
        raise ValueError("TEST_DATABASE_URL cannot be the same as DATABASE_URL. Set a different test database.")

print(f"Using Test Database URL: {TEST_DATABASE_URL}")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    # This is important for async fixtures when the scope is 'session'
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    # For SQLite, connect_args might be needed: {"check_same_thread": False}
    if TEST_DATABASE_URL.startswith("sqlite"):
        return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    return create_engine(TEST_DATABASE_URL)

@pytest.fixture(scope="session")
def setup_test_database(test_engine):
    print(f"Creating test database schema on {test_engine.url}...")
    Base.metadata.create_all(bind=test_engine) # Create tables
    yield
    print(f"Dropping test database schema on {test_engine.url}...")
    Base.metadata.drop_all(bind=test_engine) # Drop tables after tests

@pytest.fixture(scope="function")
def TestSessionLocal(test_engine):
    # The sessionmaker is configured once per test session using the test_engine
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db_session(TestSessionLocal, setup_test_database): 
    # setup_test_database ensures tables are created before session is used
    # and dropped after all tests in the session are done.
    session = TestSessionLocal()
    try:
        print("Yielding test_db_session")
        yield session
    finally:
        print("Closing test_db_session")
        session.close()

@pytest.fixture(scope="function")
async def test_client(test_db_session: Session, setup_test_database): # Ensure DB is set up
    # The dependency override function needs to be a generator
    def override_get_db_for_test():
        try:
            yield test_db_session
        finally:
            # The session is closed by the test_db_session fixture's finally block
            pass 
            # test_db_session.close() # Closing here can be problematic if session is used after request

    app.dependency_overrides[get_db] = override_get_db_for_test
    
    # Using httpx.AsyncClient for async app
    async with AsyncClient(app=app, base_url="http://test") as client:
        print("Yielding test_client")
        yield client
    
    # Clean up the override after the test client is done
    del app.dependency_overrides[get_db]
    print("Cleaned up test_client and dependency override")
