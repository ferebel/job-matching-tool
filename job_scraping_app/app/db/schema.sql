-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Table: claimants
-- Stores information about the individuals (claimants) seeking job opportunities.
CREATE TABLE claimants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50),
    notes TEXT, -- For any other relevant static info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update updated_at on claimants table
CREATE TRIGGER update_claimants_updated_at
BEFORE UPDATE ON claimants
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Index on email for faster lookups
CREATE INDEX idx_claimants_email ON claimants(email);


-- Table: claimant_documents
-- Stores documents related to claimants, such as CVs, cover letters, etc.
CREATE TABLE claimant_documents (
    id SERIAL PRIMARY KEY,
    claimant_id INTEGER REFERENCES claimants(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- e.g., 'CV', 'cover_letter', 'other'
    file_path VARCHAR(512), -- Stores path to the uploaded file, if applicable
    raw_text_content TEXT,
    parsed_entities JSONB, -- For storing structured data extracted from the document
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on claimant_id for faster lookups
CREATE INDEX idx_claimant_documents_claimant_id ON claimant_documents(claimant_id);
-- Index on document_type
CREATE INDEX idx_claimant_documents_document_type ON claimant_documents(document_type);


-- Table: job_postings
-- Stores information about job postings scraped from various sources.
CREATE TABLE job_postings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    location VARCHAR(255),
    description TEXT NOT NULL,
    job_url VARCHAR(2048) UNIQUE NOT NULL,
    source_website VARCHAR(255), -- e.g., 'Indeed', 'LinkedIn', 'company_career_page'
    date_scraped TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_posted DATE, -- If available from scraping
    is_active BOOLEAN DEFAULT TRUE
);

-- Index on job_url for faster lookups and uniqueness enforcement
CREATE UNIQUE INDEX idx_job_postings_job_url ON job_postings(job_url);
-- Index on source_website
CREATE INDEX idx_job_postings_source_website ON job_postings(source_website);
-- Index on date_posted
CREATE INDEX idx_job_postings_date_posted ON job_postings(date_posted);


-- Table: search_criteria
-- Stores the job search preferences for each claimant.
CREATE TABLE search_criteria (
    id SERIAL PRIMARY KEY,
    claimant_id INTEGER REFERENCES claimants(id) ON DELETE CASCADE,
    keywords TEXT, -- Comma-separated or array
    target_location VARCHAR(255),
    desired_sectors TEXT, -- Comma-separated or array
    barriers_notes TEXT, -- e.g., English level, background, license held
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on claimant_id for faster lookups
CREATE INDEX idx_search_criteria_claimant_id ON search_criteria(claimant_id);


-- Table: matched_jobs
-- Stores matches between claimants and job postings.
CREATE TABLE matched_jobs (
    id SERIAL PRIMARY KEY,
    claimant_id INTEGER REFERENCES claimants(id) ON DELETE CASCADE,
    job_posting_id INTEGER REFERENCES job_postings(id) ON DELETE CASCADE,
    match_score FLOAT, -- e.g., between 0 and 1
    status VARCHAR(50) DEFAULT 'new', -- e.g., 'new', 'viewed', 'suggested_to_claimant', 'applied'
    match_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes_for_advisor TEXT, -- For you to add notes about why it's a good match or any concerns
    UNIQUE (claimant_id, job_posting_id)
);

-- Index on claimant_id for faster lookups
CREATE INDEX idx_matched_jobs_claimant_id ON matched_jobs(claimant_id);
-- Index on job_posting_id for faster lookups
CREATE INDEX idx_matched_jobs_job_posting_id ON matched_jobs(job_posting_id);
-- Index on status
CREATE INDEX idx_matched_jobs_status ON matched_jobs(status);

COMMENT ON TABLE claimants IS 'Stores information about the individuals (claimants) seeking job opportunities.';
COMMENT ON COLUMN claimants.notes IS 'For any other relevant static info';

COMMENT ON TABLE claimant_documents IS 'Stores documents related to claimants, such as CVs, cover letters, etc.';
COMMENT ON COLUMN claimant_documents.document_type IS 'e.g., ''CV'', ''cover_letter'', ''other''';
COMMENT ON COLUMN claimant_documents.file_path IS 'Stores path to the uploaded file, if applicable';
COMMENT ON COLUMN claimant_documents.parsed_entities IS 'For storing structured data extracted from the document';

COMMENT ON TABLE job_postings IS 'Stores information about job postings scraped from various sources.';
COMMENT ON COLUMN job_postings.source_website IS 'e.g., ''Indeed'', ''LinkedIn'', ''company_career_page''';
COMMENT ON COLUMN job_postings.date_posted IS 'If available from scraping';

COMMENT ON TABLE search_criteria IS 'Stores the job search preferences for each claimant.';
COMMENT ON COLUMN search_criteria.keywords IS 'Comma-separated or array';
COMMENT ON COLUMN search_criteria.desired_sectors IS 'Comma-separated or array';
COMMENT ON COLUMN search_criteria.barriers_notes IS 'e.g., English level, background, license held';

COMMENT ON TABLE matched_jobs IS 'Stores matches between claimants and job postings.';
COMMENT ON COLUMN matched_jobs.match_score IS 'e.g., between 0 and 1';
COMMENT ON COLUMN matched_jobs.status IS 'e.g., ''new'', ''viewed'', ''suggested_to_claimant'', ''applied''';
COMMENT ON COLUMN matched_jobs.notes_for_advisor IS 'For you to add notes about why it''s a good match or any concerns';

-- Grant usage on sequences for the default user if necessary, or handle permissions appropriately.
-- For example, if you have a specific user for your application:
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO myappuser;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO myappuser;

-- End of schema.sql
