import logging

def get_elt_transformation_query() -> str:
    """
    Returns the complete, high-performance SQL query for database-driven transformation.
    Converts PostgreSQL arrays to plain strings to guarantee safe parsing in Python.
    """
    return """
    WITH verified_bronze AS (
        SELECT 
            id AS bronze_id,
            file_name,
            CAST(raw_xml_content AS XML) as xml_data 
        FROM bronze_clinical_trials
        WHERE xml_is_well_formed(raw_xml_content) = TRUE
    ),
    extracted_fields AS (
        SELECT
            bronze_id,
            file_name,
            
            -- Identity Fields
            (xpath('/clinical_study/id_info/nct_id/text()', xml_data))[1]::text AS trial_id,
            COALESCE((xpath('/clinical_study/overall_status/text()', xml_data))[1]::text, 'Unknown') AS status_name,
            COALESCE((xpath('/clinical_study/phase/text()', xml_data))[1]::text, 'N/A') AS phase_name,
            COALESCE((xpath('/clinical_study/study_type/text()', xml_data))[1]::text, 'Unknown Type') AS study_type_name,
            
            -- Study Design
            (xpath('/clinical_study/study_design_info/allocation/text()', xml_data))[1]::text AS design_allocation,
            (xpath('/clinical_study/study_design_info/intervention_model/text()', xml_data))[1]::text AS design_intervention_model,
            (xpath('/clinical_study/study_design_info/masking/text()', xml_data))[1]::text AS design_masking,
            
            -- Metrics
            COALESCE((xpath('/clinical_study/enrollment/text()', xml_data))[1]::text, '0')::integer AS enrollment,
            (xpath('/clinical_study/start_date/text()', xml_data))[1]::text AS raw_start_date,
            
            -- Bridges Arrays (M:N)
            xpath('/clinical_study/condition/text()', xml_data) AS conditions_array,
            
            -- Safe String Conversion for Sponsors (Using internal pipeline delimiter '||')
            array_to_string(xpath('/clinical_study/sponsors/lead_sponsor/agency/text()', xml_data)::text[], '||') AS lead_sponsors_str,
            array_to_string(xpath('/clinical_study/sponsors/collaborator/agency/text()', xml_data)::text[], '||') AS collaborators_str,
            
            -- Interventions Arrays (Text)
            xpath('/clinical_study/intervention/intervention_type/text()', xml_data)::text[] AS intervention_types,
            xpath('/clinical_study/intervention/intervention_name/text()', xml_data)::text[] AS intervention_names,
            
            -- Locations Geographies Extraction (Parallel Text Arrays)
            xpath('/clinical_study/location/facility/name/text()', xml_data)::text[] AS location_facility_names,
            xpath('/clinical_study/location/facility/address/city/text()', xml_data)::text[] AS location_cities,
            xpath('/clinical_study/location/facility/address/state/text()', xml_data)::text[] AS location_states,
            xpath('/clinical_study/location/facility/address/country/text()', xml_data)::text[] AS location_countries
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
