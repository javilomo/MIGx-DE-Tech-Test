import os
import logging
from typing import List

def get_raw_xml_files(data_dir: str) -> List[str]:
    """
    Scans the data directory and extracts paths for all available XML files.
    """
    if not os.path.exists(data_dir):
        logging.error(f"❌ Target data directory does not exist: {data_dir}")
        return []
    
    xml_files = [
        os.path.join(data_dir, f) 
        for f in os.listdir(data_dir) 
        if f.endswith('.xml')
    ]
    logging.info(f"📂 Found {len(xml_files)} raw XML files for ingestion.")
    return xml_files

def run_bronze_ingestion(conn, data_dir: str = "data/raw") -> None:
    """
    Executes the 'Extract & Load' (EL) stage. Stream-dumps raw XML strings 
    directly into the Bronze staging table without modifying data contents.
    """
    xml_files = get_raw_xml_files(data_dir)
    if not xml_files:
        logging.warning("⚠️ No data discovered. Skipping Bronze landing phase.")
        return

    cursor = conn.cursor()
    inserted_count = 0

    try:
        logging.info("📥 Starting bulk insertion into bronze_clinical_trials...")

        for file_path in xml_files:
            file_name = os.path.basename(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_xml_string = f.read()
                
                # Dynamic idempotent staging upsert
                cursor.execute("""
                    INSERT INTO bronze_clinical_trials (file_name, raw_xml_content)
                    VALUES (%s, %s)
                    ON CONFLICT (file_name) 
                    DO UPDATE SET 
                        raw_xml_content = EXCLUDED.raw_xml_content,
                        ingested_at = CURRENT_TIMESTAMP;
                """, (file_name, raw_xml_string))
                
                inserted_count += 1

            except Exception as file_err:
                logging.error(f"❌ Failed to stream file {file_name}: {file_err}")
                continue # Ensure batch processing resiliency

        conn.commit()
        logging.info(f"🎉 Efficiently staged {inserted_count} files inside the Bronze layer.")

    except Exception as e:
        conn.rollback()
        logging.error(f"💥 Bulk insertion transaction failed: {e}")
        raise e
    finally:
        cursor.close()