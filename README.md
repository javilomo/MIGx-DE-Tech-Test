# Clinical Trials ELT Data Pipeline (Medallion Architecture)

This repository contains a production-ready, database-driven ELT (Extract, Load, Transform) data pipeline that orchestrates the ingestion, normalization, and semantic modeling of ClinicalTrials.gov XML data into a PostgreSQL Data Warehouse using a unified **Medallion Architecture (Bronze ➔ Silver ➔ Gold)**.

---

## 🏗️ Architecture Overview

The project decouples raw data ingestion from analytical querying by implementing three distinct data layers within the PostgreSQL database instance:

[ Raw XML Files ] ──> 📂 BRONZE Layer (public.bronze_clinical_trials)
│   (Strict PostgreSQL Native XML Well-Formed Validation)
▼
📂 SILVER Layer (Snowflake Dimensional Model / public.silver_)
│   (Strict SQL Upserts & Idempotency Rules)
▼
📂 GOLD Layer   (Semantic Analytics / gold. Views)
(Reporting, Aggregations & BI Tools Contract)

1. **Bronze Layer (`public.bronze_clinical_trials`)**: Acts as the landing/staging area. It stores raw XML source strings alongside structural metadata (filenames, ingestion timestamps). A critical validation constraint (`xml_is_well_formed`) ensures corrupt payloads are caught instantly.
2. **Silver Layer (`public.silver_*`)**: Implements a clean, standardized **Snowflake Dimensional Schema**. It normalizes the unstructured XML into a central Fact Table (`silver_fact_trials`), 1:N dimensions, and strict M:N bridge tables. All relational entity definitions feature clean column identifiers, keeping infrastructure prefixes isolated strictly to table names.
3. **Gold Layer (`gold.*` Views)**: The semantic analytics tier. Encapsulated entirely within a dedicated database schema namespace (`gold`), it exposes heavily decoupled relational views. It flattens hierarchical structural attributes and computes complex data quality and lifecycle tracking metrics (such as publication reporting lags) ready for instant BI (Power BI/Tableau) consumption.

---

## 🛠️ Tech Stack & Key Features

- **Language**: Python 3.9+
- **Database Engine**: PostgreSQL (utilizing advanced XML Processing & XPath Functions)
- **Database Driver**: `psycopg2`
- **Testing Framework**: `pytest` + `pytest-cov` (Code Coverage)
- **Data Quality & Resilience**:
  - **Atomic Transactions**: Complete pipeline runs execute within atomic contexts (`commit`/`rollback` architecture).
  - **Idempotency**: Strict multi-column SQL `ON CONFLICT DO UPDATE/DO NOTHING` mutations prevent downstream duplication on backfills.
  - **Parser Safeguards**: Python-side type-checking (`isinstance`) prevents character-splitting bugs on scalar arrays during iteration.

---

## 📁 Repository Structure

MIGX-DE-TECH-TEST
├── src/
│   ├── schema.py       # 
│   ├── extract.py      # Core extractor parsing raw feeds into Bronze
│   ├── transform.py    # High-performance XPath ELT transformation engine
│   ├── load.py         # Relational dimension loading and bridging mechanics
│   ├── gold.py         # Automated semantic DDL view provisioning script
│   └── main.py         # Pipeline orchestration master entry point
├── config/
│   └── config.py       # Database pooling context configuration
├── sql/
│   ├── gold_layer.sql   # 
│   └── schema.sql       # 
├── tests/
│   └── test_pipeline.py # Data quality, parsing, and integration tests
├── pytest.ini          # Test runner route configurations
├── requirements.txt    # Managed project dependencies
└── README.md           # Technical project documentation

## 🚀 Getting Started
1. **Prerequisites & Environment Setup
Ensure you have a PostgreSQL instance running and clone this repository. Create a local Python virtual environment:

Clone the repository
git clone [https://github.com/your-username/MIGx-DE-Tech-Test.git](https://github.com/your-username/MIGx-DE-Tech-Test.git)
cd MIGx-DE-Tech-Test

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

