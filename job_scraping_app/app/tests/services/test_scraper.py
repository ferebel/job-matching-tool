import pytest
import requests_mock
from app.services.scraper import scrape_indeed_jobs, BASE_URL_INDEED
import logging

# Sample HTML content for mocking Indeed responses
MOCK_HTML_JOB_CARDS = """
<html>
<body>
    <div id="resultsCol">
        <div class="jobsearch-SerpJobCard">
            <h2 class="title"><a href="/rc/clk?jk=123" title="Software Engineer">Software Engineer</a></h2>
            <span class="company">Tech Solutions Inc.</span>
            <div class="location">London</div>
            <div class="summary">Develop amazing software.</div>
        </div>
        <div class="jobsearch-SerpJobCard">
            <h2 class="title"><a href="/rc/clk?jk=456" title="Data Analyst">Data Analyst</a></h2>
            <span class="company">Data Insights Ltd.</span>
            <div class="location">Manchester</div>
            <div class="summary">Analyze interesting data.</div>
        </div>
    </div>
</body>
</html>
"""

MOCK_HTML_NO_JOB_CARDS = """
<html>
<body>
    <div id="resultsCol">
        <p>No jobs found matching your criteria.</p>
    </div>
</body>
</html>
"""

MOCK_HTML_UNEXPECTED_STRUCTURE = """
<html>
<body>
    <div id="job_results">
        <div class="job-item">
            <h3 class="job-title">Software Engineer</h3>
            <p class="job-company">Innovate Corp</p>
        </div>
    </div>
</body>
</html>
"""

@pytest.fixture
def mock_requests(requests_mock):
    """Fixture to provide requests_mock.Mocker."""
    return requests_mock

def test_scrape_indeed_jobs_success(mock_requests, caplog):
    city = "London"
    job_title = "Software Engineer"
    expected_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    mock_requests.get(expected_url, text=MOCK_HTML_JOB_CARDS, status_code=200)

    caplog.set_level(logging.INFO)
    jobs = scrape_indeed_jobs(city, job_title)

    assert len(jobs) == 2
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["company_name"] == "Tech Solutions Inc."
    assert jobs[0]["location"] == "London"
    assert jobs[0]["description_snippet"] == "Develop amazing software."
    assert jobs[0]["job_url"] == f"{BASE_URL_INDEED}/rc/clk?jk=123"
    assert jobs[0]["source_website"] == "Indeed-Mock"

    assert jobs[1]["title"] == "Data Analyst"
    assert jobs[1]["company_name"] == "Data Insights Ltd."
    assert f"Successfully fetched HTML content from {expected_url}" in caplog.text
    assert "Found 2 potential job cards." in caplog.text
    assert "Successfully scraped 2 jobs" in caplog.text

def test_scrape_indeed_jobs_http_error(mock_requests, caplog):
    city = "London"
    job_title = "QA Tester"
    expected_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    mock_requests.get(expected_url, status_code=500)

    caplog.set_level(logging.ERROR)
    jobs = scrape_indeed_jobs(city, job_title)

    assert len(jobs) == 0
    assert f"Request failed for {expected_url}: 500 Server Error" in caplog.text

def test_scrape_indeed_jobs_no_job_cards_found(mock_requests, caplog):
    city = "Remote"
    job_title = "Technical Writer"
    expected_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    mock_requests.get(expected_url, text=MOCK_HTML_NO_JOB_CARDS, status_code=200)

    caplog.set_level(logging.INFO)
    jobs = scrape_indeed_jobs(city, job_title)

    assert len(jobs) == 0
    assert "Found 0 potential job cards." in caplog.text
    assert "No job cards found with class 'jobsearch-SerpJobCard'" in caplog.text
    assert "Successfully scraped 0 jobs" in caplog.text

def test_scrape_indeed_jobs_unexpected_html_structure(mock_requests, caplog):
    city = "Berlin"
    job_title = "DevOps Engineer"
    expected_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    mock_requests.get(expected_url, text=MOCK_HTML_UNEXPECTED_STRUCTURE, status_code=200)

    caplog.set_level(logging.WARNING) # Expecting warnings about missing elements
    jobs = scrape_indeed_jobs(city, job_title)

    assert len(jobs) == 0
    # This specific log comes if #resultsCol is present but no 'jobsearch-SerpJobCard'
    # In MOCK_HTML_UNEXPECTED_STRUCTURE, #resultsCol is missing, so the more general warning should appear.
    # If #resultsCol was present, we'd see:
    # assert "No job cards found with class 'jobsearch-SerpJobCard'" in caplog.text
    # Instead, we might see a warning about the missing results container, or just 0 cards found.
    # The current scraper logs "Found 0 potential job cards."
    assert "Found 0 potential job cards." in caplog.text
    # And because the specific class for job cards isn't found, it will also log:
    assert "No job cards found with class 'jobsearch-SerpJobCard'" in caplog.text
    assert "Successfully scraped 0 jobs" in caplog.text


def test_scrape_indeed_jobs_missing_elements_in_card(mock_requests, caplog):
    # HTML where a card is missing a title or URL
    MOCK_HTML_MISSING_ELEMENTS = """
    <html>
    <body>
        <div id="resultsCol">
            <div class="jobsearch-SerpJobCard">
                <!-- Missing title link -->
                <span class="company">Anonymous Corp.</span>
                <div class="location">Unknown</div>
                <div class="summary">A job.</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="title"><a href="/another/job?id=789" title="Good Job">Good Job</a></h2>
                <span class="company">Known Corp.</span>
                <div class="location">Known City</div>
                <div class="summary">This one is complete.</div>
            </div>
        </div>
    </body>
    </html>
    """
    city = "Anytown"
    job_title = "Any Job"
    expected_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    mock_requests.get(expected_url, text=MOCK_HTML_MISSING_ELEMENTS, status_code=200)

    caplog.set_level(logging.WARNING)
    jobs = scrape_indeed_jobs(city, job_title)

    assert len(jobs) == 1 # Only the valid card should be processed
    assert jobs[0]["title"] == "Good Job"
    assert jobs[0]["company_name"] == "Known Corp."
    assert "Could not extract title or URL from a card." in caplog.text
    assert "Successfully scraped 1 jobs" in caplog.text
