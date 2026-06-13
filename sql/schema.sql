-- ============================================================================
-- BRONZE LAYER (Raw Data Staging)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bronze_clinical_trials (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    raw_xml_content XML NOT NULL,                  -- Native Postgres XML data type
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint to avoid inserting completely blank files
    CONSTRAINT chk_xml_not_empty CHECK (length(raw_xml_content::text) > 0)
);

-- Indexing metadata for fast operational auditing
CREATE INDEX IF NOT EXISTS idx_bronze_ingested_at ON bronze_clinical_trials(ingested_at);