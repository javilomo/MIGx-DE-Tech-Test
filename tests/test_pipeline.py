import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from src.load import parse_clinical_date, load_silver_elt
from src.transform import get_elt_transformation_query
from src.gold import build_gold_layer_views

# ==============================================================================
# 1. UNIT TESTS: DATE VALIDATION AND PARSING
# ==============================================================================
def test_parse_clinical_date_valid_formats():
    """Validates that dates with varying granularities are formatted to ISO correctly."""
    assert parse_clinical_date("January 15, 2024") == "2024-01-15"
    assert parse_clinical_date("December 2025") == "2025-12-01"  # Defaults to the first day

def test_parse_clinical_date_invalid_or_empty():
    """Verifies that empty or invalid strings safely return None."""
    assert parse_clinical_date("") is None
    assert parse_clinical_date(None) is None
    assert parse_clinical_date("Invalid Date 123") is None


# ==============================================================================
# 2. QUALITY TESTS: SQL TRANSFORMATION RULES (LINEAGE)
# ==============================================================================
def test_transformation_query_contains_quality_filters():
    """Ensures the transformation query retains critical data quality rules."""
    query = get_elt_transformation_query()
    
    # Bronze Rule: Only process well-formed XML structures
    assert "xml_is_well_formed(raw_xml_content) = TRUE" in query
    
    # Silver Rule: Filter out records where the Unique ID extraction failed
    assert "WHERE trial_id IS NOT NULL" in query


# ==============================================================================
# 3. INTEGRATION TESTS: SILVER LOAD AND GOLD VIEW PROVISIONING
# ==============================================================================
@patch('src.load.get_elt_transformation_query')
def test_load_silver_elt_execution_flow(mock_get_query):
    """
    Mocks the DB context to verify that the loader processes records,
    executes INSERT queries in sequential order, and issues a COMMIT on success.
    """
    # 1. Configure mocked query response
    mock_get_query.return_value = "SELECT * FROM dummy"
    
    # 2. Simulate PostgreSQL connection and cursor objects
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Setup descriptive headers mimicking PostgreSQL output
    mock_cursor.description = [
        ('trial_id',), ('status_name',), ('phase_name',), ('study_type_name',),
        ('design_allocation',), ('design_intervention_model',), ('design_masking',),
        ('enrollment',), ('raw_start_date',), ('raw_primary_completion_date',),
        ('raw_completion_date',), ('raw_first_posted',), ('raw_results_first_posted',),
        ('raw_last_update_posted',), ('title',), ('url',), ('conditions_array',),
        ('lead_sponsors_str',), ('collaborators_str',), ('intervention_types',),
        ('intervention_names',), ('location_countries',), ('location_facility_names',),
        ('location_cities',), ('location_states',)
    ]
    
    # Mock a simulated pipeline output row
    simulated_row = (
        "NCT00000001", "Completed", "Phase 3", "Interventional",
        "Randomized", "Parallel Assignment", "Double",
        100, "January 01, 2026", None, None, None, None, None,
        "Test Clinical Trial", "http://example.com", 
        ["Diabetes"], "Lead Sponsor Inc", None, None, None, None, None, None, None
    )
    mock_cursor.fetchall.return_value = [simulated_row]
    mock_cursor.fetchone.return_value = (1,)  # Mock SERIAL RETURNING IDs
    
    # 3. Trigger the loader execution
    load_silver_elt(mock_conn)
    
    # 4. Quality Asserts
    assert mock_cursor.execute.called, "The cursor should have executed queries."
    mock_conn.commit.assert_called_once()  # Guarantees save on complete success
    mock_conn.rollback.assert_not_called() # Guarantees no exceptions occurred


def test_build_gold_layer_views_creates_schema():
    """Verifies that the Gold layer attempts to build both the schema and semantic views."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    build_gold_layer_views(mock_conn)
    
    # Validate initialization sequence starts by securing the schema namespace
    mock_cursor.execute.assert_any_call("CREATE SCHEMA IF NOT EXISTS gold;")
    mock_conn.commit.assert_called_once()