import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
from pprint import pprint

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL_INDEED = "https://uk.indeed.com"

def scrape_indeed_jobs(city: str, job_title: str) -> list[dict]:
    """
    Scrapes job postings from a mock Indeed structure.
    Note: This uses a hypothetical HTML structure and may not work on the live Indeed site.
    """
    search_url = f"{BASE_URL_INDEED}/jobs?q={job_title.replace(' ', '+')}&l={city.replace(' ', '+')}"
    logging.info(f"Starting scrape for job title: '{job_title}' in city: '{city}' from URL: {search_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    found_jobs = []

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        logging.info(f"Successfully fetched HTML content from {search_url}")

        soup = BeautifulSoup(response.content, "html.parser")

        # Hypothetical HTML structure:
        # Each job card is a div with class 'jobsearch-SerpJobCard'
        job_cards = soup.find_all("div", class_="jobsearch-SerpJobCard")
        logging.info(f"Found {len(job_cards)} potential job cards.")

        if not job_cards:
            # Example of a more specific check if the main container is missing
            # This helps differentiate between no jobs and a page structure change.
            results_container = soup.find(id="resultsCol")
            if not results_container:
                logging.warning("Could not find the main job results container (e.g., #resultsCol). Page structure might have changed.")
            else:
                logging.info("No job cards found with class 'jobsearch-SerpJobCard'. It's possible no jobs match the criteria or the class name is different.")


        for card in job_cards:
            title_element = card.find("h2", class_="title") # Often an 'a' tag inside or is the 'a' tag
            company_element = card.find("span", class_="company")
            location_element = card.find("div", class_="location") # Or 'span'
            summary_element = card.find("div", class_="summary")
            
            job_title_text = None
            job_url = None

            if title_element:
                # Title might be within an 'a' tag, or the 'a' tag itself might be the title_element
                a_tag = title_element.find("a") if title_element.find("a") else title_element if title_element.name == 'a' else None
                if a_tag and a_tag.has_attr("title"):
                    job_title_text = a_tag.get("title", "").strip()
                elif title_element:
                     job_title_text = title_element.text.strip()

                if a_tag and a_tag.has_attr("href"):
                    relative_url = a_tag.get("href")
                    job_url = urljoin(BASE_URL_INDEED, relative_url)


            company_name = company_element.text.strip() if company_element else "N/A"
            location = location_element.text.strip() if location_element else "N/A"
            description_snippet = summary_element.text.strip() if summary_element else "N/A"

            if job_title_text and job_url:
                found_jobs.append({
                    "title": job_title_text,
                    "company_name": company_name,
                    "location": location,
                    "description_snippet": description_snippet,
                    "job_url": job_url,
                    "source_website": "Indeed-Mock"
                })
            else:
                logging.warning(f"Could not extract title or URL from a card. Title element: {title_element}, Company: {company_name}")


    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {search_url}: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred during scraping: {e}")
        # In a production scenario, you might want to save the HTML for debugging:
        # with open("error_page.html", "w", encoding="utf-8") as f:
        # f.write(response.text)
        return []

    logging.info(f"Successfully scraped {len(found_jobs)} jobs for '{job_title}' in '{city}'.")
    return found_jobs

if __name__ == "__main__":
    # Basic logging setup for CLI execution
    # This will be active if the script is run directly
    # If imported, the root logger config (if any) or the one set by the app will be used.
    if not logging.getLogger().hasHandlers(): # Avoid adding multiple handlers if already configured
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logging.info("--- Starting Scraper Test CLI ---")
    
    # Test case 1: Software Developer in London
    city_test = "London"
    job_title_test = "software developer"
    
    # Because the HTML is hypothetical, we expect 0 results but want to see the process
    logging.info(f"Testing with: City='{city_test}', Job Title='{job_title_test}'")
    scraped_jobs = scrape_indeed_jobs(city_test, job_title_test)

    if scraped_jobs:
        logging.info(f"Found {len(scraped_jobs)} jobs:")
        pprint(scraped_jobs)
    else:
        logging.info(f"No jobs found for '{job_title_test}' in '{city_test}'. This is expected with the mock HTML structure.")

    # Test case 2: A different job or city (optional)
    # city_test_2 = "Manchester"
    # job_title_test_2 = "data analyst"
    # logging.info(f"Testing with: City='{city_test_2}', Job Title='{job_title_test_2}'")
    # scraped_jobs_2 = scrape_indeed_jobs(city_test_2, job_title_test_2)
    # if scraped_jobs_2:
    #     logging.info(f"Found {len(scraped_jobs_2)} jobs:")
    #     pprint(scraped_jobs_2)
    # else:
    #     logging.info(f"No jobs found for '{job_title_test_2}' in '{city_test_2}'. This is expected.")

    logging.info("--- Scraper Test CLI Finished ---")
