import logging

def get_elt_transformation_query() -> str:
    """
    Returns the core SQL query executing the database-driven transformation.
    Tailored specifically to handle official ClinicalTrials.gov XML structures,
    extracting multi-layered elements via strict, fast-indexed XPath routing.
    """
    return """
    WITH verified_bronze AS (
        SELECT 
            id AS bronze_id,
            file_name,
            -- Force clean XML rendering stripping formatting anomalies
            CAST(raw_xml_content AS XML) as xml_data 
        FROM bronze_clinical_trials
        WHERE xml_is_well_formed(raw_xml_content) = TRUE
    ),
    extracted_fields AS (
        SELECT
            bronze_id,
            file_name,
            
            -- Core Multi-layered Identity mapping
            (xpath('/clinical_study/id_info/nct_id/text()', xml_data))[1]::text AS trial_id,
            COALESCE((xpath('/clinical_study/condition/text()', xml_data))[1]::text, 'Unknown Condition') AS condition_name,
            COALESCE((xpath('/clinical_study/overall_status/text()', xml_data))[1]::text, 'Unknown') AS status_name,
            COALESCE((xpath('/clinical_study/phase/text()', xml_data))[1]::text, 'N/A') AS phase_name,
            COALESCE((xpath('/clinical_study/study_type/text()', xml_data))[1]::text, 'Unknown Type') AS study_type_name,
            
            -- Structural Study Design Attributes
            (xpath('/clinical_study/study_design_info/allocation/text()', xml_data))[1]::text AS design_allocation,
            (xpath('/clinical_study/study_design_info/intervention_model/text()', xml_data))[1]::text AS design_intervention_model,
            (xpath('/clinical_study/study_design_info/masking/text()', xml_data))[1]::text AS design_masking,
            
            -- Metadata Metrics & Numerical properties
            COALESCE((xpath('/clinical_study/enrollment/text()', xml_data))[1]::text, '0')::integer AS enrollment,
            (xpath('/clinical_study/start_date/text()', xml_data))[1]::text AS raw_start_date,
            
            -- Sub-node Arrays mapping directly into M:N bridges
            xpath('/clinical_study/sponsors/lead_sponsor/agency/text()', xml_data) AS lead_sponsor_array,
            xpath('/clinical_study/sponsors/collaborator/agency/text()', xml_data) AS collaborators_array,
            xpath('/clinical_study/location', xml_data) AS location_nodes,
            xpath('/clinical_study/intervention', xml_data) AS intervention_nodes
        FROM verified_bronze
    )
    SELECT * FROM extracted_fields WHERE trial_id IS NOT NULL;
    """

def run_elt_pipeline(conn) -> None:
    """
    Triggers the database-driven ELT Transformation workflow.
    """
    import logging
    logging.info("🧠 Initializing database-driven ELT Transformation in PostgreSQL...")
    from src.load import load_silver_elt
    load_silver_elt(conn)
