import logging
from config.settings import get_db_connection
from src.extract import extract_raw_xmls
from src.load import load_to_bronze

# Setup logging to monitor the ingestion execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_pipeline_bronze():
    logging.info("🎬 Initializing Bronze Layer Integration Test...")
    
    # 1. Test Extraction from local folder
    raw_dir = "data/raw"
    logging.info(f"Step 1: Scanning '{raw_dir}' for XML files...")
    payload = extract_raw_xmls(raw_dir)
    
    if not payload:
        logging.error("❌ Test Failed: No XML files found. Please add 'NCT04785898.xml' to 'data/raw/'.")
        return
        
    logging.info(f"✅ Step 1 Success: Extracted {len(payload)} file(s) into memory.")
    
    # 2. Test Connection and Bulk Load to Docker Postgres
    logging.info("Step 2: Connecting to Docker PostgreSQL instance...")
    try:
        conn = get_db_connection()
        logging.info("🔌 Connection established successfully.")
        
        logging.info("Step 3: Loading raw payloads into 'bronze_clinical_trials'...")
        load_to_bronze(payload, conn)
        logging.info("✅ Step 3 Success: Bulk insert transaction committed.")
        
        conn.close()
        logging.info("🔌 Database connection closed cleanly.")
        logging.info("🎉 BRONZE LAYER TEST PASSED SUCCESSFULLY!")
        
    except Exception as e:
        logging.error(f"❌ Test Failed due to Database Error: {e}")

if __name__ == "__main__":
    test_pipeline_bronze()