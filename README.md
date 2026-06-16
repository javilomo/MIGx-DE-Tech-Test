# Clinical Trials ELT Data Pipeline (Medallion Architecture)

This repository contains a database-driven ELT (Extract, Load, Transform) data pipeline that orchestrates the ingestion, normalization, and modeling of ClinicalTrials.gov XML data into a PostgreSQL Data Warehouse using a **Medallion Architecture (Bronze ➔ Silver ➔ Gold)**.

---

## 🏗️ Architecture Overview

The project decouples raw data ingestion from analytical querying by implementing three distinct data layers within the PostgreSQL database instance:

1. **Bronze Layer (`public.bronze_clinical_trials`)**: Acts as the landing/staging area. It stores raw XML source strings alongside structural metadata (filenames, ingestion timestamps). A critical validation constraint (`xml_is_well_formed`) ensures corrupt payloads are caught instantly.
2. **Silver Layer (`public.silver_*`)**: Implements a clean, standardized **Star Dimensional Schema**. It normalizes the unstructured XML into a central Fact Table (`silver_fact_trials`), 1:N dimensions, and strict M:N bridge tables. All relational entity definitions feature clean column identifiers, keeping infrastructure prefixes isolated strictly to table names.
3. **Gold Layer (`gold.*` Views)**: The semantic analytics tier. Encapsulated entirely within a dedicated database schema namespace (`gold`), it exposes heavily decoupled relational views. It flattens hierarchical structural attributes and computes complex data quality and lifecycle tracking metrics (such as publication reporting lags) ready for instant BI (Power BI/Tableau) consumption.

I decided to use this approach as it is the the industry standard and, by separating the data into these three distinct steps, the pipeline becomes highly maintainable, easy to debug, and production-ready.

---

## 🛠️ Tech Stack & Key Features

I built this project using a lightweight but powerful setup to keep things simple, professional, and easy to run on any machine.

### 🧰 The Tech Stack
* **Python:** I used it to open the raw XML files, extract the data we need, clean up any messy text, and send everything to the database.
* **PostgreSQL:** Clinical trials have a lot of moving parts that connect to each other (like trials matching with multiple locations and medical conditions). Postgres is perfect for handling these relational links and storing our clean tables.
* **Docker & Docker Compose:** Instead of forcing you to install Python, Postgres, or specific packages on your computer, Docker bundles everything into containers. 
* **Pytest:** I used this to write quick, automated tests. It makes sure that my code parses dates and reads XMLs correctly before anything touches the database.

### ✨ Key Features
* **Safe Credentials (.env):** No passwords or database names are hardcoded in the scripts. Everything is hidden away in a `.env` file.
* **Smart Startup (Health Checks):** Databases take a few seconds to boot up. I added a health check in Docker so the Python script patiently waits until Postgres is 100% ready, preventing early connection crashes.
* **Easy Reporting (Gold Views):** Instead of making users or BI tools write massive SQL queries with 5 different `JOIN`s, the Gold layer gives them a clean, ready-to-use View with everything already put together.

---

## ⚖️ Trade-offs, Limitations & Future Improvements

Here is a quick look at what I chose to prioritize, what the limits are, and how we could level them up in the future:

### 1. File Processing Approach
* **My Choice:** I used standard Python loops and native libraries to parse the XML files instead of heavy big-data frameworks.
* **The Trade-off:** This makes the code lightweight, easy to read, and very fast for hundreds of files. However, if we suddenly scale to millions of complex XMLs, this single-threaded approach will slow down and could run out of RAM.
* **Improvements Needed:** I would replace the standard Python loops with a distributed processing engine like **Apache Spark** (using Azure Databricks). This would allow the pipeline to split the XMLs across multiple servers and process them in parallel.

### 2. Database Selection
* **My Choice:** I chose **PostgreSQL** because it is amazing for relational data (linking trials to locations and conditions) and runs easily inside a local Docker container.
* **The Trade-off:** It is perfect for this project size and for a quick local evaluation. But for a massive corporate setup with terabytes of data, standard Postgres queries would start to lag during heavy reporting.
* **Improvements Needed:** I would migrate the backend storage to a cloud-native, columnar Data Warehouse like **Snowflake** or **Azure Synapse**. This keeps the exact same SQL logic but allows the system to query billions of rows in seconds.

### 3. Data Storage Location
* **My Choice:** The pipeline reads XML files directly from a local folder mapped into Docker.
* **The Trade-off:** This is great for a quick local test. However, it means the raw data is locked to the local machine and cannot be easily shared or automated by external systems.
* **Improvements Needed:** I would decouple the storage by moving the raw XML files to a cloud object store like **Azure Blob Storage**. The pipeline would then trigger automatically whenever a new file drops into the cloud bucket, making the ingestion truly dynamic.

---

## ⏱️ Time Allocation Breakdown

* **Setup & Architecture:** 3 Hours
* **Implementation:** 8 Hours
* **Testing & Documentation:** 3 Hours

---

## 📁 Repository Structure

