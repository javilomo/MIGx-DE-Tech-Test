import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Import pipeline orchestrators
from src.schema import init_database_schema
from src.extract import run_bronze_ingestion 
from src.transform import run_elt_pipeline
from src.gold import build_gold_layer_views

# Industrial logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_db_connection():
    """
    Builds an isolated connection to the PostgreSQL engine using environment variables.
    """
    load_dotenv()
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "clinical_trials_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        logging.critical(f"❌ Target Database cluster unreachable: {e}")
        sys.exit(1)

def main():
    logging.info("🚀 Booting up ClinicalTrials.gov ELT Engine Pipeline...")
    
    # Connect to PostgreSQL cluster
    conn = get_db_connection()
    
    try:
        # =====================================================================
        # INFRASTRUCTURE DEPLOYMENT: Deploy Schemas if non-existent
        # =====================================================================
        init_database_schema(conn)
        
        # =====================================================================
        # PHASE 1: EXTRACT & LOAD (EL) -> Structural Landing into Bronze
        # =====================================================================
        logging.info("=== PHASE 1: Initiating Raw File Landing into Bronze ===")
        run_bronze_ingestion(conn)
        
        # =====================================================================
        # PHASE 2: TRANSFORM (T) -> Pure Relational Spark-Like Parsing inside DB
        # =====================================================================
        logging.info("=== PHASE 2: Running Heavy Database-Native Transformations ===")
        run_elt_pipeline(conn)
        
        logging.info("🎉 Execution complete. Data Lakehouse Architecture Synchronized.")

        # =====================================================================
        # PHASE 3: VIEW (V) -> Gold layer's views
        # =====================================================================

        build_gold_layer_views(conn)
        
    except Exception as pipeline_error:
        logging.critical(f"💥 Pipeline collapsed due to unhandled exception: {pipeline_error}")
        sys.exit(1)
        
    finally:
        if conn:
            conn.close()
            logging.info("🔌 Connection context returned to database connection pool cleanly.")

if __name__ == "__main__":
    main()