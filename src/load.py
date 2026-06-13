import logging
from typing import List, Tuple
from psycopg2.extras import execute_values

def load_to_bronze(raw_xml_data: List[Tuple[str, str]], conn) -> None:
    """
    Executes an optimized batch insert of raw XML strings into the Bronze layer table.
    """
    if not raw_xml_data:
        logging.info("Bronze Loader received an empty payload list. Skipping execution.")
        return

    cursor = conn.cursor()
    
    # %s placeholders are automatically mapped by psycopg2 to match table columns
    insert_query = """
        INSERT INTO bronze_clinical_trials (file_name, raw_xml_content)
        VALUES %s;
    """
    
    try:
        # execute_values reduces database roundtrips drastically, improving performance
        execute_values(cursor, insert_query, raw_xml_data)
        conn.commit()
        logging.info(f"Successfully loaded {len(raw_xml_data)} raw records into the Bronze staging layer.")
        
    except Exception as e:
        # Ensure database rollback to prevent corrupted transaction blocks
        conn.rollback()
        raise RuntimeError(f"Bronze layer transaction failed. Database rolled back. Error: {e}")
        
    finally:
        cursor.close()