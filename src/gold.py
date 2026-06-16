import logging

def build_gold_layer_views(conn) -> None:
    """
    Executes DDL commands to provision the Gold Analytical Layer in the PostgreSQL database.
    Creates views inside the dedicated 'gold' schema for reporting and BI consumptions,
    decoupling technical storage from end-user business query logic.
    """
    cursor = conn.cursor()
    try:
        logging.info("🌟 Initializing Gold Analytical Layer Schema and Semantic Views...")
        
        # Array of DDL statements to construct the Gold views safely
        gold_ddl_statements = [
            "CREATE SCHEMA IF NOT EXISTS gold;",
            
            # Statuses Dimension
            """CREATE OR REPLACE VIEW gold.dim_statuses AS 
               SELECT status_id, status_name AS status FROM silver_dim_statuses;""",
            
            # Phases Dimension
            """CREATE OR REPLACE VIEW gold.dim_phases AS 
               SELECT phase_id, phase_name AS phase FROM silver_dim_phases;""",
               
            # Study Types Dimension
            """CREATE OR REPLACE VIEW gold.dim_study_types AS 
               SELECT study_type_id, study_type_name AS study_type FROM silver_dim_study_types;""",
               
            # Study Designs Dimension
            """CREATE OR REPLACE VIEW gold.dim_study_designs AS 
               SELECT study_design_id, design_allocation AS allocation, 
                      design_intervention_model AS intervention_model, design_masking AS masking 
               FROM silver_dim_study_designs;""",
               
            # Conditions Dimension
            """CREATE OR REPLACE VIEW gold.dim_conditions AS 
               SELECT condition_id, condition_name AS condition FROM silver_dim_conditions;""",
               
            # Sponsors Dimension
            """CREATE OR REPLACE VIEW gold.dim_sponsors AS 
               SELECT sponsor_id, sponsor_name AS sponsor FROM silver_dim_sponsors;""",
               
            # Interventions Dimension
            """CREATE OR REPLACE VIEW gold.dim_interventions AS 
               SELECT intervention_id, intervention_type, intervention_name AS intervention 
               FROM silver_dim_interventions;""",
               
            # Unified Geography View (A flattening of countries and details)
            """CREATE OR REPLACE VIEW gold.v_locations_geography AS 
               SELECT l.location_id, l.facility_name AS facility, l.city, l.state, c.country_name AS country 
               FROM silver_dim_locations l 
               LEFT JOIN silver_dim_countries c ON l.country_id = c.country_id;""",
               
            # Bridge M:N Aided Views for easier analytical filtering
            """CREATE OR REPLACE VIEW gold.v_trial_conditions_bridge AS 
               SELECT bc.trial_id, bc.condition_id, c.condition_name AS condition 
               FROM silver_bridge_trial_conditions bc JOIN silver_dim_conditions c ON bc.condition_id = c.condition_id;""",
               
            """CREATE OR REPLACE VIEW gold.v_trial_sponsors_bridge AS 
               SELECT bs.trial_id, bs.sponsor_id, s.sponsor_name AS sponsor, bs.sponsor_role AS role 
               FROM silver_bridge_trial_sponsors bs JOIN silver_dim_sponsors s ON bs.sponsor_id = s.sponsor_id;""",
               
            """CREATE OR REPLACE VIEW gold.v_trial_interventions_bridge AS 
               SELECT bi.trial_id, bi.intervention_id, i.intervention_type, i.intervention_name AS intervention 
               FROM silver_bridge_trial_interventions bi JOIN silver_dim_interventions i ON bi.intervention_id = i.intervention_id;""",
               
            # COMPREHENSIVE BUSINESS FACT VIEW (Includes Lag Metrics calculations)
            """CREATE OR REPLACE VIEW gold.v_fact_trials_comprehensive AS 
               SELECT 
                   f.trial_id AS nct_number, f.title AS study_title, f.url AS clinical_trials_url,
                   s.status_name AS current_status, p.phase_name AS clinical_phase, t.study_type_name AS study_type,
                   d.design_allocation AS allocation_type, d.design_intervention_model AS model_type, d.design_masking AS masking_type,
                   f.enrollment AS target_enrollment, f.start_date, f.primary_completion_date, f.completion_date,
                   f.first_posted, f.results_first_posted, f.last_update_posted,
                   (f.completion_date - f.start_date) AS total_study_duration_days,
                   (f.results_first_posted - f.completion_date) AS reporting_lag_days,
                   (f.last_update_posted - f.first_posted) AS maintenance_lifecycle_days,
                   f.updated_at AS warehouse_load_timestamp
               FROM silver_fact_trials f
               LEFT JOIN silver_dim_statuses s ON f.status_id = s.status_id
               LEFT JOIN silver_dim_phases p ON f.phase_id = p.phase_id
               LEFT JOIN silver_dim_study_types t ON f.study_type_id = t.study_type_id
               LEFT JOIN silver_dim_study_designs d ON f.study_design_id = d.study_design_id;"""
        ]

        # Orderly execution of view creation
        for statement in gold_ddl_statements:
            cursor.execute(statement)
            
    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Failed to construct Gold Analytical Views: {e}")
        raise e
    else:
        conn.commit()
        logging.info("✨ GOLD ANALYTICAL SEMANTIC LAYER DEPLOYED SUCCESSFULLY!")
    finally:
        cursor.close()