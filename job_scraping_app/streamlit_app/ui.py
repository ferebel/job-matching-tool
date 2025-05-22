import streamlit as st
import requests
import json # For parsing JSON responses if needed, though requests.json() is usually enough
import os # For environment variables
from datetime import datetime # For formatting dates in matched jobs display

# --- Configuration ---
# Read backend URL from environment variable, with a default for local development
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# --- Helper Functions ---

def handle_api_response(response: requests.Response, success_message: str = "Success!"):
    """Handles API response, showing success or error messages."""
    if 200 <= response.status_code < 300:
        st.success(success_message)
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text # Or None, or handle as an error
    else:
        error_details = response.text
        try:
            error_json = response.json()
            if "detail" in error_json: # FastAPI often uses "detail" for errors
                if isinstance(error_json["detail"], list) and len(error_json["detail"]) > 0:
                     # Handle Pydantic validation errors
                    error_messages = [f"{err['loc'][-1]}: {err['msg']}" for err in error_json["detail"]]
                    error_details = "; ".join(error_messages)
                else:
                    error_details = str(error_json["detail"])
            else:
                error_details = str(error_json) # Fallback to full JSON string
        except json.JSONDecodeError:
            pass # Keep original text if not JSON
        st.error(f"Error (Status {response.status_code}): {error_details}")
        return None

