import logging
import os
from config.settings import get_db_connection
from src.extract import extract_raw_xmls
from src.load import load_to_bronze

# Setup professional logging format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

def run_bronze_pipeline():
    """
    Orchestrates the Bronze Layer ingestion. 
    Extracts raw XML files from the local filesystem and loads them 
    directly into the PostgreSQL staging area.
    """
    logging.info("🚀 Starting Medallion Pipeline: BRONZE LAYER INGESTION")
    
    # Define source directory for raw clinical trials
    raw_data_dir = "data/raw"
    
    # Step 1: EXTRACT - Scan and read local XML files
    logging.info(f"📁 Scanning source directory: '{raw_data_dir}' for clinical trial XMLs...")
    raw_xml_payloads = extract_raw_xmls(raw_data_dir)
    
    if not raw_xml_payloads:
        logging.warning("⚠️ Ingestion halted: No XML files were found or successfully read. Check your data/raw folder.")
        return

    logging.info(f"📥 Extraction successful. Loaded {len(raw_xml_payloads)} files into memory payload.")
    
    # Step 2: LOAD - Establish connection and bulk insert into PostgreSQL Bronze Table
    logging.info("🔌 Connecting to PostgreSQL database...")
    db_connection = None
    try:
        db_connection = get_db_connection()
        
        logging.info("💾 Executing bulk load into 'bronze_clinical_trials' table...")
        load_to_bronze(raw_xml_payloads, db_connection)
        
        logging.info("🏁 BRONZE LAYER pipeline execution finalized successfully!")
        
    except Exception as e:
        logging.critical(f"❌ Critical Pipeline Failure during Bronze Phase: {e}")
    finally:
        if db_connection:
            db_connection.close()
            logging.info("🔌 Database connection closed cleanly.")

if __name__ == "__main__":
    run_bronze_pipeline()