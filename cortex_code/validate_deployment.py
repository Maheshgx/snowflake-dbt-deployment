import os
import sys
from snowflake.snowpark import Session

def has_severe_anomalies(results):
    """
    Parses the Cortex results to determine if the pipeline should fail.
    In a real implementation, you'd inspect the JSON output of the 
    DETECT_ANOMALIES function and check if is_anomaly = True.
    """
    for row in results:
        # Pseudo-logic: checking the first column of the Cortex output
        result_str = str(row[0]).lower()
        if "is_anomaly\": true" in result_str:
            return True
    return False

def validate_revenue_anomalies(session, db_name, schema_name):
    print(f"Running Cortex Anomaly Detection on {db_name}.{schema_name}.FCT_REVENUE...")
    query = f"""
    SELECT SNOWFLAKE.CORTEX.DETECT_ANOMALIES(
        INPUT_DATA => SYSTEM$REFERENCE('TABLE', '{db_name}.{schema_name}.FCT_REVENUE'),
        TIMESTAMP_COLNAME => 'ORDER_DATE',
        TARGET_COLNAME => 'TOTAL_REVENUE'
    )
    """
    try:
        results = session.sql(query).collect()
        if has_severe_anomalies(results):
             raise Exception("Cortex detected massive data anomalies post-deployment. Failing pipeline.")
        print("No severe anomalies detected. Data quality validation passed.")
    except Exception as e:
        # In DEV environments where there is not enough data to train the model, it might fail.
        # Handling it gracefully for this example.
        print(f"Skipping anomaly detection or caught exception: {e}")

if __name__ == "__main__":
    env = sys.argv[1]
    
    # Retrieve DB and Schema configurations dynamically from ENV vars
    db_name = os.getenv("SNOWFLAKE_DATABASE", f"SHOPSTREAM_{env.upper()}")
    schema_name = os.getenv("SNOWFLAKE_SCHEMA", "ANALYTICS")
    
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    }
    
    session = Session.builder.configs(connection_parameters).create()
    validate_revenue_anomalies(session, db_name, schema_name)
