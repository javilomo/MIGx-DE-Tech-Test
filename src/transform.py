import logging

def get_elt_transformation_query() -> str:
    """
    Returns the complete, high-performance SQL query for database-driven transformation.
    Guarantees that arrays are strictly cast to text[] to prevent Python 
    string-splitting bugs during iteration.
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
            
            -- Identity & Degenerate Descriptive Fields
            (xpath('//id_info/nct_id/text()', xml_data))[1]::text AS trial_id,
            (xpath('//brief_title/text()', xml_data))[1]::text AS title,
            (xpath('//required_header/url/text()', xml_data))[1]::text AS url,
            
            COALESCE((xpath('//overall_status/text()', xml_data))[1]::text, 'Unknown') AS status_name,
            COALESCE((xpath('//phase/text()', xml_data))[1]::text, 'N/A') AS phase_name,
            COALESCE((xpath('//study_type/text()', xml_data))[1]::text, 'Unknown Type') AS study_type_name,
            
            -- Study Design
            (xpath('//study_design_info/allocation/text()', xml_data))[1]::text AS design_allocation,
            (xpath('//study_design_info/intervention_model/text()', xml_data))[1]::text AS design_intervention_model,
            (xpath('//study_design_info/masking/text()', xml_data))[1]::text AS design_masking,
            
            -- Metrics & Tracking Dates
            COALESCE((xpath('//enrollment/text()', xml_data))[1]::text, '0')::integer AS enrollment,
            (xpath('//start_date/text()', xml_data))[1]::text AS raw_start_date,
            (xpath('//primary_completion_date/text()', xml_data))[1]::text AS raw_primary_completion_date,
            (xpath('//completion_date/text()', xml_data))[1]::text AS raw_completion_date,
            (xpath('//study_first_posted/text()', xml_data))[1]::text AS raw_first_posted,
            (xpath('//results_first_posted/text()', xml_data))[1]::text AS raw_results_first_posted,
            (xpath('//last_update_posted/text()', xml_data))[1]::text AS raw_last_update_posted,
            
            -- Bridges Arrays (Garantizamos conversión explícita a array de texto)
            xpath('//condition/text()', xml_data)::text[] AS conditions_array,
            
            -- Safe String Conversion for Sponsors
            array_to_string(xpath('//sponsors/lead_sponsor/agency/text()', xml_data)::text[], '||') AS lead_sponsors_str,
            array_to_string(xpath('//sponsors/collaborator/agency/text()', xml_data)::text[], '||') AS collaborators_str,
            
            -- Interventions Arrays (Text)
            xpath('//intervention/intervention_type/text()', xml_data)::text[] AS intervention_types,
            xpath('//intervention/intervention_name/text()', xml_data)::text[] AS intervention_names,
            
            -- Locations Geographies Extraction (Parallel Text Arrays)
            xpath('//location/facility/name/text()', xml_data)::text[] AS location_facility_names,
            xpath('//location/facility/address/city/text()', xml_data)::text[] AS location_cities,
            xpath('//location/facility/address/state/text()', xml_data)::text[] AS location_states,
            xpath('//location/facility/address/country/text()', xml_data)::text[] AS location_countries
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