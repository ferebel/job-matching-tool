import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, quote_plus
from pprint import pprint
# from datetime import datetime # For parsing date_posted if available

# Configure basic logging - module level logger
logger = logging.getLogger(__name__)
# Ensure logging is configured by the application if this module is imported
# If run as script, basicConfig will apply if no handlers are already set.

BASE_URL_REED_UK = "https://www.reed.co.uk"

def scrape_reed_uk_jobs(job_title_query: str, location_query: str) -> list[dict]:
    """
    Scrapes job postings from Reed.co.uk.
    """
    # URL encode the job title and location
    encoded_job_title = quote_plus(job_title_query)
    encoded_location = quote_plus(location_query)
    
    search_url = f"{BASE_URL_REED_UK}/jobs/{encoded_job_title}-jobs-in-{encoded_location}"
    logger.info(f"Starting scrape for job title: '{job_title_query}' in location: '{location_query}' from URL: {search_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 JobScrapingApp/1.0"
    }

    found_jobs = []

    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        logger.info(f"Successfully fetched HTML content from {search_url}. Status: {response.status_code}")

        soup = BeautifulSoup(response.content, "html.parser")

        # Identifying job cards: Based on typical job site structures and past explorations,
        # job cards are often <article> elements or <div>s with specific classes.
        # From the previous view_text_website output, job links like [26], [30] etc. are prominent.
        # These links were associated with text like "(BUTTON) Python Developer".
        # The links themselves were of the form: /jobs/python-developer/JOB_ID?source=searchResults...
        # We need to find the common parent for job title, company, location, snippet.
        
        # Looking for <article> tags that might contain job details.
        # Reed.co.uk uses <article> elements with class "card job-card_jobCard__MytvR" (inspected in browser)
        # However, class names can change and might be dynamically generated.
        # Let's try a more general approach first, then refine.
        # The output of view_text_website showed links like [26], [30], etc. for job titles.
        # The job title links seem to have a pattern like `/jobs/JOB_TITLE_SLUG/JOB_ID?source=...`
        
        # Updated selector based on common patterns on Reed (inspected via browser developer tools)
        # Each job card is an <article> element.
        job_cards = soup.find_all("article", class_=lambda x: x and "job-card_jobCard__" in x) # More robust to minor class changes
        
        if not job_cards: # Fallback if the specific class name changed significantly
             # A less specific selector might be needed if the class above fails.
             # For example, find all articles and then filter them based on content.
             # This is a placeholder for more advanced fallback logic.
             logger.warning(f"No job cards found with the primary selector. The page structure might have changed or no jobs match.")
             # Attempting a broader search for elements that contain job links
             # This is highly experimental and might not yield good results.
             # potential_cards = soup.find_all(lambda tag: tag.name == 'div' and tag.find('a', href=lambda h: h and '/jobs/' in h and '?source=searchResults' in h))
             # logger.info(f"Found {len(potential_cards)} potential cards with a broader search.")
             # job_cards = potential_cards # If using this, parsing below needs to be very robust


        logger.info(f"Found {len(job_cards)} potential job cards using primary selector.")

        for card_idx, card in enumerate(job_cards):
            job_title_text = None
            job_url_absolute = None
            company_name = None
            location_text = None
            description_snippet = None
            # date_posted_str = None # Reed specific

            # Title and URL (typically an <a> tag within a heading <h1>, <h2>, <h3>)
            # Reed uses <h3> with class "job-card_jobResultHeading__title__SSrkG" containing an <a>
            title_element_container = card.find("h3", class_=lambda x: x and "job-card_jobResultHeading__title__" in x)
            if title_element_container:
                title_link = title_element_container.find("a", href=True)
                if title_link:
                    job_title_text = title_link.text.strip()
                    relative_url = title_link['href']
                    job_url_absolute = urljoin(BASE_URL_REED_UK, relative_url)

            # Company Name
            # Typically a <span> or <div> near the title or in metadata section.
            # Reed uses a <ul> with class "job-card_jobResultMeta__transient__" then <li> then <a>
            # This can be complex. Let's try finding by text "by" then the next <a>
            meta_items_list = card.find("ul", class_=lambda x: x and "job-card_jobResultMeta__" in x)
            if meta_items_list:
                # Company is often the first <li> with an <a> tag inside
                company_link = meta_items_list.find("li") 
                if company_link and company_link.find("a"):
                    company_name = company_link.find("a").text.strip()
                
                # Location is often another <li>
                # Example: <li class="job-card_jobResultLocation__" ...> London </li>
                location_item = meta_items_list.find("li", class_=lambda x: x and "job-card_jobResultLocation__" in x)
                if location_item:
                    location_text = location_item.text.strip()


            # Description Snippet
            # Reed uses a <div> with class "job-card_jobResultDescription___"
            description_element = card.find("div", class_=lambda x: x and "job-card_jobResultDescription__" in x)
            if description_element:
                description_snippet = description_element.text.strip()
            
            # Date Posted (Example, might be complex to parse reliably)
            # date_posted_element = card.find("div", class_="job-card_postedDate") # Hypothetical
            # if date_posted_element:
            #     date_posted_str = date_posted_element.text.strip()
                # Further parsing would be needed to convert "Posted X days ago" to a date

            if job_title_text and job_url_absolute:
                job_data = {
                    "title": job_title_text,
                    "company_name": company_name if company_name else "N/A",
                    "location": location_text if location_text else "N/A",
                    "description_snippet": description_snippet if description_snippet else "N/A",
                    "job_url": job_url_absolute,
                    "source_website": "Reed.co.uk",
                    # "date_posted": date_posted_str # If parsed
                }
                found_jobs.append(job_data)
                # logger.debug(f"Scraped job: {job_title_text} - {company_name}")
            else:
                logger.warning(f"Card {card_idx+1}: Could not extract all required details. Title: '{job_title_text}', URL: '{job_url_absolute}'. Skipping this card.")
                # logger.debug(f"Problematic card HTML snippet: {card.prettify()[:500]}")


    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {search_url}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping of {search_url}: {e}", exc_info=True)
        # To help debug structure changes, you could save the HTML:
        # with open(f"error_page_reed_{job_title_query}_{location_query}.html", "w", encoding="utf-8") as f:
        #     f.write(response.text if 'response' in locals() else "No response object available")
        return []

    logger.info(f"Successfully scraped {len(found_jobs)} jobs for '{job_title_query}' in '{location_query}' from Reed.co.uk.")
    return found_jobs

