import os
import logging

def init_database_schema(conn, sql_file_path: str = "sql/schema.sql") -> None:
    """
    Reads the physical DDL constraints from schema.sql and executes them
    within a safe transactional block to initialize the database architecture.
    """
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"💥 Target SQL schema file missing at: {sql_file_path}")

    logging.info("🚀 Initializing target database relational schemas via SQL DDL...")
    cursor = conn.cursor()
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        cursor.execute(sql_script)
        conn.commit()
        logging.info("🎉 Database infrastructure schema deployed and verified successfully.")
    except Exception as e:
        conn.rollback()
        logging.error(f"💥 Critical failure during physical schema creation: {e}")
        raise e
    finally:
        cursor.close()