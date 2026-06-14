-- ============================================================================
-- BRONZE LAYER: Raw Landing Zone
-- ============================================================================
CREATE TABLE IF NOT EXISTS bronze_clinical_trials (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE NOT NULL,
    raw_xml_content TEXT NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SILVER LAYER: Normalized Snowflake Dimensions
-- ============================================================================

-- Out-branched Geography Dimension (Snowflake Structure)
CREATE TABLE IF NOT EXISTS dim_countries (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_locations (
    location_id SERIAL PRIMARY KEY,
    facility_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    country_id INT REFERENCES dim_countries(country_id),
    CONSTRAINT uq_facility_location UNIQUE (facility_name, city, country_id)
);

-- Core 1:N Dimensions
CREATE TABLE IF NOT EXISTS dim_conditions (
    condition_id SERIAL PRIMARY KEY,
    condition_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_phases (
    phase_id SERIAL PRIMARY KEY,
    phase_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_study_types (
    study_type_id SERIAL PRIMARY KEY,
    study_type_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_study_designs (
    study_design_id SERIAL PRIMARY KEY,
    design_allocation VARCHAR(100),
    design_intervention_model VARCHAR(100),
    design_masking VARCHAR(100),
    CONSTRAINT uq_study_design UNIQUE (design_allocation, design_intervention_model, design_masking)
);

CREATE TABLE IF NOT EXISTS dim_sponsors (
    sponsor_id SERIAL PRIMARY KEY,
    sponsor_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_interventions (
    intervention_id SERIAL PRIMARY KEY,
    intervention_type VARCHAR(100),
    intervention_name VARCHAR(255) NOT NULL,
    CONSTRAINT uq_intervention UNIQUE (intervention_type, intervention_name)
);

-- ============================================================================
-- SILVER LAYER: Central Fact Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS fact_trials (
    trial_id VARCHAR(50) PRIMARY KEY,
    title TEXT,
    status_id INT REFERENCES dim_statuses(status_id),
    phase_id INT REFERENCES dim_phases(phase_id),
    study_type_id INT REFERENCES dim_study_types(study_type_id),
    study_design_id INT REFERENCES dim_study_designs(study_design_id),
    enrollment INT,
    url TEXT,
    start_date DATE,
    primary_completion_date DATE,
    completion_date DATE,
    first_posted DATE,
    results_first_posted DATE,
    last_update_posted DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SILVER LAYER: Many-to-Many Bridge Tables
-- ============================================================================
CREATE TABLE IF NOT EXISTS bridge_trial_sponsors (
    trial_id VARCHAR(50) REFERENCES fact_trials(trial_id) ON DELETE CASCADE,
    sponsor_id INT REFERENCES dim_sponsors(sponsor_id) ON DELETE RESTRICT,
    sponsor_role VARCHAR(50) NOT NULL, -- 'Lead Sponsor' or 'Collaborator'
    PRIMARY KEY (trial_id, sponsor_id)
);

CREATE TABLE IF NOT EXISTS bridge_trial_locations (
    trial_id VARCHAR(50) REFERENCES fact_trials(trial_id) ON DELETE CASCADE,
    location_id INT REFERENCES dim_locations(location_id) ON DELETE RESTRICT,
    PRIMARY KEY (trial_id, location_id)
);

CREATE TABLE IF NOT EXISTS bridge_trial_interventions (
    trial_id VARCHAR(50) REFERENCES fact_trials(trial_id) ON DELETE CASCADE,
    intervention_id INT REFERENCES dim_interventions(intervention_id) ON DELETE RESTRICT,
    PRIMARY KEY (trial_id, intervention_id)
);

CREATE TABLE IF NOT EXISTS bridge_trial_conditions (
    trial_id VARCHAR(50) REFERENCES fact_trials(trial_id) ON DELETE CASCADE,
    condition_id INT REFERENCES dim_conditions(condition_id) ON DELETE RESTRICT,
    PRIMARY KEY (trial_id, condition_id)
);