# --- Integration with DB ---
from sqlalchemy.orm import Session
from app.db import crud_jobs # Import the CRUD module for job postings

def run_scraper_and_store_jobs(db: Session, job_title_query: str, location_query: str) -> dict:
    """
    Runs the Reed.co.uk scraper and stores the results in the database.
    Returns a summary of the operation.
    """
    logger.info(f"Starting job scraping and storing process for: Title='{job_title_query}', Location='{location_query}'")
    
    scraped_jobs_data = scrape_reed_uk_jobs(job_title_query, location_query)
    
    jobs_found_count = len(scraped_jobs_data)
    new_jobs_added_count = 0
    existing_jobs_skipped_count = 0 # Or updated, depending on logic in create_job_posting

    if not scraped_jobs_data:
        summary_message = f"No jobs found by scraper for Title='{job_title_query}', Location='{location_query}'."
        logger.info(summary_message)
        return {
            "message": summary_message,
            "jobs_found": jobs_found_count,
            "new_jobs_added": new_jobs_added_count,
            "existing_jobs_skipped": existing_jobs_skipped_count
        }

    for job_data in scraped_jobs_data:
        try:
            # create_job_posting now returns (SQLJobPosting, bool_was_created)
            _, was_created = crud_jobs.create_job_posting(db=db, job_data=job_data)
            if was_created:
                new_jobs_added_count += 1
            else:
                existing_jobs_skipped_count += 1
        except Exception as e:
            logger.error(f"Error storing job data for URL {job_data.get('job_url', 'N/A')}: {e}", exc_info=True)
            # Optionally, count these as errors or failures

    summary_message = (
        f"Scraping finished for Title='{job_title_query}', Location='{location_query}'. "
        f"Found {jobs_found_count} jobs. "
        f"Added {new_jobs_added_count} new jobs. "
        f"Skipped {existing_jobs_skipped_count} existing jobs."
    )
    logger.info(summary_message)
    
    return {
        "message": summary_message,
        "jobs_found": jobs_found_count,
        "new_jobs_added": new_jobs_added_count,
        "existing_jobs_skipped": existing_jobs_skipped_count
    }


if __name__ == "__main__":
    # Setup basic logging for CLI execution if not already configured by the app
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logger.info("--- Starting Reed.co.uk Scraper Test CLI ---")
    
    city_test = "London"
    job_title_test = "python developer"
    
    logger.info(f"Testing with: Job Title='{job_title_test}', Location='{city_test}'")
    scraped_jobs_reed = scrape_reed_uk_jobs(job_title_test, city_test)

    if scraped_jobs_reed:
        logger.info(f"Found {len(scraped_jobs_reed)} jobs from Reed.co.uk:")
        pprint(scraped_jobs_reed[:2]) # Print first 2 jobs as sample
    else:
        logger.warning(f"No jobs found for '{job_title_test}' in '{city_test}' from Reed.co.uk. This could be due to no matching jobs, network issues, or HTML structure changes.")

    logger.info("--- Reed.co.uk Scraper Test CLI Finished ---")
