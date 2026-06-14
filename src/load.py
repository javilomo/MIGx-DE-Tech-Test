import logging
from datetime import datetime
from src.transform import get_elt_transformation_query

def parse_clinical_date(raw_date_str: str) -> str:
    """
    Cleans clinical trial dates into a relational standard ISO format (YYYY-MM-DD).
    Handles mixed granularities such as 'January 15, 2024' or 'December 2025'.
    """
    if not raw_date_str:
        return None
    clean_val = raw_date_str.split('type=')[0].strip()
    for fmt in ["%B %d, %Y", "%B %Y"]:
        try:
            return datetime.strptime(clean_val, fmt).date().isoformat()
        except ValueError:
            continue
    return None

def load_silver_elt(conn) -> None:
    """
    Populates the Silver Snowflake dimensional models and maps cross-relational 
    bridge tables using strict SQL Upserts to ensure system idempotency.
    Supports M:N mapping for conditions, sponsors, interventions, and locations.
    """
    cursor = conn.cursor()
    try:
        transform_query = get_elt_transformation_query()
        cursor.execute(transform_query)
        transformed_rows = cursor.fetchall()
        
        colnames = [desc[0] for desc in cursor.description]
        logging.info(f"📥 Loading {len(transformed_rows)} records into Silver Snowflake Architecture...")

        for tuple_row in transformed_rows:
            row = dict(zip(colnames, tuple_row))
            trial_id = row['trial_id']
            
            if not trial_id:
                continue

            # -----------------------------------------------------------------
            # STEP 1: POPULATE 1:N DIMENSIONS
            # -----------------------------------------------------------------
            cursor.execute("""
                INSERT INTO dim_statuses (status_name) VALUES (%s)
                ON CONFLICT (status_name) DO UPDATE SET status_name = EXCLUDED.status_name RETURNING status_id;
            """, (row['status_name'],))
            status_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO dim_phases (phase_name) VALUES (%s)
                ON CONFLICT (phase_name) DO UPDATE SET phase_name = EXCLUDED.phase_name RETURNING phase_id;
            """, (row['phase_name'],))
            phase_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO dim_study_types (study_type_name) VALUES (%s)
                ON CONFLICT (study_type_name) DO UPDATE SET study_type_name = EXCLUDED.study_type_name RETURNING study_type_id;
            """, (row['study_type_name'],))
            study_type_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO dim_study_designs (design_allocation, design_intervention_model, design_masking)
                VALUES (%s, %s, %s)
                ON CONFLICT (design_allocation, design_intervention_model, design_masking) 
                DO UPDATE SET design_allocation = EXCLUDED.design_allocation RETURNING study_design_id;
            """, (row['design_allocation'], row['design_intervention_model'], row['design_masking']))
            study_design_id = cursor.fetchone()[0]

            # -----------------------------------------------------------------
            # STEP 2: LOAD CENTRAL FACT TABLE (fact_trials)
            # -----------------------------------------------------------------
            start_date = parse_clinical_date(row['raw_start_date'])
            
            cursor.execute("""
                INSERT INTO fact_trials (trial_id, status_id, phase_id, study_type_id, study_design_id, enrollment, start_date, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (trial_id) DO UPDATE SET
                    status_id = EXCLUDED.status_id,
                    phase_id = EXCLUDED.phase_id,
                    study_type_id = EXCLUDED.study_type_id,
                    study_design_id = EXCLUDED.study_design_id,
                    enrollment = EXCLUDED.enrollment,
                    start_date = EXCLUDED.start_date,
                    updated_at = CURRENT_TIMESTAMP;
            """, (trial_id, status_id, phase_id, study_type_id, study_design_id, row['enrollment'], start_date))

            # -----------------------------------------------------------------
            # STEP 3: RECONCILE M:N BRIDGE RELATIONSHIPS
            # -----------------------------------------------------------------

            # 3A. Conditions M:N
            if row['conditions_array']:
                for cond_name_raw in row['conditions_array']:
                    cond_name = str(cond_name_raw).strip()
                    if cond_name:
                        cursor.execute("""
                            INSERT INTO dim_conditions (condition_name) VALUES (%s)
                            ON CONFLICT (condition_name) DO UPDATE SET condition_name = EXCLUDED.condition_name RETURNING condition_id;
                        """, (cond_name,))
                        condition_id = cursor.fetchone()[0]
                        
                        cursor.execute("""
                            INSERT INTO bridge_trial_conditions (trial_id, condition_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;
                        """, (trial_id, condition_id))

            # 3B. Sponsors M:N (Safe Split Breakdown via Custom Pipeline Delimiter)
            sponsors = []
            
            if row.get('lead_sponsors_str'):
                for lead in row['lead_sponsors_str'].split('||'):
                    if lead and lead.strip():
                        sponsors.append((lead.strip(), "Lead Sponsor"))
                        
            if row.get('collaborators_str'):
                for col in row['collaborators_str'].split('||'):
                    if col and col.strip():
                        sponsors.append((col.strip(), "Collaborator"))

            for name, role in sponsors:
                cursor.execute("""
                    INSERT INTO dim_sponsors (sponsor_name) VALUES (%s)
                    ON CONFLICT (sponsor_name) DO UPDATE SET sponsor_name = EXCLUDED.sponsor_name RETURNING sponsor_id;
                """, (name,))
                sponsor_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO bridge_trial_sponsors (trial_id, sponsor_id, sponsor_role) VALUES (%s, %s, %s)
                    ON CONFLICT (trial_id, sponsor_id) DO UPDATE SET sponsor_role = EXCLUDED.sponsor_role;
                """, (trial_id, sponsor_id, role))

            # 3C. Interventions M:N
            if row['intervention_names'] and row['intervention_types']:
                for i_type, i_name in zip(row['intervention_types'], row['intervention_names']):
                    if i_name:
                        i_name = str(i_name).strip()
                        i_type = str(i_type).strip() if i_type else 'Other'
                        
                        cursor.execute("""
                            INSERT INTO dim_interventions (intervention_type, intervention_name) 
                            VALUES (%s, %s)
                            ON CONFLICT (intervention_type, intervention_name) 
                            DO UPDATE SET intervention_name = EXCLUDED.intervention_name 
                            RETURNING intervention_id;
                        """, (i_type, i_name))
                        intervention_id = cursor.fetchone()[0]
                        
                        cursor.execute("""
                            INSERT INTO bridge_trial_interventions (trial_id, intervention_id) 
                            VALUES (%s, %s) 
                            ON CONFLICT DO NOTHING;
                        """, (trial_id, intervention_id))

            # 3D. Locations M:N (Safe Text Array Parallel Iteration)
            if row['location_countries'] and row['location_facility_names']:
                cities = row['location_cities'] if row['location_cities'] else []
                states = row['location_states'] if row['location_states'] else []
                
                for idx, (country, facility) in enumerate(zip(row['location_countries'], row['location_facility_names'])):
                    if not country or not facility:
                        continue
                    
                    c_name = str(country).strip()
                    f_name = str(facility).strip()
                    
                    city_name = str(cities[idx]).strip() if idx < len(cities) else 'Unknown City'
                    state_name = str(states[idx]).strip() if idx < len(states) else None

                    # 1. Insert into dim_countries
                    cursor.execute("""
                        INSERT INTO dim_countries (country_name) VALUES (%s)
                        ON CONFLICT (country_name) DO UPDATE SET country_name = EXCLUDED.country_name 
                        RETURNING country_id;
                    """, (c_name,))
                    country_id = cursor.fetchone()[0]

                    # 2. Insert into dim_locations
                    cursor.execute("""
                        INSERT INTO dim_locations (facility_name, city, state, country_id) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (facility_name, city, country_id) 
                        DO UPDATE SET state = EXCLUDED.state 
                        RETURNING location_id;
                    """, (f_name, city_name, state_name, country_id))
                    location_id = cursor.fetchone()[0]

                    # 3. Connect via bridge_trial_locations
                    cursor.execute("""
                        INSERT INTO bridge_trial_locations (trial_id, location_id) 
                        VALUES (%s, %s) 
                        ON CONFLICT DO NOTHING;
                    """, (trial_id, location_id))

    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Critical runtime exception captured in loading transaction: {e}")
        raise e
    else:
        conn.commit()
        logging.info("🎉 ELT LOAD PHASE COMPLETED SUCCESSFULLY! Silver Warehouse layers fully up to date.")
    finally:
        cursor.close()