def get_all_claimants_from_api():
    """Fetches all claimants from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/claimants/")
        if response.status_code == 200:
            return response.json()
        else:
            # st.error(f"Error fetching claimants (Status {response.status_code}): {response.text}")
            handle_api_response(response, "Failed to fetch claimants initially.")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the backend. Is it running?")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching claimants: {e}")
        return []

# --- Main App Layout ---
st.set_page_config(layout="wide")
st.title("Job Scraper - Claimant Management")

# Initialize session state for claimants if not already present
if 'claimants_list' not in st.session_state:
    st.session_state.claimants_list = []


# --- Section: List Existing Claimants ---
st.header("Current Claimants")

if st.button("Refresh Claimant List"):
    st.session_state.claimants_list = get_all_claimants_from_api()

# Fetch claimants on first load or if list is empty and refresh button not just pressed
if not st.session_state.claimants_list:
     st.session_state.claimants_list = get_all_claimants_from_api()

if st.session_state.claimants_list:
    # Prepare data for display (e.g., select specific columns)
    display_data = [
        {"ID": c.get("id"), "Name": c.get("name"), "Email": c.get("email"), "Phone": c.get("phone_number"), "Notes": c.get("notes")} 
        for c in st.session_state.claimants_list if isinstance(c, dict)
    ]
    if display_data:
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No claimants found or data format issue.")
else:
    st.info("No claimants found. Add one below or try refreshing.")


# --- Section: Create New Claimant ---
st.header("Create New Claimant")
with st.form("create_claimant_form", clear_on_submit=True):
    st.subheader("Enter Claimant Details:")
    name = st.text_input("Name*", help="Claimant's full name.")
    email = st.text_input("Email*", help="Claimant's email address.")
    phone = st.text_input("Phone (Optional)")
    notes = st.text_area("Notes (Optional)", height=100)
    
    submit_button = st.form_submit_button(label="Create Claimant")

    if submit_button:
        if not name or not email:
            st.warning("Name and Email are required fields.")
        else:
            payload = {
                "name": name,
                "email": email,
                "phone_number": phone if phone else None,
                "notes": notes if notes else None,
            }
            try:
                response = requests.post(f"{BACKEND_URL}/claimants/", json=payload)
                api_response_data = handle_api_response(response, f"Claimant '{name}' created successfully!")
                if api_response_data:
                    # Refresh claimant list after successful creation
                    st.session_state.claimants_list = get_all_claimants_from_api()
                    st.rerun() # Rerun to update the displayed list
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Could not connect to the backend to create claimant.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


# --- Section: Upload CV for Claimant ---
st.header("Upload Document for Claimant")

if st.session_state.claimants_list:
    # Prepare options for selectbox: list of tuples (id, display_name)
    # Filter out any potential None entries or entries without 'id' or 'name'
    claimant_options = {
        c['id']: f"{c.get('name', 'N/A')} (ID: {c['id']})" 
        for c in st.session_state.claimants_list if isinstance(c, dict) and 'id' in c
    }

    if not claimant_options:
        st.warning("No claimants available to select for document upload. Please create a claimant first or refresh the list.")
    else:
        selected_claimant_id = st.selectbox(
            "Select Claimant*", 
            options=list(claimant_options.keys()), 
            format_func=lambda id_val: claimant_options.get(id_val, "Unknown Claimant")
        )
        
        document_type = st.selectbox("Document Type*", ["CV", "Cover Letter", "Other"])
        uploaded_file = st.file_uploader("Choose a file (PDF or DOCX)*", type=["pdf", "docx"])

        if st.button("Upload Document"):
            if uploaded_file is not None and selected_claimant_id and document_type:
                files_payload = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                data_payload = {'document_type': document_type}
                
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/claimants/{selected_claimant_id}/documents/",
                        files=files_payload,
                        data=data_payload
                    )
                    api_response_data = handle_api_response(response, f"Document '{uploaded_file.name}' uploaded successfully for Claimant ID {selected_claimant_id}!")
                    if api_response_data:
                        st.write("Server Response Snippet:")
                        # Display relevant parts of the response
                        st.json({
                            "id": api_response_data.get("id"),
                            "file_path": api_response_data.get("file_path"),
                            "raw_text_content_snippet": (api_response_data.get("raw_text_content") or "")[:200] + "..."
                        })
                except requests.exceptions.ConnectionError:
                    st.error(f"Connection Error: Could not connect to the backend to upload document for Claimant ID {selected_claimant_id}.")
                except Exception as e:
                    st.error(f"An unexpected error occurred during upload: {e}")
            else:
                st.warning("Please select a claimant, choose a document type, and upload a file.")
else:
    st.info("Create a claimant first to enable document uploads.")

st.divider()

# --- Section: Run Job Scraper ---
st.header("Run Job Scraper")
scraper_job_title = st.text_input("Job Title for Scraper", value="python developer", key="scraper_job_title")
scraper_location = st.text_input("Location for Scraper", value="london", key="scraper_location")

if st.button("Scrape Jobs"):
    if scraper_job_title and scraper_location:
        st.info(f"Triggering scraper for '{scraper_job_title}' in '{scraper_location}'...")
        payload = {"job_title": scraper_job_title, "location": scraper_location}
        try:
            response = requests.post(f"{BACKEND_URL}/scraper/trigger-scraper/", json=payload)
            # Use the same handle_api_response or a similar one for this
            if 200 <= response.status_code < 300:
                scraper_summary = response.json()
                st.success(scraper_summary.get("message", "Scraping completed successfully."))
                st.json(scraper_summary) # Display full summary
            else:
                handle_api_response(response, "Scraper run failed.") # Re-use existing handler
        except requests.exceptions.ConnectionError:
            st.error(f"Connection Error: Could not connect to the backend at {BACKEND_URL}/scraper/trigger-scraper/.")
        except Exception as e:
            st.error(f"An unexpected error occurred while triggering scraper: {e}")
    else:
        st.warning("Please provide both Job Title and Location for scraping.")

st.divider()

# --- Section: AI Job Matching ---
st.header("AI Job Matching")

# Re-use claimant selection if available, or adapt if needed.
# Assuming st.session_state.claimants_list is populated from "Current Claimants" section.
if 'claimants_list' in st.session_state and st.session_state.claimants_list:
    matcher_claimant_options = {
        c['id']: f"{c.get('name', 'N/A')} (ID: {c['id']})" 
        for c in st.session_state.claimants_list if isinstance(c, dict) and 'id' in c
    }

    if not matcher_claimant_options:
        st.warning("No claimants available to select for matching. Please create a claimant or refresh the list.")
    else:
        selected_claimant_id_for_matching = st.selectbox(
            "Select Claimant for AI Matching*", 
            options=list(matcher_claimant_options.keys()), 
            format_func=lambda id_val: matcher_claimant_options.get(id_val, "Unknown Claimant"),
            key="matcher_claimant_select" # Unique key
        )

        if st.button("Find Matching Jobs for Selected Claimant"):
            if selected_claimant_id_for_matching:
                st.info(f"Initiating AI matching for Claimant ID: {selected_claimant_id_for_matching}...")
                try:
                    response = requests.post(f"{BACKEND_URL}/claimants/{selected_claimant_id_for_matching}/match-jobs/")
                    
                    if 200 <= response.status_code < 300:
                        matched_jobs_data = response.json()
                        st.session_state.matched_jobs = matched_jobs_data # Store in session state
                        if matched_jobs_data:
                            st.success(f"Found {len(matched_jobs_data)} potential matches!")
                        else:
                            # If API returns empty list (200 OK but no matches)
                            st.info("No new matches found based on current criteria.")
                    else:
                        # Use handle_api_response for consistent error display
                        handle_api_response(response, "AI Matching process failed.")
                        st.session_state.matched_jobs = [] # Clear previous matches on error
                
                except requests.exceptions.ConnectionError:
                    st.error(f"Connection Error: Could not connect to the backend at {BACKEND_URL}/claimants/{selected_claimant_id_for_matching}/match-jobs/.")
                    st.session_state.matched_jobs = []
                except Exception as e:
                    st.error(f"An unexpected error occurred while triggering AI matching: {e}")
                    st.session_state.matched_jobs = []
            else:
                st.error("Please select a claimant first.")

        # Display Matched Job Results
        if 'matched_jobs' in st.session_state and st.session_state.matched_jobs:
            st.subheader("Matching Job Opportunities")
            for match_data in st.session_state.matched_jobs:
                job_posting = match_data.get('job_posting', {})
                expander_title = f"{job_posting.get('title', 'N/A')} at {job_posting.get('company_name', 'N/A')} (Score: {match_data.get('match_score', 'N/A')})"
                with st.expander(expander_title):
                    st.write(f"**Match Score:** {match_data.get('match_score', 'N/A')}")
                    st.write(f"**Status:** {match_data.get('status', 'N/A')}")
                    st.write(f"**Location:** {job_posting.get('location', 'N/A')}")
                    st.write(f"**Advisor Notes:** {match_data.get('notes_for_advisor', 'N/A')}")
                    
                    description = job_posting.get('description', 'N/A')
                    st.write(f"**Job Description Snippet:** {description[:300]}..." if description else "N/A")
                    
                    if job_posting.get('job_url'):
                        st.markdown(f"[View Full Job Posting]({job_posting.get('job_url')})")
                    
                    date_scraped_str = job_posting.get('date_scraped', 'N/A')
                    # Format date_scraped if it's a valid datetime string
                    try:
                        # Assuming date_scraped is ISO format e.g., "2023-05-21T10:00:00"
                        parsed_date_scraped = datetime.fromisoformat(date_scraped_str.replace("Z", "+00:00")) if date_scraped_str else None
                        formatted_date_scraped = parsed_date_scraped.strftime("%Y-%m-%d %H:%M") if parsed_date_scraped else "N/A"
                    except (ValueError, TypeError):
                        formatted_date_scraped = date_scraped_str # Keep as is if parsing fails
                    
                    st.write(f"**Scraped from:** {job_posting.get('source_website', 'N/A')} on {formatted_date_scraped}")
                    st.caption(f"Match ID: {match_data.get('id')}, Job ID: {job_posting.get('id')}")

        elif 'matched_jobs' in st.session_state and not st.session_state.matched_jobs:
            # This state means matching ran but found nothing, or an error cleared previous results.
            st.info("No job matches found for the selected claimant with the current criteria, or an error occurred.")

else:
    st.info("Create or refresh claimants list to enable AI Job Matching.")


# --- (Optional) Section: View Scraped Jobs ---
# This requires a new API endpoint to list jobs from the DB, e.g., GET /api/v1/jobs/
# For now, we'll just put a placeholder or leave it out.
# If you implement a GET /jobs endpoint:
# st.header("View Scraped Jobs")
# if st.button("Refresh Scraped Jobs List"):
#     try:
#         jobs_response = requests.get(f"{BACKEND_URL}/jobs/") # Assuming a /jobs/ endpoint
#         if jobs_response.status_code == 200:
#             st.session_state.scraped_jobs_list = jobs_response.json()
#             if st.session_state.scraped_jobs_list:
#                 st.dataframe(st.session_state.scraped_jobs_list, use_container_width=True)
#             else:
#                 st.info("No scraped jobs found in the database.")
#         else:
#             handle_api_response(jobs_response, "Failed to fetch scraped jobs.")
#     except requests.exceptions.ConnectionError:
#         st.error("Connection Error: Could not connect to the backend to fetch jobs.")
#     except Exception as e:
#         st.error(f"An error occurred while fetching scraped jobs: {e}")

# Display the backend URL being used (for debugging, can be removed later)
st.sidebar.caption(f"API Backend: {BACKEND_URL}")
st.sidebar.info("Ensure the FastAPI backend is running and accessible at the URL above.")