```text
MIGX-DE-TECH-TEST/
├── src/
│   ├── main.py          # The main switch; triggers the whole pipeline in order
│   ├── extract.py       # Reads the raw XML files and loads them into Bronze
│   ├── transform.py     # Cleans the text and extracts the nested fields
│   ├── load.py          # Inserts the structured data into Silver (Facts & Dimensions)
│   ├── gold.py          # Creates the final easy-to-query SQL Views
│   └── schema.py        # Connects to the database to run the setup queries
├── config/
│   └── config.py        # Handles database connections and .env settings
├── sql/
│   ├── schema.sql       # SQL code to build the Bronze and Silver tables
│   └── gold_layer.sql   # SQL code to build the final Gold analytical views
├── tests/
│   └── test_pipeline.py # Automated tests for XML parsing and database logic
├── pytest.ini           # Configuration file for running Pytest
├── requirements.txt     # List of Python packages required for the project
└── README.md            # This documentation guide
```

## 🚀 Getting Started & Execution Guide

Follow these steps to spin up the localized PostgreSQL data warehouse, configure environment secrets, and trigger the automated ELT pipeline seamlessly within an isolated Docker ecosystem.

### 1. Prerequisites
Ensure you have the following dependencies installed on your host system:
- **Docker** & **Docker Compose**
- A terminal client or database GUI (e.g., DBeaver, TablePlus, or pgAdmin) if you wish to query visually.

### 2. Prepare Environment Variables
To decouple your production-ready engine configuration from infrastructure blueprints, the project uses localized environments. Duplicate the provided ecosystem template:

cp .env.example .env

(Open the newly created .env file in your root folder and modify variables like DB_PASSWORD if necessary, or keep the secure defaults provided).

### 3. Build & Run the Data Pipeline
Execute a single orchestrated container setup command to initialize the database cluster, run health validations, map input XML files, and trigger the engine execution:

docker-compose up --build

### 4. Execute Automated Test Suites
To validate atomic pipeline data constraints, model parsing capabilities, and error isolation thresholds within the active Docker layer environment, run:

docker-compose run data_pipeline python -m pytest -v

### Inspecting the Data Warehouse

Once the pipeline logs confirm a successful execution cycle, you can easily query the data.

**Option A: Via Terminal (No External Tools Required)**
Access the running container's interactive psql instance directly by typing:

docker exec -it clinical_trials_postgres psql -U postgres -d clinical_trials_dw

(type \q to exit the prompt)

**Option B: Via GUI Client / BI Tools (DBeaver, Power BI, etc.)**
Connect your local viewer to the PostgreSQL engine using the parameters described in your .env

---

## 🌟 Bonus Questions & Considerations

### 1. Scalability: Handling 100x Data Volume
If the data volume grows 100x (thousands of large XML files), a single machine running Python and PostgreSQL would run out of memory and slow down. To fix this, I would make three main changes:
* **Distributed Processing:** Move the XML parsing logic from a single Python script to a distributed system like **Apache Spark** (using **Azure Databricks**). This allows multiple servers to process chunks of data at the same time.
* **Cloud Storage:** Instead of keeping XMLs locally, I would store them in a cloud storage bucket (like **Azure Data Lake**) to act as our raw Data Lake.
* **Cloud Data Warehouse:** Switch PostgreSQL for a cloud database built for heavy analytics, such as **Snowflake** or **Azure Synapse**, which can process millions of rows using massive cloud power.

### 2. Data Quality: Additional Validation Rules
* **Date Logic:** Check that the trial's `start_date` happens *before* the `completion_date`. If a file says a trial ended before it started, it should be sent to a quarantine table for review.
* **Allowed Values:** Force strict lists for categorical fields. For example, the `clinical_phase` column must strictly be 'Phase 1', 'Phase 2', etc. Anything else is rejected.
* **Realistic Numbers:** Ensure fields like `enrollment` are never negative numbers, and flag trials with suspicious participant counts (like a Phase 1 safety trial claiming millions of patients).

### 3. Compliance: GxP Environment Considerations
If this pipeline were running in a regulated GxP environment (like pharma or healthcare), I would need to implement strict controls to ensure data integrity and trackability:
* **Audit Trail (Data Lineage):** I would add timestamps and user/process identifiers (`created_at`, `updated_by`) to every table in Silver and Gold. This guarantees we always know exactly *when* a record was modified and *what* process changed it.
* **Data & Code Versioning:** Every raw XML file processed would be archived and tagged alongside the specific Git commit version of the pipeline. If an auditor asks to reproduce a report from six months ago, we can re-run the exact same code with the exact same historical data.
* **Strict Validation (Testing):** Before deploying any changes to production, the pipeline would have to pass a strict testing protocol using predefined sample data to prove the code is 100% deterministic and doesn't alter clinical metrics.

### 4. Monitoring: Production Pipeline Observability
To make sure the pipeline runs smoothly in production without us having to check it manually every day, I would set up a basic monitoring system:
* **Orchestration:** Wrap the scripts inside a tool like **Apache Airflow**. If a step fails (e.g., a network error), it will automatically retry or notify us.
* **Alerting:** Connect the pipeline logs to **Slack** or **Teams**. If the script crashes or throws a critical error, the team gets an instant message.

### 5. Security: Safeguarding Sensitive Clinical Data
Even if ClinicalTrials.gov data is public, real-world clinical pipelines handle internal or sensitive data. I would secure it like this:
* **Data Masking:** Anonymize or hash (using SHA-256) any personal names, emails, or specific doctor addresses right at the beginning of the pipeline before saving them.
* **Permissions (RBAC):** Restrict database access. Data engineers can manage the whole system, but business analysts or BI tools (like Power BI) should only have read-only access to the final **Gold** schema, keeping the raw data safe.